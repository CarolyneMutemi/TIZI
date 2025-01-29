from datetime import datetime, timedelta
import uuid
from typing import Tuple
from fastapi import HTTPException, status
import jwt
from jose import JWTError
from app.core.config import TOKEN_KEY
from app.db.redis_client import redis_client
from app.services.user_services import find_user_by_id


ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

def generate_verification_token(payload: dict) -> str:
    """
    Generate verification token.
    """
    payload["token_type"] = "verification"
    payload["exp"] = int((datetime.now() + timedelta(minutes=15)).timestamp())
    return jwt.encode(payload, TOKEN_KEY, algorithm="HS256")

async def generate_access_token(payload: dict) -> str:
    """
    Generate access token.
    """
    payload["token_type"] = "access"
    payload["exp"] = int((datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    session_id = payload.get("session_id")
    token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
    await redis_client.setex(f"{session_id}_access_token", ACCESS_TOKEN_EXPIRE_MINUTES * 60, token)
    return token

async def generate_refresh_token(payload: dict) -> str:
    """
    Generate refresh token.
    """
    payload["token_type"] = "refresh"
    payload["exp"] = int((datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp())
    session_id = payload.get("session_id")
    token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
    await redis_client.setex(f"{session_id}_refresh_token", REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, token)
    return token

async def get_refresh_token_from_session(session_id: str) -> str:
    """
    Get refresh token from session.
    """
    try:
        token = await redis_client.get(f"{session_id}_refresh_token")
        if not token:
            return None
        return token.decode("utf-8")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error getting refresh token.") from exc

async def get_access_token_from_session(session_id: str) -> str:
    """
    Get access token from session.
    """
    token = await redis_client.get(f"{session_id}_access_token")
    if not token:
        return None
    return token.decode("utf-8")

def decode_token(token: str) -> dict:
    """
    Decode token.
    """
    try:
        return jwt.decode(token, TOKEN_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired."}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token."}
    except JWTError as e:
        return {"error": str(e)}

async def validate_token(token: str, token_type: str) -> dict:
    """
    Validate token.
    """
    try:
        is_blacklisted = await token_is_blacklisted(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized access.") from exc

    if is_blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized access.")

    payload = decode_token(token)
    error = payload.get("error")
    if error:
        print("Error decoding token:", error)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized access.")

    session_id = payload.get("session_id")
    is_right_type = payload.get("token_type") == token_type
    if not is_right_type:
        print("Token type not equal to token_type.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized access.")

    token_functions = {
        "access": get_access_token_from_session,
        "refresh": get_refresh_token_from_session
    }
    stored_token = await token_functions[token_type](session_id)
    if stored_token != token:
        print("Stored token not equal to token.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized access.")

    user_id = payload.get("sub")
    user = await find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="Unauthorized access.")
    return payload

async def store_auth_data(auth_data: dict) -> str:
    """
    Store authentication data in redis.
    """
    state_id = str(uuid.uuid4())
    await redis_client.hset(state_id, mapping=auth_data)
    await redis_client.expire(state_id, 600)

    return state_id

async def get_auth_data(state_id: str) -> dict:
    """
    Get authentication data from redis.
    """
    auth_data = await redis_client.hgetall(state_id)
    modified_auth_data = {}
    for key, value in auth_data.items():
        key = key.decode("utf-8")
        modified_auth_data[key] = value.decode("utf-8")
    await redis_client.delete(state_id)
    return modified_auth_data

async def blacklist_token(token: str, ttl: int) -> None:
    """
    Blacklist token.
    """
    try:
        await redis_client.setex(token, ttl, "blacklisted")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Token blacklisting failed.") from exc

async def token_is_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted.
    """
    blacklisted = await redis_client.get(token)
    is_blacklisted = blacklisted == b"blacklisted"
    return is_blacklisted

async def store_registration_data(user_data: dict) -> str:
    """
    Store user's registration data in redis.
    """
    registration_id = f"e-{str(uuid.uuid4())}"
    await redis_client.hset(registration_id, mapping=user_data)
    await redis_client.expire(registration_id, 3600)

    return registration_id

async def get_registration_data(registration_id: str) -> dict:
    """
    Get user's registration data from redis.
    """
    user_data = await redis_client.hgetall(registration_id)
    modified_user_data = {}
    for key, value in user_data.items():
        key = key.decode("utf-8")
        modified_user_data[key] = value.decode("utf-8")
    await redis_client.delete(registration_id)
    return modified_user_data

async def blacklist_tokens(access_token_str: str) -> str:
    """
    Blacklist both access and refresh tokens.
    """
    payload = await validate_token(access_token_str, token_type="access")

    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    ttl = payload.get("exp") - int(datetime.now().timestamp())

    refresh_token = await get_refresh_token_from_session(session_id)
    payload = decode_token(refresh_token)
    error = payload.get("error")
    if not error:
        ttl = payload.get("exp") - int(datetime.now().timestamp())
        await blacklist_token(refresh_token, ttl)
        await blacklist_token(access_token_str, ttl)
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Error occurred: {error}"
        )

    try:
        await redis_client.delete(f"{session_id}_access_token")
        await redis_client.delete(f"{session_id}_refresh_token")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error deleting tokens.") from exc

    return user_id

async def get_session_expires_at(session_id: str, user_id:str) -> str:
    """
    Get session expires at.
    """
    access_token = await get_refresh_token_from_session(session_id)
    if not access_token:
        print("Access token not found.")
        return None
    payload = decode_token(access_token)
    if not payload.get("error") and payload.get("sub") == user_id:
        timestamp =  payload.get("exp")
        return datetime.fromtimestamp(timestamp).isoformat()
    print("Error getting session expires at or user ID not equal to sub.")
    return None

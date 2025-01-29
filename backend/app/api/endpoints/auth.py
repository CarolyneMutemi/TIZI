from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.utils.auth_utils import generate_access_token, get_auth_data
from app.utils.auth_utils import blacklist_tokens
from app.utils.auth_utils import validate_token
from app.services.user_services import async_delete_user
from app.schemas.auth.auth_responses import AccessTokenResponse, TokenResponse, MessageResponse


auth_router = APIRouter()

http_bearer = HTTPBearer()

@auth_router.post('/token/refresh', response_model=AccessTokenResponse)
async def refresh_access_token(refresh_token: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """
    Refresh token.
    """
    token = refresh_token.credentials
    try:
        payload = await validate_token(token=token, token_type="refresh")
    except Exception as exc:
        raise exc

    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    access_token = await generate_access_token({"sub": user_id, "session_id": session_id})
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=AccessTokenResponse(
                            access_token = access_token,
                            token_type = "Bearer",
                            expires_in = 3600).model_dump())

@auth_router.get('/auth-data', response_model=TokenResponse)
async def get_tokens(state_id: str):
    """
    Get access and refresh tokens.
    """
    auth_data = await get_auth_data(state_id)
    if not auth_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Invalid state ID or state expired.")
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=TokenResponse(
                            registered = True,
                            access_token = auth_data.get("access_token"),
                            refresh_token = auth_data.get("refresh_token"),
                            token_type = "Bearer",
                            access_expires_in = 3600,
                            refresh_expires_in = 2592000).model_dump())

@auth_router.post("/logout", response_model=MessageResponse)
async def logout(access_token: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """
    Logout user.
    """
    access_token_str = access_token.credentials
    await blacklist_tokens(access_token_str)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=MessageResponse(message="Logged out.").model_dump())

@auth_router.delete("/delete-account", response_model=MessageResponse)
async def delete_account(background_tasks: BackgroundTasks, access_token: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """
    Delete user account.
    """
    access_token_str = access_token.credentials
    user_id = await blacklist_tokens(access_token_str)
    background_tasks.add_task(async_delete_user, user_id)
    return JSONResponse(status_code=status.HTTP_200_OK,
                            content=MessageResponse(message="Account deleted.").model_dump())

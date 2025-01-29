from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from app.utils.auth_utils import validate_token
from app.services.user_services import find_user_by_id, update_username


user_router = APIRouter()
http_bearer = HTTPBearer()

async def get_current_user(access_token: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """
    Get current user.
    """
    token_str = access_token.credentials

    payload = await validate_token(token_str, "access")

    user_id = payload.get("sub")
    user = await find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found.")
    return user

@user_router.get('/me')
async def get_me(user: dict = Depends(get_current_user)):
    """
    Get current user.
    """
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authenticated.")

    user["user_id"] = user.pop("_id")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=user)

@user_router.put('/me/username')
async def update_user_name(username: str, user: dict = Depends(get_current_user)):
    """
    Updates username.
    """
    user_id = user.get("_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found.")
    
    updated_user = await update_username(user_id, username)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=updated_user
    )

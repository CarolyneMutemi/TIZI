"""
Email-only authentication.
"""
import uuid
from fastapi import APIRouter, status, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse

from app.utils.auth_utils import generate_verification_token, generate_access_token, generate_refresh_token
from app.utils.auth_utils import store_auth_data, decode_token, store_registration_data, get_registration_data
from app.utils.email_auth_utils import send_email_verification_link
from app.services.user_services import create_user, find_user_by_email
from app.schemas.auth.auth_responses import MessageResponse, TokenResponse
from app.schemas.auth.auth_requests import EmailRegistrationData, LoginRequestBody
from app.core.config import HOME_URL, EMAIL_REGISTER_URL, DASHBOARD_URL


email_auth_router = APIRouter()

@email_auth_router.post('/login', response_model=MessageResponse)
async def login(body: LoginRequestBody, background_tasks: BackgroundTasks):
    """
    Login with email.
    """
    email = body.email

    user = await find_user_by_email(email)
    if user:
        token = generate_verification_token({"sub": email, "registered": True})
    else:
        token = generate_verification_token({"sub": email, "registered": False})

    # email_is_send = send_email_verification_link(email, token)
    background_tasks.add_task(send_email_verification_link, email, token)

    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=MessageResponse(message="Email sent successfully.").model_dump())

@email_auth_router.get('/auth/verify')
async def verify(token: str):
    """
    Verify token.
    """
    payload = decode_token(token)
    error = payload.get("error")
    is_verification = payload.get("token_type") == "verification"
    if error or not is_verification:
        return RedirectResponse(url=HOME_URL)

    registered = payload.get("registered")
    email = payload.get("sub")
    user = await find_user_by_email(email)
    if registered and user:
        user_id = str(user.get("_id"))
        session_id = str(uuid.uuid4())
        access_token = await generate_access_token({"sub": user_id, "session_id": session_id})
        refresh_token = await generate_refresh_token({"sub": user_id, "session_id": session_id})
        # state_id = await store_auth_data({"access_token": access_token, "refresh_token": refresh_token})
        response = RedirectResponse(url=f"{DASHBOARD_URL}?access_token={access_token}&refresh_token={refresh_token}")
        return response
    registration_id = await store_registration_data(user_data={"email": email})
    response = RedirectResponse(url=f"{EMAIL_REGISTER_URL}?registration_id={registration_id}")
    return response

@email_auth_router.post('/register', response_model=TokenResponse)
async def register_with_email(registration_data: EmailRegistrationData):
    """
    Register user.
    """
    registration_id = registration_data.registration_id
    if registration_id[0:2] != "e-":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Invalid registration ID.")
    stored_data = await get_registration_data(registration_id)

    if not stored_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="Unauthorized access.")

    email = stored_data.get("email")
    user_exists = await find_user_by_email(email)

    if user_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                             detail="User already exists.")

    user_obj = registration_data.model_dump()
    user_obj.update(stored_data)
    del user_obj["registration_id"]
    inserted_user_id = await create_user(user_obj)
    if not inserted_user_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail="Error adding user to database.")

    session_id = str(uuid.uuid4())
    access_token = await generate_access_token({"sub": inserted_user_id, "session_id": session_id})
    refresh_token = await generate_refresh_token({"sub": inserted_user_id, "session_id": session_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content=TokenResponse(
                            registered = True,
                            access_token = access_token,
                            refresh_token = refresh_token,
                            token_type = "Bearer",
                            access_expires_in = 3600,
                            refresh_expires_in = 2592000).model_dump())

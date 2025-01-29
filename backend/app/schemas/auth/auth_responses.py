from pydantic import BaseModel

class MessageResponse(BaseModel):
    message: str

class TokenResponse(BaseModel):
    registered: bool
    access_token: str
    refresh_token: str
    token_type: str
    access_expires_in: int
    refresh_expires_in: int

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

from pydantic import BaseModel, EmailStr


class EmailRegistrationData(BaseModel):
    username: str
    registration_id: str

class LoginRequestBody(BaseModel):
    email: EmailStr

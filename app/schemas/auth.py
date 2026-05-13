from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # saniye
    user: "MeResponse"


class MeResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime


# Forward ref resolve
TokenResponse.model_rebuild()

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class VerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send verification code to")


class VerificationVerify(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    verification_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class VerificationResponse(BaseModel):
    message: str
    email: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to resend verification code to")

"""
Authentication request and response schemas.
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """
    Login credentials supplied by the client.
    """

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """
    Refresh token supplied by the client to obtain a new access token.
    """

    refresh_token: str


class TokenResponse(BaseModel):
    """
    JWT token response.
    """

    access_token: str
    refresh_token: str
    token_type: str

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.auth.passwords import verify_password
from app.auth.tokens import TokenError, create_access_token
from app.database.connection import get_connection


logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@auth_router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    email = payload.email.strip().lower()

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, password_hash, is_active
                FROM app_users
                WHERE email = %s;
                """,
                (email,),
            )
            user = cursor.fetchone()
    finally:
        connection.close()

    # Return the same public error for missing users and incorrect passwords.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id, password_hash, is_active = user

    if not is_active or not verify_password(payload.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = create_access_token(user_id)
    except TokenError:
        logger.exception("Local authentication configuration error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Local authentication is unavailable.",
        ) from None

    # Token lifetime is configured in minutes, between 1 and 60.
    import os

    lifetime = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "15"))

    return LoginResponse(
        access_token=token,
        expires_in=lifetime * 60,
    )

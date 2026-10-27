import os
import time
import uuid

import jwt


ALGORITHM = "HS256"


class TokenError(Exception):
    """Raised when token configuration or validation fails."""


def _configuration():
    if os.getenv("APP_ENV") != "development":
        raise TokenError("Local authentication is development-only.")

    if os.getenv("LOCAL_AUTH_ENABLED", "").lower() != "true":
        raise TokenError("Local authentication is disabled.")

    secret = os.getenv("JWT_SECRET", "")
    if len(secret.encode("utf-8")) < 32:
        raise TokenError("JWT_SECRET must be at least 32 bytes.")

    if len(set(secret)) == 1:
        raise TokenError("JWT_SECRET must not be a repeated-character placeholder.")

    issuer = os.getenv("JWT_ISSUER", "rag-local")
    audience = os.getenv("JWT_AUDIENCE", "rag-api")

    try:
        lifetime = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "15"))
    except ValueError as exc:
        raise TokenError("Invalid token lifetime configuration.") from exc

    if not 1 <= lifetime <= 60:
        raise TokenError("Token lifetime must be between 1 and 60 minutes.")

    return secret, issuer, audience, lifetime


def get_access_token_lifetime_seconds() -> int:
    """Return the validated access-token lifetime in seconds."""
    _, _, _, lifetime = _configuration()
    return lifetime * 60


def create_access_token(user_id: str) -> str:
    if not isinstance(user_id, str) or not user_id.strip():
        raise TokenError("Invalid token subject.")

    secret, issuer, audience, lifetime = _configuration()

    now = int(time.time())
    claims = {
        "sub": user_id,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + lifetime * 60,
        "jti": str(uuid.uuid4()),
    }

    return jwt.encode(claims, secret, algorithm=ALGORITHM)


def verify_access_token(token: str) -> str:
    secret, issuer, audience, _ = _configuration()

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            issuer=issuer,
            audience=audience,
            options={
                "require": [
                    "sub", "iss", "aud", "iat", "nbf", "exp", "jti"
                ]
            },
        )
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid or expired access token.") from exc

    user_id = claims.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise TokenError("Invalid token subject.")

    token_id = claims.get("jti")
    if not isinstance(token_id, str) or not token_id.strip():
        raise TokenError("Invalid token ID.")

    return user_id

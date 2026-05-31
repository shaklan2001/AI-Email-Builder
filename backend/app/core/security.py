from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import JWKError
from pydantic import BaseModel

from app.core.config import settings
from app.core.logger import get_logger

bearer_scheme = HTTPBearer()
logger = get_logger(__name__)


class CurrentUser(BaseModel):
    user_id: str


def _normalize_pem(pem: str) -> str:
    return pem.replace("\\n", "\n").strip()


def _decode_clerk_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg", "RS256")

    if algorithm == "HS256":
        if not settings.clerk_secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication is not configured (CLERK_SECRET_KEY required for HS256 tokens)",
            )
        return jwt.decode(token, settings.clerk_secret_key, algorithms=["HS256"])

    if not settings.clerk_pem_public_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )

    pem_key = _normalize_pem(settings.clerk_pem_public_key)
    if "BEGIN PUBLIC KEY" not in pem_key or "END PUBLIC KEY" not in pem_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLERK_PEM_PUBLIC_KEY is malformed; use a single-line value with \\n between PEM lines",
        )

    return jwt.decode(token, pem_key, algorithms=["RS256"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials

    try:
        payload = _decode_clerk_token(token)
    except JWKError as exc:
        logger.error("clerk_pem_invalid", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLERK_PEM_PUBLIC_KEY is invalid or malformed",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return CurrentUser(user_id=user_id)

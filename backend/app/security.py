from datetime import UTC, datetime, timedelta
import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db import get_session
from app.models import User
from app.models import OrganizationMember, Role
from sqlalchemy import select

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def issue_access_token(user_id: uuid.UUID) -> str:
    payload = {"sub": str(user_id), "iss": settings.jwt_issuer, "exp": datetime.now(UTC) + timedelta(minutes=15)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), session: AsyncSession = Depends(get_session)) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"], issuer=settings.jwt_issuer)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from error
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")
    return user


async def require_organization_permission(organization_id: uuid.UUID, user: User, session: AsyncSession, permission: str) -> None:
    role = await session.scalar(select(Role).join(OrganizationMember, OrganizationMember.role_id == Role.id).where(OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id))
    if role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not belong to this organization")
    if not any(grant == permission or grant.endswith(":*") and permission.startswith(grant[:-1]) for grant in role.permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role does not allow this action")

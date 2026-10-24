from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal, get_session, initialize_database
from app.models import AuditLog, Organization, OrganizationMember, Role, User
from app.schemas import LoginRequest, OrganizationCreate, OrganizationResponse, RegisterRequest, TokenResponse
from app.security import current_user, hash_password, issue_access_token, verify_password
from app.accounting import router as accounting_router
from app.clients import router as clients_router
from app.gst import router as gst_router
from app.reconciliation import router as reconciliation_router
from app.integrations import router as integrations_router
from app.documents import router as documents_router
from app.core.config import settings
from app.itr_tax import router as itr_tax_router
import uuid
from fastapi import Query
from pydantic import BaseModel, Field

@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    async with SessionLocal() as session:
        await administrator_role(session)
        await ensure_role_catalog(session)
        await session.commit()
    yield


app = FastAPI(title="TaxSphere India API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(accounting_router)
app.include_router(clients_router)
app.include_router(gst_router)
app.include_router(reconciliation_router)
app.include_router(integrations_router)
app.include_router(documents_router)
app.include_router(itr_tax_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "taxsphere-api"}


async def administrator_role(session: AsyncSession) -> Role:
    permissions = ["organization:*", "members:*", "clients:*", "gst:*", "accounting:*", "documents:*", "workflow:*", "reconciliation:*", "integrations:*", "reports:read", "audit:read"]
    role = await session.scalar(select(Role).where(Role.key == "organization_admin"))
    if role is None:
        role = Role(key="organization_admin", name="Organization Admin", permissions=permissions)
        session.add(role)
        await session.flush()
    else:
        role.permissions = list(dict.fromkeys([*(role.permissions or []), *permissions]))
    return role


ROLE_CATALOG = {
    "tax_preparer": ("Tax Preparer", ["clients:read", "clients:write", "gst:read", "gst:write", "accounting:write", "documents:read", "documents:write", "reconciliation:write", "integrations:read", "workflow:read"]),
    "reviewer": ("Tax Reviewer", ["clients:read", "gst:read", "gst:approve", "accounting:read", "documents:read", "reconciliation:read", "integrations:read", "audit:read"]),
    "read_only": ("Read Only", ["clients:read", "gst:read", "accounting:read", "documents:read", "reconciliation:read", "integrations:read", "reports:read"]),
}


async def ensure_role_catalog(session: AsyncSession) -> None:
    for key, (name, permissions) in ROLE_CATALOG.items():
        role = await session.scalar(select(Role).where(Role.key == key))
        if role is None:
            session.add(Role(key=key, name=name, permissions=permissions))


class MemberAdd(BaseModel):
    email: str = Field(min_length=5, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role_key: str = Field(pattern=r"^(organization_admin|tax_preparer|reviewer|read_only)$")


@app.get("/api/v1/organizations/{organization_id}/members", tags=["organizations"])
async def list_members(organization_id: uuid.UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    from app.security import require_organization_permission
    await require_organization_permission(organization_id, user, session, "members:read")
    rows = (await session.execute(select(User, Role).join(OrganizationMember, OrganizationMember.user_id == User.id).join(Role, Role.id == OrganizationMember.role_id).where(OrganizationMember.organization_id == organization_id).order_by(User.full_name))).all()
    return [{"user_id":str(member.id),"email":member.email,"full_name":member.full_name,"role_key":role.key,"role_name":role.name} for member, role in rows]


@app.post("/api/v1/organizations/{organization_id}/members", status_code=201, tags=["organizations"])
async def add_member(organization_id: uuid.UUID, payload: MemberAdd, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    from app.security import require_organization_permission
    await require_organization_permission(organization_id, user, session, "members:manage")
    member_user = await session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if member_user is None: raise HTTPException(status_code=404, detail="Register this user before adding them to the organization")
    role = await session.scalar(select(Role).where(Role.key == payload.role_key))
    if role is None: raise HTTPException(status_code=422, detail="Role is not configured")
    existing = await session.scalar(select(OrganizationMember).where(OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == member_user.id))
    if existing is not None: raise HTTPException(status_code=409, detail="User is already a member")
    membership = OrganizationMember(organization_id=organization_id,user_id=member_user.id,role_id=role.id)
    session.add(membership)
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action="organization.member.added",entity_type="organization_member",entity_id=membership.id,metadata_={"member_user_id":str(member_user.id),"role_key":role.key}))
    await session.commit()
    return {"user_id":str(member_user.id),"email":member_user.email,"role_key":role.key,"role_name":role.name}


@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    existing = await session.scalar(select(User.id).where(User.email == payload.email.lower()))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(email=payload.email.lower(), full_name=payload.full_name, password_hash=hash_password(payload.password))
    organization = Organization(name=payload.organization_name)
    session.add_all([user, organization])
    await session.flush()
    role = await administrator_role(session)
    await ensure_role_catalog(session)
    session.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role_id=role.id))
    await session.commit()
    return TokenResponse(access_token=issue_access_token(user.id))


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=issue_access_token(user.id))


@app.get("/api/v1/organizations", response_model=list[OrganizationResponse], tags=["organizations"])
async def list_organizations(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[Organization]:
    query = select(Organization).join(OrganizationMember).where(OrganizationMember.user_id == user.id).order_by(Organization.name)
    return list((await session.scalars(query)).all())


@app.get("/api/v1/organizations/{organization_id}/audit-log", tags=["audit"])
async def list_audit_log(organization_id: uuid.UUID, limit: int = Query(default=100, ge=1, le=500), user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    role = await session.scalar(select(Role).join(OrganizationMember, OrganizationMember.role_id == Role.id).where(OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id))
    from app.security import require_organization_permission
    await require_organization_permission(organization_id, user, session, "audit:read")
    events = (await session.scalars(select(AuditLog).where(AuditLog.organization_id == organization_id).order_by(AuditLog.created_at.desc()).limit(limit))).all()
    return [{"id":str(event.id),"user_id":str(event.actor_id) if event.actor_id else None,"action":event.action,"entity_type":event.entity_type,"entity_id":str(event.entity_id) if event.entity_id else None,"details":event.metadata_,"created_at":event.created_at.isoformat()} for event in events]


@app.post("/api/v1/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, tags=["organizations"])
async def create_organization(payload: OrganizationCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> Organization:
    organization = Organization(name=payload.name, legal_name=payload.legal_name, pan=payload.pan)
    session.add(organization)
    await session.flush()
    role = await administrator_role(session)
    await ensure_role_catalog(session)
    session.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role_id=role.id))
    await session.commit()
    await session.refresh(organization)
    return organization

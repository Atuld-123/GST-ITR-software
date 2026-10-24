import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import AuditLog, Client, User
from app.security import current_user, require_organization_permission

router = APIRouter(prefix="/api/v1/organizations/{organization_id}/clients", tags=["clients"])


class ClientCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=200)
    client_type: str = Field(pattern=r"^(individual|proprietorship|partnership|llp|company|trust|other)$")
    pan: str | None = Field(default=None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    email: str | None = Field(default=None, max_length=320)
    mobile: str | None = Field(default=None, max_length=20)


class ClientResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    client_type: str
    pan: str | None
    email: str | None
    mobile: str | None
    status: str


async def require_membership(organization_id: uuid.UUID, user: User, session: AsyncSession, permission: str = "clients:read") -> None:
    await require_organization_permission(organization_id, user, session, permission)


@router.get("", response_model=list[ClientResponse])
async def list_clients(organization_id: uuid.UUID, include_inactive: bool = Query(default=False), user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[Client]:
    await require_membership(organization_id, user, session, "clients:read")
    query = select(Client).where(Client.organization_id == organization_id)
    if not include_inactive:
        query = query.where(Client.status == "active")
    return list((await session.scalars(query.order_by(Client.display_name))).all())


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(organization_id: uuid.UUID, client_id: uuid.UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> Client:
    await require_membership(organization_id, user, session, "clients:read")
    client = await session.scalar(select(Client).where(Client.id == client_id, Client.organization_id == organization_id))
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(organization_id: uuid.UUID, payload: ClientCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> Client:
    await require_membership(organization_id, user, session, "clients:write")
    client = Client(organization_id=organization_id, created_by=user.id, **payload.model_dump())
    session.add(client)
    session.add(AuditLog(organization_id=organization_id, actor_id=user.id, action="client.created", entity_type="client", entity_id=client.id, metadata_={"client_type":client.client_type}))
    try:
        await session.commit()
    except Exception as error:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A client with this PAN already exists in this organization") from error
    await session.refresh(client)
    return client

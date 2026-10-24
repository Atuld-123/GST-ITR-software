import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.clients import require_membership
from app.db import get_session
from app.models import ApiIntegration, User
from app.security import current_user, require_organization_permission

router = APIRouter(prefix="/api/v1/organizations/{organization_id}/integrations", tags=["integrations"])


class IntegrationUpdate(BaseModel):
    service: str = Field(pattern=r"^(gst|income_tax)$")
    provider_name: str = Field(min_length=2, max_length=200)
    environment: str = Field(pattern=r"^(sandbox|production)$")
    credential_reference: str | None = Field(default=None, max_length=200)


class IntegrationResponse(BaseModel):
    service: str
    provider_name: str | None
    environment: str
    status: str
    credential_reference: str | None


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(organization_id: uuid.UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[ApiIntegration]:
    await require_organization_permission(organization_id, user, session, "integrations:read")
    return list((await session.scalars(select(ApiIntegration).where(ApiIntegration.organization_id == organization_id).order_by(ApiIntegration.service))).all())


@router.put("", response_model=IntegrationResponse)
async def configure_integration(organization_id: uuid.UUID, payload: IntegrationUpdate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> ApiIntegration:
    await require_organization_permission(organization_id, user, session, "integrations:manage")
    connection = await session.scalar(select(ApiIntegration).where(ApiIntegration.organization_id == organization_id, ApiIntegration.service == payload.service))
    if connection is None:
        connection = ApiIntegration(organization_id=organization_id, service=payload.service)
        session.add(connection)
    connection.provider_name = payload.provider_name
    connection.environment = payload.environment
    connection.credential_reference = payload.credential_reference
    connection.status = "sandbox_configured" if payload.environment == "sandbox" else "approval_pending"
    await session.commit()
    await session.refresh(connection)
    return connection


@router.post("/{service}/mock-submission")
async def mock_submission(organization_id: uuid.UUID, service: str, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    await require_organization_permission(organization_id, user, session, "integrations:write")
    if service not in {"gst", "income_tax"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown integration service")
    return {"state": "simulated", "message": "Sandbox simulation completed. No government submission was made."}

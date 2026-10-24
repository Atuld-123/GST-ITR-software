import uuid
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import AuditLog, OrganizationMember, Role, User
from app.security import current_user

router = APIRouter(prefix="/api/v1/accounting", tags=["accounting"])


class AccountCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    account_type: str


class JournalLineCreate(BaseModel):
    account_id: uuid.UUID
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def has_exactly_one_side(self) -> "JournalLineCreate":
        if (self.debit > 0) == (self.credit > 0):
            raise ValueError("Each line requires exactly one positive debit or credit amount")
        return self


class JournalEntryCreate(BaseModel):
    organization_id: uuid.UUID
    entry_date: date
    narration: str = Field(min_length=2, max_length=500)
    reference: str | None = Field(default=None, max_length=100)
    lines: list[JournalLineCreate] = Field(min_length=2)

    @model_validator(mode="after")
    def is_balanced(self) -> "JournalEntryCreate":
        debit_total = sum((line.debit for line in self.lines), Decimal("0"))
        credit_total = sum((line.credit for line in self.lines), Decimal("0"))
        if debit_total != credit_total:
            raise ValueError("Journal entry debits must equal credits")
        return self


async def require_membership(organization_id: uuid.UUID, user: User, session: AsyncSession) -> None:
    role = await session.scalar(select(Role).join(OrganizationMember, OrganizationMember.role_id == Role.id).where(OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id))
    if role is None or not any(grant == "accounting:write" or grant == "accounting:*" for grant in role.permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not belong to this organization")


@router.post("/organizations/{organization_id}/accounts", status_code=status.HTTP_201_CREATED)
async def create_account(organization_id: uuid.UUID, payload: AccountCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session)
    from app.models import ChartOfAccount
    account = ChartOfAccount(organization_id=organization_id, **payload.model_dump())
    session.add(account)
    await session.commit()
    return {"id": str(account.id), "code": account.code, "name": account.name}


@router.post("/journal-entries", status_code=status.HTTP_201_CREATED)
async def post_journal_entry(payload: JournalEntryCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(payload.organization_id, user, session)
    from app.models import ChartOfAccount, JournalEntry, JournalEntryLine
    account_ids = {line.account_id for line in payload.lines}
    accounts = list((await session.scalars(select(ChartOfAccount).where(ChartOfAccount.organization_id == payload.organization_id, ChartOfAccount.id.in_(account_ids), ChartOfAccount.is_active.is_(True)))).all())
    if len(accounts) != len(account_ids):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Every line must use an active account in this organization")
    entry = JournalEntry(organization_id=payload.organization_id, entry_date=payload.entry_date, narration=payload.narration, reference=payload.reference, created_by=user.id)
    session.add(entry)
    await session.flush()
    session.add_all([JournalEntryLine(journal_entry_id=entry.id, **line.model_dump()) for line in payload.lines])
    session.add(AuditLog(organization_id=payload.organization_id, actor_id=user.id, action="accounting.journal_entry.posted", entity_type="journal_entry", entity_id=entry.id, metadata_={"reference":entry.reference}))
    await session.commit()
    return {"id": str(entry.id), "status": entry.status, "message": "Balanced journal entry posted"}

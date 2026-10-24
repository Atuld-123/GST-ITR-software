import re
import uuid
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import AuditLog, GstRegistration, Gstr2bEntry, PurchaseInvoice, ReconciliationMatch, ReconciliationRun, User
from app.security import current_user, require_organization_permission

router = APIRouter(prefix="/api/v1/organizations/{organization_id}/reconciliation", tags=["reconciliation"])


class PurchaseInvoiceCreate(BaseModel):
    gst_registration_id: uuid.UUID
    supplier_gstin: str = Field(pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")
    supplier_name: str = Field(min_length=2, max_length=300)
    invoice_number: str = Field(min_length=1, max_length=50)
    invoice_date: date
    taxable_value: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)


class Gstr2bEntryCreate(PurchaseInvoiceCreate):
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class ReconciliationRequest(BaseModel):
    gst_registration_id: uuid.UUID
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


def normalize(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


async def require_membership(organization_id: uuid.UUID, user: User, session: AsyncSession) -> None:
    await require_organization_permission(organization_id, user, session, "reconciliation:write")


async def registration_exists(organization_id: uuid.UUID, registration_id: uuid.UUID, session: AsyncSession) -> None:
    registration = await session.scalar(select(GstRegistration.id).where(GstRegistration.id == registration_id, GstRegistration.organization_id == organization_id, GstRegistration.status == "active"))
    if registration is None: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Use an active GST registration in this organization")


@router.post("/purchase-invoices", status_code=status.HTTP_201_CREATED)
async def add_purchase_invoice(organization_id: uuid.UUID, payload: PurchaseInvoiceCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session); await registration_exists(organization_id, payload.gst_registration_id, session)
    invoice = PurchaseInvoice(organization_id=organization_id, created_by=user.id, **payload.model_dump()); session.add(invoice)
    try: await session.commit()
    except Exception as error: await session.rollback(); raise HTTPException(status_code=409, detail="Duplicate purchase invoice") from error
    return {"id": str(invoice.id), "status": "recorded"}


@router.post("/gstr2b-entries", status_code=status.HTTP_201_CREATED)
async def add_gstr2b_entry(organization_id: uuid.UUID, payload: Gstr2bEntryCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session); await registration_exists(organization_id, payload.gst_registration_id, session)
    entry = Gstr2bEntry(organization_id=organization_id, **payload.model_dump(exclude={"supplier_name"})); session.add(entry)
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action="gst.gstr2b_entry.imported",entity_type="gstr2b_entry",entity_id=entry.id,metadata_={"period":payload.period}))
    try: await session.commit()
    except Exception as error: await session.rollback(); raise HTTPException(status_code=409, detail="Duplicate GSTR-2B entry") from error
    return {"id": str(entry.id), "status": "imported"}


@router.post("/runs")
async def run_reconciliation(organization_id: uuid.UUID, payload: ReconciliationRequest, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session); await registration_exists(organization_id, payload.gst_registration_id, session)
    year, month = map(int, payload.period.split("-")); period_start = date(year, month, 1)
    period_end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    purchases = list((await session.scalars(select(PurchaseInvoice).where(PurchaseInvoice.organization_id == organization_id, PurchaseInvoice.gst_registration_id == payload.gst_registration_id, PurchaseInvoice.invoice_date >= period_start, PurchaseInvoice.invoice_date < period_end))).all())
    entries = list((await session.scalars(select(Gstr2bEntry).where(Gstr2bEntry.organization_id == organization_id, Gstr2bEntry.gst_registration_id == payload.gst_registration_id, Gstr2bEntry.period == payload.period))).all())
    run = ReconciliationRun(organization_id=organization_id, gst_registration_id=payload.gst_registration_id, period=payload.period, created_by=user.id); session.add(run); await session.flush()
    unmatched_entries = set(entry.id for entry in entries); matches = []
    for purchase in purchases:
        candidates = [entry for entry in entries if entry.id in unmatched_entries and entry.supplier_gstin == purchase.supplier_gstin and normalize(entry.invoice_number) == normalize(purchase.invoice_number)]
        if not candidates:
            matches.append(ReconciliationMatch(run_id=run.id, purchase_invoice_id=purchase.id, match_status="missing_in_gstr2b", confidence_score=Decimal("0"), explanation="Purchase invoice has no GSTIN and normalized invoice-number match in GSTR-2B.")); continue
        entry = candidates[0]; unmatched_entries.remove(entry.id)
        values_match = entry.taxable_value == purchase.taxable_value and entry.tax_amount == purchase.tax_amount
        matches.append(ReconciliationMatch(run_id=run.id, purchase_invoice_id=purchase.id, gstr2b_entry_id=entry.id, match_status="exact_match" if values_match else "value_mismatch", confidence_score=Decimal("100" if values_match else "80"), explanation="GSTIN and normalized invoice number match." if values_match else "GSTIN/invoice match, but taxable value or tax amount differs."))
    for entry in entries:
        if entry.id in unmatched_entries: matches.append(ReconciliationMatch(run_id=run.id, gstr2b_entry_id=entry.id, match_status="missing_in_books", confidence_score=Decimal("0"), explanation="GSTR-2B entry has no matching purchase invoice in books."))
    session.add_all(matches)
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action="gst.reconciliation.completed",entity_type="reconciliation_run",entity_id=run.id,metadata_={"period":payload.period,"match_count":len(matches)}))
    await session.commit()
    counts: dict[str, int] = {}
    for match in matches: counts[match.match_status] = counts.get(match.match_status, 0) + 1
    return {"run_id": str(run.id), "period": payload.period, "total_records": len(matches), "summary": counts, "results": [{"status": match.match_status, "confidence": str(match.confidence_score), "explanation": match.explanation} for match in matches]}

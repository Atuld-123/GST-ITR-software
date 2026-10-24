import uuid
import csv
import io
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import AuditLog, FilingReview, GstRegistration, OrganizationMember, Role, SalesInvoice, SalesInvoiceItem, User
from app.security import current_user, require_organization_permission

router = APIRouter(prefix="/api/v1/organizations/{organization_id}/gst", tags=["gst"])
money = lambda amount: amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_gst_breakup(items: list["InvoiceItemCreate"], interstate: bool) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    taxable = money(sum((money(item.taxable_value) for item in items), Decimal("0")))
    tax = money(sum((money(money(item.taxable_value) * item.gst_rate / 100) for item in items), Decimal("0")))
    if interstate:
        return taxable, Decimal("0.00"), Decimal("0.00"), tax, tax
    cgst = money(tax / 2)
    sgst = tax - cgst
    return taxable, cgst, sgst, Decimal("0.00"), tax


class GstRegistrationCreate(BaseModel):
    gstin: str = Field(pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")
    legal_name: str = Field(min_length=2, max_length=300)
    state_code: str = Field(pattern=r"^[0-9]{2}$")

    @model_validator(mode="after")
    def state_matches_gstin(self) -> "GstRegistrationCreate":
        if self.gstin[:2] != self.state_code:
            raise ValueError("GSTIN state prefix must match the selected state code")
        return self


class InvoiceItemCreate(BaseModel):
    description: str = Field(min_length=2, max_length=500)
    hsn_sac: str = Field(min_length=4, max_length=8)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=3)
    taxable_value: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    gst_rate: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)


class SalesInvoiceCreate(BaseModel):
    gst_registration_id: uuid.UUID
    invoice_number: str = Field(min_length=1, max_length=50)
    invoice_date: date
    place_of_supply: str = Field(pattern=r"^[0-9]{2}$")
    recipient_gstin: str | None = Field(default=None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")
    recipient_name: str = Field(min_length=2, max_length=300)
    items: list[InvoiceItemCreate] = Field(min_length=1)


class FilingReviewCreate(BaseModel):
    gst_registration_id: uuid.UUID
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class ReviewDecision(BaseModel):
    decision: str = Field(pattern=r"^(approved|changes_requested)$")
    note: str | None = Field(default=None, max_length=1000)


class AcknowledgementRecord(BaseModel):
    arn: str = Field(min_length=5, max_length=100)


async def require_membership(organization_id: uuid.UUID, user: User, session: AsyncSession, permission: str = "gst:read") -> None:
    await require_organization_permission(organization_id, user, session, permission)


@router.post("/registrations", status_code=status.HTTP_201_CREATED)
async def create_registration(organization_id: uuid.UUID, payload: GstRegistrationCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session, "gst:write")
    registration = GstRegistration(organization_id=organization_id, **payload.model_dump())
    session.add(registration)
    session.add(AuditLog(organization_id=organization_id, actor_id=user.id, action="gst.registration.created", entity_type="gst_registration", entity_id=registration.id, metadata_={"gstin_suffix":registration.gstin[-4:]}))
    try: await session.commit()
    except Exception as error:
        await session.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GSTIN is already registered or the state code does not match") from error
    return {"id": str(registration.id), "gstin": registration.gstin, "status": registration.status}


@router.get("/registrations")
async def list_registrations(organization_id: uuid.UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    await require_membership(organization_id, user, session, "gst:read")
    registrations = list((await session.scalars(select(GstRegistration).where(GstRegistration.organization_id == organization_id, GstRegistration.status == "active").order_by(GstRegistration.gstin))).all())
    return [{"id": str(registration.id), "gstin": registration.gstin, "legal_name": registration.legal_name, "state_code": registration.state_code} for registration in registrations]


@router.post("/sales-invoices", status_code=status.HTTP_201_CREATED)
async def create_sales_invoice(organization_id: uuid.UUID, payload: SalesInvoiceCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session, "gst:write")
    registration = await session.scalar(select(GstRegistration).where(GstRegistration.id == payload.gst_registration_id, GstRegistration.organization_id == organization_id, GstRegistration.status == "active"))
    if registration is None: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Use an active GST registration belonging to this organization")
    interstate = registration.state_code != payload.place_of_supply
    taxable_value, cgst, sgst, igst, tax_total = calculate_gst_breakup(payload.items, interstate)
    invoice = SalesInvoice(organization_id=organization_id, gst_registration_id=registration.id, invoice_number=payload.invoice_number, invoice_date=payload.invoice_date, place_of_supply=payload.place_of_supply, recipient_gstin=payload.recipient_gstin, recipient_name=payload.recipient_name, taxable_value=taxable_value, cgst=cgst, sgst=sgst, igst=igst, cess=Decimal("0"), total_value=taxable_value + tax_total, status="validated", created_by=user.id)
    session.add(invoice); await session.flush()
    session.add_all([SalesInvoiceItem(sales_invoice_id=invoice.id, **item.model_dump()) for item in payload.items])
    session.add(AuditLog(organization_id=organization_id, actor_id=user.id, action="gst.invoice.created", entity_type="sales_invoice", entity_id=invoice.id, metadata_={"invoice_number": invoice.invoice_number}))
    try: await session.commit()
    except Exception as error:
        await session.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice number already exists for this GST registration") from error
    return {"id": str(invoice.id), "status": invoice.status, "taxable_value": str(taxable_value), "cgst": str(cgst), "sgst": str(sgst), "igst": str(igst), "total_value": str(invoice.total_value)}


@router.get("/gstr-1-summary")
async def gstr1_summary(organization_id: uuid.UUID, gst_registration_id: uuid.UUID, period: str, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session, "gst:read")
    try: year, month = map(int, period.split("-")); period_start = date(year, month, 1)
    except ValueError as error: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Period must use YYYY-MM") from error
    if month == 12: period_end = date(year + 1, 1, 1)
    else: period_end = date(year, month + 1, 1)
    statement = select(func.count(SalesInvoice.id), func.coalesce(func.sum(SalesInvoice.taxable_value), 0), func.coalesce(func.sum(SalesInvoice.cgst), 0), func.coalesce(func.sum(SalesInvoice.sgst), 0), func.coalesce(func.sum(SalesInvoice.igst), 0)).where(SalesInvoice.organization_id == organization_id, SalesInvoice.gst_registration_id == gst_registration_id, SalesInvoice.invoice_date >= period_start, SalesInvoice.invoice_date < period_end, SalesInvoice.status == "validated")
    count, taxable, cgst, sgst, igst = (await session.execute(statement)).one()
    return {"form": "GSTR-1", "period": period, "state": "prepared", "invoice_count": count, "taxable_value": str(taxable), "cgst": str(cgst), "sgst": str(sgst), "igst": str(igst), "notice": "Prepared summary only. Submission requires authorized GSTN/GSP integration."}


@router.post("/filing-reviews", status_code=201)
async def create_filing_review(organization_id: uuid.UUID, payload: FilingReviewCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session, "gst:write")
    registration = await session.scalar(select(GstRegistration).where(GstRegistration.id == payload.gst_registration_id, GstRegistration.organization_id == organization_id))
    if registration is None: raise HTTPException(status_code=404, detail="GST registration not found")
    existing = await session.scalar(select(FilingReview).where(FilingReview.organization_id == organization_id, FilingReview.gst_registration_id == registration.id, FilingReview.period == payload.period))
    if existing: return {"id": str(existing.id), "period": existing.period, "status": existing.status}
    review = FilingReview(organization_id=organization_id, gst_registration_id=registration.id, period=payload.period, created_by=user.id)
    session.add(review); await session.flush()
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action="gst.filing_review.created",entity_type="filing_review",entity_id=review.id,metadata_={"period":payload.period}))
    await session.commit()
    return {"id": str(review.id), "period": review.period, "status": review.status, "filing_status": "not_submitted"}


@router.get("/filing-reviews")
async def list_filing_reviews(organization_id: uuid.UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    await require_membership(organization_id, user, session, "gst:read")
    rows = (await session.scalars(select(FilingReview).where(FilingReview.organization_id == organization_id).order_by(FilingReview.created_at.desc()))).all()
    return [{"id":str(r.id),"gst_registration_id":str(r.gst_registration_id),"period":r.period,"status":r.status,"review_note":r.review_note,"acknowledgement_number":r.acknowledgement_number,"acknowledgement_verified":r.acknowledgement_verified} for r in rows]


@router.post("/filing-reviews/{review_id}/decision")
async def decide_filing_review(organization_id: uuid.UUID, review_id: uuid.UUID, payload: ReviewDecision, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session, "gst:approve")
    review = await session.scalar(select(FilingReview).where(FilingReview.id == review_id, FilingReview.organization_id == organization_id))
    if review is None: raise HTTPException(status_code=404, detail="Review not found")
    if review.status not in {"prepared", "changes_requested"}: raise HTTPException(status_code=409, detail="This review is already decided")
    if review.created_by == user.id: raise HTTPException(status_code=403, detail="A different authorized reviewer must approve this filing")
    review.status = payload.decision; review.reviewer_id = user.id; review.review_note = payload.note
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action=f"gst.filing_review.{payload.decision}",entity_type="filing_review",entity_id=review.id,metadata_={"note_present":bool(payload.note)}))
    await session.commit()
    return {"id":str(review.id),"status":review.status,"reviewer_id":str(user.id),"filing_status":"not_submitted"}


@router.post("/filing-reviews/{review_id}/acknowledgement")
async def record_acknowledgement(organization_id: uuid.UUID, review_id: uuid.UUID, payload: AcknowledgementRecord, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await require_membership(organization_id, user, session, "gst:approve")
    review = await session.scalar(select(FilingReview).where(FilingReview.id == review_id, FilingReview.organization_id == organization_id))
    if review is None: raise HTTPException(status_code=404, detail="Review not found")
    if review.status != "approved": raise HTTPException(status_code=409, detail="Approve the return before recording an acknowledgement")
    review.acknowledgement_number = payload.arn
    review.acknowledgement_verified = False
    review.status = "acknowledgement_pending_verification"
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action="gst.acknowledgement.recorded_unverified",entity_type="filing_review",entity_id=review.id,metadata_={"arn_suffix":payload.arn[-4:]}))
    await session.commit()
    return {"id":str(review.id),"status":review.status,"acknowledgement_number":review.acknowledgement_number,"verified":False,"notice":"ARN stored for follow-up; portal verification is not available until authorized GSP/GSTN integration is configured."}


@router.get("/gstr-1-export")
async def export_gstr1(organization_id: uuid.UUID, gst_registration_id: uuid.UUID, period: str, format: str = "json", user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> Response:
    await require_membership(organization_id, user, session, "gst:read")
    if format not in {"json", "csv"}:
        raise HTTPException(status_code=422, detail="format must be json or csv")
    try:
        year, month = map(int, period.split("-")); start = date(year, month, 1)
        if month not in range(1, 13): raise ValueError()
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Period must use YYYY-MM") from error
    registration = await session.scalar(select(GstRegistration).where(GstRegistration.id == gst_registration_id, GstRegistration.organization_id == organization_id))
    if registration is None: raise HTTPException(status_code=404, detail="GST registration not found")
    invoices = list((await session.scalars(select(SalesInvoice).where(SalesInvoice.organization_id == organization_id, SalesInvoice.gst_registration_id == gst_registration_id, SalesInvoice.invoice_date >= start, SalesInvoice.invoice_date < end).order_by(SalesInvoice.invoice_date, SalesInvoice.invoice_number))).all())
    rows = [{"invoice_number": i.invoice_number, "invoice_date": i.invoice_date.isoformat(), "recipient_gstin": i.recipient_gstin, "recipient_name": i.recipient_name, "place_of_supply": i.place_of_supply, "taxable_value": str(i.taxable_value), "cgst": str(i.cgst), "sgst": str(i.sgst), "igst": str(i.igst), "total_value": str(i.total_value), "status": i.status} for i in invoices]
    session.add(AuditLog(organization_id=organization_id, actor_id=user.id, action="gst.gstr1.exported", entity_type="gst_registration", entity_id=registration.id, metadata_={"period": period, "format": format}))
    await session.commit()
    if format == "json": return Response(json.dumps({"form":"GSTR-1","period":period,"state":"prepared","filing_status":"not_submitted","invoices":rows}, ensure_ascii=False), media_type="application/json", headers={"Content-Disposition":f'attachment; filename="gstr1-{period}.json"'})
    buffer = io.StringIO(); writer = csv.DictWriter(buffer, fieldnames=list(rows[0]) if rows else ["invoice_number","invoice_date","recipient_gstin","recipient_name","place_of_supply","taxable_value","cgst","sgst","igst","total_value","status"]); writer.writeheader(); writer.writerows(rows)
    return Response(buffer.getvalue(), media_type="text/csv", headers={"Content-Disposition":f'attachment; filename="gstr1-{period}.csv"'})

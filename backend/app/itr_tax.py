"""Narrow AY 2026-27 salary estimate for CA review; not an ITR return computation."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.models import User
from app.security import current_user

router = APIRouter(prefix="/api/v1/income-tax", tags=["income-tax"])
MONEY = Decimal("1")


class EstimateInput(BaseModel):
    assessment_year: Literal["2026-27"] = "2026-27"
    salary_income: Decimal = Field(ge=0, le=Decimal("50000000"))
    other_ordinary_income: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("50000000"))
    age_category: Literal["below_60", "60_to_79", "80_plus"] = "below_60"
    resident: bool = True
    deductions_80c: Decimal = Field(default=Decimal("0"), ge=0)
    deductions_80ccd_1b: Decimal = Field(default=Decimal("0"), ge=0)


def rupee(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def round_total_income(value: Decimal) -> Decimal:
    return (value / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("10")


def slab_tax(income: Decimal, regime: str, age_category: str) -> Decimal:
    if regime == "new":
        bands = [(400000, 0), (800000, 5), (1200000, 10), (1600000, 15), (2000000, 20), (2400000, 25), (Decimal("Infinity"), 30)]
    else:
        basic = 500000 if age_category == "80_plus" else 300000 if age_category == "60_to_79" else 250000
        bands = [(basic, 0), (500000, 5), (1000000, 20), (Decimal("Infinity"), 30)]
    tax = Decimal("0")
    lower = Decimal("0")
    for upper, rate in bands:
        upper = Decimal(upper)
        portion = max(Decimal("0"), min(income, upper) - lower)
        tax += portion * Decimal(rate) / 100
        if income <= upper:
            break
        lower = upper
    return tax


def regime_result(data: EstimateInput, regime: str) -> dict:
    salary_deduction = Decimal("75000") if regime == "new" else Decimal("50000")
    allowed_deductions = Decimal("0")
    if regime == "old":
        allowed_deductions = min(data.deductions_80c, Decimal("150000")) + min(data.deductions_80ccd_1b, Decimal("50000"))
    gross = data.salary_income + data.other_ordinary_income
    taxable = round_total_income(max(Decimal("0"), gross - salary_deduction - allowed_deductions))
    if taxable > Decimal("5000000"):
        raise ValueError("This review build supports taxable income up to ₹50 lakh only; surcharge and marginal-relief cases need CA-reviewed rules")
    tax_age_category = data.age_category if data.resident else "below_60"
    base_tax = slab_tax(taxable, regime, tax_age_category)
    rebate = Decimal("0")
    if data.resident and regime == "new":
        rebate = min(base_tax, Decimal("60000"))
        if taxable > Decimal("1200000"):
            excess_income = taxable - Decimal("1200000")
            if (base_tax - rebate) * Decimal("1.04") > excess_income:
                rebate = base_tax - excess_income / Decimal("1.04")
    elif data.resident and regime == "old" and taxable <= Decimal("500000"):
        rebate = min(base_tax, Decimal("12500"))
    after_rebate = max(Decimal("0"), base_tax - rebate)
    cess = rupee(after_rebate * Decimal("0.04"))
    return {"regime": regime, "gross_income": str(rupee(gross)), "salary_standard_deduction": str(salary_deduction), "other_allowed_deductions": str(rupee(allowed_deductions)), "taxable_income": str(taxable), "income_tax_before_rebate": str(rupee(base_tax)), "rebate_87a": str(rupee(rebate)), "health_education_cess": str(cess), "surcharge": "0", "estimated_tax": str(rupee(after_rebate + cess))}


@router.post("/estimate")
async def estimate_income_tax(payload: EstimateInput, user: User = Depends(current_user)) -> dict:
    try:
        results = [regime_result(payload, "new"), regime_result(payload, "old")]
    except ValueError as error:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"assessment_year": payload.assessment_year, "applicable_act": "Income-tax Act, 1961 (AY 2026-27)", "status": "estimate_for_ca_review", "filing_status": "not_filed", "regimes": results, "notice": "Salary and ordinary income estimate only. Capital gains, special-rate income, house property, business/profession, relief, surcharge, MAT/AMT and complex deductions are excluded. CA review required."}

from decimal import Decimal

from app.itr_tax import EstimateInput, regime_result


def test_new_regime_87a_rebate_at_12_lakh_taxable_income() -> None:
    result = regime_result(EstimateInput(salary_income=Decimal("1275000")), "new")
    assert result["taxable_income"] == "1200000"
    assert result["rebate_87a"] == "60000"
    assert result["estimated_tax"] == "0"


def test_new_regime_tax_above_12_lakh() -> None:
    result = regime_result(EstimateInput(salary_income=Decimal("1276000")), "new")
    assert result["taxable_income"] == "1201000"
    assert result["estimated_tax"] == "156"


def test_old_regime_resident_senior_citizen_basic_exemption() -> None:
    senior = EstimateInput(salary_income=Decimal("350000"), age_category="60_to_79", resident=True)
    non_senior = EstimateInput(salary_income=Decimal("350000"), age_category="60_to_79", resident=False)
    assert regime_result(senior, "old")["taxable_income"] == "300000"
    assert regime_result(senior, "old")["estimated_tax"] == "0"
    assert regime_result(non_senior, "old")["estimated_tax"] == "2600"


def test_old_regime_80c_is_capped_at_150000() -> None:
    result = regime_result(EstimateInput(salary_income=Decimal("1000000"), deductions_80c=Decimal("250000")), "old")
    assert result["other_allowed_deductions"] == "150000"
    assert result["taxable_income"] == "800000"

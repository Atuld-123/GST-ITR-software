from decimal import Decimal

from app.gst import InvoiceItemCreate, calculate_gst_breakup


def item(value: str, rate: str) -> InvoiceItemCreate:
    return InvoiceItemCreate(description="Test item", hsn_sac="1234", quantity=Decimal("1"), taxable_value=Decimal(value), gst_rate=Decimal(rate))


def test_interstate_tax_uses_igst_and_preserves_total() -> None:
    taxable, cgst, sgst, igst, tax = calculate_gst_breakup([item("100.00", "18")], True)
    assert (taxable, cgst, sgst, igst, tax) == (Decimal("100.00"), Decimal("0.00"), Decimal("0.00"), Decimal("18.00"), Decimal("18.00"))


def test_intrastate_split_reconciles_odd_paise() -> None:
    taxable, cgst, sgst, igst, tax = calculate_gst_breakup([item("0.05", "18")], False)
    assert taxable == Decimal("0.05")
    assert cgst + sgst == tax == Decimal("0.01")
    assert igst == Decimal("0.00")


def test_rounds_each_line_before_summing() -> None:
    _, _, _, igst, tax = calculate_gst_breakup([item("0.05", "18"), item("0.05", "18")], True)
    assert tax == igst == Decimal("0.02")

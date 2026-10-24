# Income tax estimate: CA review packet

**Status: draft implementation; awaiting CA sign-off.** This calculator is a narrow estimate for AY 2026-27 under the Income-tax Act, 1961. AY 2026-27 relates to FY 2025-26; income earned from 1 April 2026 is under the Income-tax Act, 2025 and Tax Year terminology. Do not use this calculator for that next tax year.

## Implemented scope

- Individual salary plus ordinary, non-special-rate other income only.
- Old and new regime comparison; resident status and old-regime age bands.
- Salary standard deduction (₹50,000 old / ₹75,000 new), old-regime 80C (₹1.5 lakh cap) and 80CCD(1B) (₹50,000 cap).
- Section 87A rebate and 4% health and education cess.
- Income limited to ₹50 lakh taxable income; no surcharge cases.
- Income rounded to nearest ₹10 and estimate output explicitly says not filed.

Capital gains, special-rate income, house property, business/profession, carry-forwards, regime election restrictions, HRA, other exemptions/deductions, rebate edge cases outside the implemented boundary, surcharge, foreign income, AMT/MAT and return-form eligibility are excluded. Unsupported cases must be routed to CA review rather than treated as complete.

## Official rule references

- [Income Tax Department: AY 2026-27 salaried tax rates, rebates, cess and age bands](https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1?mobile-app=1)
- [CBDT: ITR-1 validation rules for AY 2026-27](https://www.incometax.gov.in/iec/foportal/sites/default/files/2026-05/CBDT_e-Filing_ITR%201_Validation%20Rules_AY%202026-27.pdf), including standard deduction validation and new-regime limits
- [Income Tax Department: deductions by tax regime](https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable)
- [Income Tax Department: new Act transition](https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/objective-and-scope-new-act)

## CA approval checklist

Review the stated scope, statutory references, slab boundaries, rounding, rebate/cess calculations, and four deterministic fixtures in `backend/tests/test_ay2026_27_income_tax.py`. Record reviewer name, membership details, review date, approved AY/tax year, and any corrections before enabling this as a tax computation feature. Tax rules must be re-reviewed for later years.

"use client";

import { FormEvent, useState } from "react";

type Regime = { regime: string; gross_income: string; salary_standard_deduction: string; other_allowed_deductions: string; taxable_income: string; income_tax_before_rebate: string; rebate_87a: string; health_education_cess: string; estimated_tax: string };
type Estimate = { status: string; notice: string; regimes: Regime[] };

export default function ItrEstimatePage() {
  const [result, setResult] = useState<Estimate | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function calculate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setResult(null); setBusy(true);
    const values = new FormData(event.currentTarget);
    const token = localStorage.getItem("taxsphere_session");
    if (!token) { setError("Please sign in first."); setBusy(false); return; }
    try {
      const response = await fetch("/api/v1/income-tax/estimate", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ assessment_year: "2026-27", salary_income: Number(values.get("salary")), other_ordinary_income: Number(values.get("other")), age_category: values.get("age"), resident: values.get("resident") === "yes", deductions_80c: Number(values.get("80c")), deductions_80ccd_1b: Number(values.get("nps")) }) });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail ?? "Calculation failed"); setResult(data);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Calculation failed"); } finally { setBusy(false); }
  }
  return <main className="module-page"><a className="back" href="/itr">Back to ITR workspace</a><p className="eyebrow">AY 2026–27 · CA REVIEW DRAFT</p><h1>Salary tax estimate</h1><p className="sub">Compare old and new regimes using salary and ordinary income. This estimate does not prepare or file a return.</p><div className="module-grid"><section className="journal"><form className="client-form" onSubmit={calculate}><label>Annual salary (₹)<input name="salary" type="number" min="0" step="1" required /></label><label>Other ordinary income (₹)<input name="other" type="number" min="0" step="1" defaultValue="0" required /></label><label>Age during FY 2025–26<select name="age"><option value="below_60">Below 60</option><option value="60_to_79">60–79</option><option value="80_plus">80 or above</option></select></label><label>Resident in India for tax purposes?<select name="resident"><option value="yes">Yes</option><option value="no">No</option></select></label><label>Eligible 80C claim, old regime only (₹)<input name="80c" type="number" min="0" step="1" defaultValue="0" /></label><label>Eligible 80CCD(1B) NPS claim, old regime only (₹)<input name="nps" type="number" min="0" step="1" defaultValue="0" /></label>{error && <p className="form-error">{error}</p>}<button className="primary" disabled={busy}>{busy ? "Calculating…" : "Compare regimes"}</button></form></section><section className="journal"><h2>Included rules and exclusions</h2><p>AY 2026–27 only. Salary standard deduction, selected old-regime deductions, Section 87A rebate, marginal relief near ₹12 lakh and 4% cess are included.</p><p>Capital gains, business income, house property, special rates, surcharge, foreign income and other deductions are outside this draft. Ask the reviewing CA to confirm the case fits.</p><p>CA rule review packet: docs/TAX_RULE_REVIEW_AY_2026_27.md</p></section></div>{result && <section className="journal"><h2>Estimate · requires CA review</h2><div className="module-grid">{result.regimes.map((r) => <article key={r.regime}><h3>{r.regime === "new" ? "New regime" : "Old regime"}</h3><p>Taxable income: ₹{Number(r.taxable_income).toLocaleString("en-IN")}</p><p>Tax before rebate: ₹{Number(r.income_tax_before_rebate).toLocaleString("en-IN")}</p><p>Section 87A rebate: ₹{Number(r.rebate_87a).toLocaleString("en-IN")}</p><p>Cess: ₹{Number(r.health_education_cess).toLocaleString("en-IN")}</p><strong>Estimated tax: ₹{Number(r.estimated_tax).toLocaleString("en-IN")}</strong></article>)}</div><p className="tiny">{result.notice}</p></section>}</main>;
}

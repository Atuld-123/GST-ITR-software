"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

type ReturnRecord = { id?: string; pan: string; assessmentYear: string; form: string; type: string; status: string; createdAt: string };
const storageKey = "taxsphere_demo_itr_returns";

export default function ItrPage() {
  const router = useRouter();
  const [returns, setReturns] = useState<ReturnRecord[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!localStorage.getItem("taxsphere_session")) { router.replace("/login"); return; }
    const saved: ReturnRecord[] = JSON.parse(localStorage.getItem(storageKey) ?? "[]");
    const migrated = saved.map((record) => record.id ? record : { ...record, id: crypto.randomUUID() });
    localStorage.setItem(storageKey, JSON.stringify(migrated));
    setReturns(migrated);
  }, [router]);

  function createReturn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setMessage("");
    const formElement = event.currentTarget;
    const values = new FormData(formElement);
    const pan = String(values.get("pan")).toUpperCase();
    const assessmentYear = String(values.get("assessmentYear"));
    const returnType = String(values.get("returnType"));
    const form = String(values.get("form"));
    const priorOriginal = returns.find((item) => item.pan === pan && item.assessmentYear === assessmentYear && item.type === "Original");
    if (returnType === "Original" && priorOriginal) {
      setError("An original training return already exists for this PAN and assessment year. Choose Revised or Updated after professional review.");
      return;
    }
    if ((returnType === "Revised" || returnType === "Updated") && !priorOriginal) {
      setError("No original training return was found. Create an Original return first, or verify the case with the reviewing CA.");
      return;
    }
    const record: ReturnRecord = { id: crypto.randomUUID(), pan, assessmentYear, form, type: returnType, status: "Prepared — CA review required", createdAt: new Date().toLocaleString("en-IN") };
    const next = [record, ...returns];
    localStorage.setItem(storageKey, JSON.stringify(next));
    setReturns(next);
    setMessage(`${returnType} ${form} training return created. It is not e-filed and has no acknowledgement number.`);
    formElement.reset();
  }

  return <main className="module-page">
    <a className="back" href="/dashboard">← Back to dashboard</a>
    <p className="eyebrow">INCOME TAX RETURN WORKSPACE</p>
    <h1>ITR preparation & review</h1>
    <a className="primary" href="/itr/estimate">Open AY 2026-27 salary tax estimate</a>
    <p className="sub">Prepare return cases for review. Return selection must be reviewed by a qualified CA before real-world use.</p>
    <p className="demo-banner"><b>Training mode:</b> return cases are locally saved practice records. There is no e-filing portal connection or ITR submission yet.</p>
    <div className="module-grid">
      <section className="journal"><h2>Start a practice return</h2><form className="client-form" onSubmit={createReturn}>
        <label>PAN<input name="pan" required pattern="[A-Za-z]{5}[0-9]{4}[A-Za-z]" placeholder="ABCDE1234F" /></label>
        <label>Assessment year<select name="assessmentYear" defaultValue="2026-27"><option>2025-26</option><option>2026-27</option><option>2027-28</option></select></label>
        <label>Suggested ITR form<select name="form" defaultValue="ITR-1"><option>ITR-1</option><option>ITR-2</option><option>ITR-3</option><option>ITR-4</option><option>ITR-5</option><option>ITR-6</option><option>ITR-7</option></select></label>
        <label>Return category<select name="returnType" defaultValue="Original"><option>Original</option><option>Revised</option><option>Updated</option></select></label>
        {error && <p className="form-error">{error}</p>}{message && <p className="ok">{message}</p>}
        <button className="primary">Create practice return</button>
      </form></section>
      <section className="journal"><h2>CA review checklist</h2><ol className="step-list"><li className="current"><span>1</span>Confirm taxpayer eligibility and ITR form</li><li><span>2</span>Verify AIS, TIS, Form 26AS and income records</li><li><span>3</span>Review tax rules for the selected assessment year</li><li><span>4</span>Approve computation before any filing action</li></ol><p className="tiny">The software cannot replace CA professional validation or portal acknowledgement.</p></section>
    </div>
    <section className="journal"><h2>Return register <span className="count">{returns.length}</span></h2>
      {returns.length === 0 ? <p className="sub">No practice return cases yet.</p> : <div className="return-list">{returns.map((item) => <article key={item.id}><Link className="return-open" href={`/itr/returns/${item.id}`}><strong>{item.type} · {item.form}</strong><p>PAN: {item.pan} · AY {item.assessmentYear}</p><small>{item.status} · {item.createdAt}</small><span className="return-open-label">Open return details →</span></Link></article>)}</div>}
    </section>
  </main>;
}

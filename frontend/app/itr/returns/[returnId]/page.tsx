"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

type ReturnRecord = { id?: string; pan: string; assessmentYear: string; form: string; type: string; status: string; createdAt: string };
const storageKey = "taxsphere_demo_itr_returns";

export default function ItrReturnDetailPage() {
  const { returnId } = useParams<{ returnId: string }>();
  const router = useRouter();
  const [record, setRecord] = useState<ReturnRecord | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("taxsphere_session")) { router.replace("/login"); return; }
    const saved: ReturnRecord[] = JSON.parse(localStorage.getItem(storageKey) ?? "[]");
    const migrated = saved.map((item) => item.id ? item : { ...item, id: crypto.randomUUID() });
    localStorage.setItem(storageKey, JSON.stringify(migrated));
    setRecord(migrated.find((item) => item.id === returnId) ?? null);
    setLoaded(true);
  }, [returnId, router]);

  return <main className="module-page return-detail">
    <Link className="back" href="/itr">← Back to return register</Link>
    {!loaded ? <p className="sub">Loading return details…</p> : !record ? <section className="journal"><h1>Return case not found</h1><p className="sub">This case may have been removed from this browser’s training register.</p></section> : <>
      <p className="eyebrow">INCOME TAX RETURN CASE</p><h1>{record.type} · {record.form}</h1>
      <p className="demo-banner"><b>Training record:</b> this is locally saved practice data. It has not been submitted to the Income Tax Department and has no acknowledgement number.</p>
      <section className="journal"><h2>Return details</h2><div className="return-facts">
        <p><strong>PAN</strong>{record.pan}</p><p><strong>Assessment year</strong>{record.assessmentYear}</p><p><strong>Suggested form</strong>{record.form}</p><p><strong>Return category</strong>{record.type}</p><p><strong>Current status</strong>{record.status}</p><p><strong>Created</strong>{record.createdAt}</p>
      </div></section>
      <section className="journal"><h2>Review status</h2><p className="warning">CA review required</p><ol className="step-list"><li className="current"><span>1</span>Confirm taxpayer eligibility and ITR form</li><li><span>2</span>Verify AIS, TIS, Form 26AS and income records</li><li><span>3</span>Review tax rules for the selected assessment year</li><li><span>4</span>Record CA approval before any filing action</li></ol><p className="tiny">This register entry does not contain a completed ITR computation or portal filing.</p></section>
    </>}
  </main>;
}

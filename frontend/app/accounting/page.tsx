"use client";

import { useMemo, useState } from "react";

type Line = { account: string; debit: string; credit: string };
const initialLines: Line[] = [{ account: "Cash in hand", debit: "", credit: "" }, { account: "Sales", debit: "", credit: "" }];

export default function AccountingPage() {
  const [lines, setLines] = useState<Line[]>(initialLines);
  const totals = useMemo(() => lines.reduce((result, line) => ({ debit: result.debit + Number(line.debit || 0), credit: result.credit + Number(line.credit || 0) }), { debit: 0, credit: 0 }), [lines]);
  const balanced = totals.debit > 0 && totals.debit === totals.credit;
  const update = (index: number, key: keyof Line, value: string) => setLines(lines.map((line, lineIndex) => lineIndex === index ? { ...line, [key]: value } : line));
  return <main className="workspace"><a href="/" className="back">Back to dashboard</a><p className="eyebrow">ACCOUNTING</p><h1>Journal entry</h1><p className="sub">Create balanced double-entry vouchers. Posting requires an authorized organization session.</p><section className="journal"><div className="journal-head"><span>Account</span><span>Debit (Rs.)</span><span>Credit (Rs.)</span></div>{lines.map((line, index) => <div className="journal-row" key={index}><input value={line.account} onChange={(event) => update(index, "account", event.target.value)} aria-label={`Account ${index + 1}`} /><input inputMode="decimal" value={line.debit} onChange={(event) => update(index, "debit", event.target.value)} aria-label={`Debit ${index + 1}`} /><input inputMode="decimal" value={line.credit} onChange={(event) => update(index, "credit", event.target.value)} aria-label={`Credit ${index + 1}`} /></div>)}<button onClick={() => setLines([...lines, { account: "", debit: "", credit: "" }])}>+ Add line</button><div className="totals"><span>Total</span><strong>Rs. {totals.debit.toFixed(2)}</strong><strong>Rs. {totals.credit.toFixed(2)}</strong></div><p className={balanced ? "ok" : "warning"}>{balanced ? "Balanced and ready to post" : "Enter matching debit and credit totals"}</p><button className="primary" disabled={!balanced}>Post journal entry</button></section></main>;
}

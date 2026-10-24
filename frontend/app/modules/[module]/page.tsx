"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type ModuleDefinition = { title: string; label: string; description: string; steps: string[]; records: string[]; action: string };

const moduleDefinitions: Record<string, ModuleDefinition> = {
  "income-tax": { title: "Income Tax workspace", label: "ITR PREPARATION DEMO", description: "Capture dummy taxpayer data, review income heads and produce a simulated calculation worksheet.", steps: ["Create taxpayer profile", "Add salary, interest and deduction records", "Compare old and new regime", "Review simulated ITR checklist"], records: ["Dummy taxpayer profile", "Form 16 data pending", "80C deduction checklist"], action: "Prepare simulated ITR" },
  "tds-tcs": { title: "TDS / TCS workspace", label: "TDS COMPLIANCE DEMO", description: "Demonstrate deductor setup, payment records, challans and quarterly-return readiness with dummy data.", steps: ["Create deductor profile", "Record a deduction", "Link dummy challan", "Review quarterly return checklist"], records: ["24Q · Q2 draft", "26Q · vendor deductions", "Challan verification pending"], action: "Create dummy deduction" },
  invoicing: { title: "Invoicing workspace", label: "BILLING DEMO", description: "Create a simulated GST invoice, track its payment status and demonstrate a professional client statement.", steps: ["Choose customer", "Add invoice line items", "Validate GST breakup", "Mark payment status"], records: ["INV-DEMO-001 · Draft", "Quotation · Awaiting approval", "Payment reminder · Scheduled"], action: "Create demo invoice" },
  reports: { title: "Reports & MIS", label: "MANAGEMENT REPORTS DEMO", description: "Explore presentation-ready financial, GST and compliance reports using safe dummy records.", steps: ["Choose financial year", "Choose report type", "Apply organization filter", "Export simulated report"], records: ["Profit & Loss · Draft", "GST liability summary", "Client compliance health"], action: "Generate demo report" },
  "compliance-calendar": { title: "Compliance calendar", label: "DEADLINES DEMO", description: "Plan GST, ITR and TDS work using a configurable internal reminder workflow.", steps: ["Create compliance task", "Assign responsible staff", "Set internal due date", "Send simulated reminder"], records: ["GSTR-1 review · Upcoming", "TDS checklist · Pending", "ITR documents · Awaiting"], action: "Add demo deadline" },
  documents: { title: "Document repository", label: "DOCUMENT MANAGEMENT DEMO", description: "Demonstrate permission-aware document collection, categorisation and review tracking with dummy files only.", steps: ["Select dummy document type", "Attach sample file", "Add metadata", "Mark reviewer status"], records: ["Dummy Form 16 · Review", "Sample purchase register · Ready", "Demo GST certificate · Expiring"], action: "Add demo document" },
  notices: { title: "Notices tracker", label: "NOTICE MANAGEMENT DEMO", description: "Track a sample notice, response date, evidence checklist and internal reviewer status.", steps: ["Register sample notice", "Set response due date", "Attach dummy evidence", "Assign reviewer"], records: ["GST notice · Sample only", "Response draft · Not submitted", "Hearing tracker · No date"], action: "Create demo notice" },
  tasks: { title: "Firm tasks", label: "WORK ALLOCATION DEMO", description: "Show how an administrator allocates client work, monitors status and reviews completion.", steps: ["Create client task", "Assign employee", "Set priority", "Move task for review"], records: ["Collect ITR documents · Open", "Review GSTR-1 · In progress", "Bank reconciliation · Assigned"], action: "Create demo task" },
  settings: { title: "Organization settings", label: "ADMINISTRATION DEMO", description: "Demonstrate secure organisation preferences, staff roles and data-protection configuration.", steps: ["Review organization profile", "Review role permissions", "Set notification preference", "Review backup status"], records: ["Organization profile · Complete", "Administrator role · Active", "Local desktop database · Active"], action: "Save demo preference" },
};

export default function ModuleDemoPage() {
  const router = useRouter();
  const params = useParams<{ module: string }>();
  const definition = useMemo(() => moduleDefinitions[params.module] ?? moduleDefinitions.reports, [params.module]);
  const [currentStep, setCurrentStep] = useState(0);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!localStorage.getItem("taxsphere_session")) router.replace("/login");
  }, [router]);

  function advance() {
    const nextStep = Math.min(currentStep + 1, definition.steps.length);
    setCurrentStep(nextStep);
    setMessage(nextStep === definition.steps.length ? "Demo workflow is ready for internal review." : "Demo record saved. Continue to the next step.");
  }

  return <main className="module-page"><a className="back" href="/dashboard">← Back to dashboard</a><p className="eyebrow">{definition.label}</p><h1>{definition.title}</h1><p className="sub">{definition.description}</p><p className="demo-banner"><b>Simulation only:</b> this module is for training and presentations. No government portal, tax filing or legal submission is performed.</p><div className="module-grid"><section className="journal"><h2>Guided workflow</h2><ol className="step-list">{definition.steps.map((step, index) => <li className={index < currentStep ? "complete" : index === currentStep ? "current" : ""} key={step}><span>{index < currentStep ? "✓" : index + 1}</span>{step}</li>)}</ol><button className="primary" onClick={advance} disabled={currentStep === definition.steps.length}>{currentStep === definition.steps.length ? "Demo workflow completed" : definition.action}</button>{message && <p className="ok">{message}</p>}</section><section className="journal"><h2>Demo work queue</h2><div className="demo-records">{definition.records.map((record, index) => <article key={record}><strong>{record}</strong><small>{index === 0 ? "Ready for review" : "Demo data · Internal use"}</small></article>)}</div></section></div></main>;
}

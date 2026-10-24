"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { loadServiceCases, saveServiceCases, ServiceCase } from "../caseStore";

type ServiceDefinition = { title: string; documents: string[]; steps: string[] };
const definitions: Record<string, ServiceDefinition> = {
  "gst-registration": { title: "GST Registration", documents: ["PAN and Aadhaar", "Business address proof", "Bank account proof"], steps: ["Capture business details", "Verify document checklist", "Prepare application draft", "Internal review"] },
  "gst-return": { title: "GST Return Preparation", documents: ["Sales register", "Purchase register", "GSTR-2B export"], steps: ["Import records", "Run validation", "Review tax summary", "Mark prepared"] },
  "gst-refund": { title: "GST Refund", documents: ["Refund working", "Invoice evidence", "Bank details"], steps: ["Assess eligibility", "Collect evidence", "Prepare claim draft", "Review status"] },
  "gst-notice": { title: "GST Notice Solution", documents: ["Notice copy", "Supporting evidence", "Response draft"], steps: ["Register notice", "Set due date", "Prepare response", "Reviewer approval"] },
  "pf-registration": { title: "PF Registration & Returns", documents: ["Employer PAN", "Employee list", "Bank details"], steps: ["Capture employer profile", "Collect employee data", "Prepare compliance draft", "Internal review"] },
  udyam: { title: "Udyam (MSME) Registration", documents: ["PAN", "Aadhaar", "Business activity details"], steps: ["Check eligibility", "Collect profile data", "Prepare registration draft", "Review checklist"] },
  trademark: { title: "Trademark & Brand", documents: ["Brand name", "Logo sample", "Goods/services class"], steps: ["Search brand details", "Choose class", "Prepare application draft", "Review filing pack"] },
  iso: { title: "ISO Certificate", documents: ["Business profile", "Process documents", "Audit checklist"], steps: ["Choose certification", "Collect documents", "Schedule audit", "Review readiness"] },
  itr: { title: "Income Tax Return", documents: ["Form 16 / income proof", "Bank interest", "Deduction evidence"], steps: ["Collect income data", "Review deductions", "Prepare computation", "CA review"] },
  tds: { title: "TDS Filing & Refund", documents: ["Deduction register", "Challan details", "Deductee PAN list"], steps: ["Collect TDS records", "Reconcile challans", "Prepare return checklist", "Internal review"] },
  audit: { title: "Balance Sheet & Audit", documents: ["Trial balance", "Bank statements", "Supporting schedules"], steps: ["Close books", "Prepare schedules", "CA review", "Mark audit pack ready"] },
  loan: { title: "Loan File & Advisor", documents: ["KYC", "ITR / financials", "Bank statement"], steps: ["Capture requirement", "Collect financials", "Prepare advisor pack", "Track lender discussion"] },
  fssai: { title: "FSSAI & Labour Licence", documents: ["Business proof", "Premises documents", "Owner KYC"], steps: ["Choose licence", "Collect documents", "Prepare application draft", "Review readiness"] },
  iec: { title: "IEC / CEPC / RCMC", documents: ["PAN", "Bank certificate", "Import-export profile"], steps: ["Select registration", "Collect business proof", "Prepare application draft", "Review checklist"] },
};

export default function ServiceCasePage() {
  const router = useRouter();
  const params = useParams<{ service: string }>();
  const definition = useMemo(() => definitions[params.service], [params.service]);
  const [error, setError] = useState("");
  const [clients, setClients] = useState<{ id: string; display_name: string }[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { router.replace("/login"); return; }
    fetch(`/api/v1/organizations/${organizationId}/clients`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async (response) => response.ok ? setClients(await response.json()) : undefined)
      .catch(() => undefined);
  }, [router]);

  function createCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    if (!definition) { setError("This service workflow was not found."); return; }
    const values = new FormData(event.currentTarget);
    const clientId = String(values.get("clientId") ?? "") || undefined;
    const selectedClient = clients.find((client) => client.id === clientId);
    const record: ServiceCase = {
      id: crypto.randomUUID(), service: params.service, serviceTitle: definition.title,
      clientName: selectedClient?.display_name ?? String(values.get("clientName")), clientId, priority: String(values.get("priority")),
      note: String(values.get("note") ?? ""), createdAt: new Date().toLocaleString("en-IN"),
      steps: definition.steps, documents: definition.documents, completedStep: 0, receivedDocuments: [],
    };
    saveServiceCases([record, ...loadServiceCases()]);
    router.push(`/services/${record.service}/${record.id}`);
  }

  if (!definition) return <main className="module-page"><a className="back" href="/services">← Back to Service Desk</a><h1>Service not found</h1></main>;
  return <main className="module-page"><a className="back" href="/services">← Back to Service Desk</a><p className="eyebrow">SERVICE CASE · TRAINING WORKFLOW</p><h1>{definition.title}</h1><p className="demo-banner"><b>Training workflow:</b> case progress and checklist statuses are saved in this browser. Uploaded files are encrypted in the workspace document store; government filing is not enabled.</p><section className="journal case-form"><h2>Create a service case</h2><form className="client-form" onSubmit={createCase}>{clients.length > 0 && <label>Link to existing client (optional)<select name="clientId" defaultValue=""><option value="">No linked client</option>{clients.map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}</select></label>}<label>Client / business name<input name="clientName" placeholder="Client or business name" required minLength={2} /></label><label>Service priority<select name="priority" defaultValue="normal"><option value="normal">Normal</option><option value="high">High</option><option value="urgent">Urgent</option></select></label><label>Internal note<input name="note" placeholder="Optional case note" /></label>{error && <p className="form-error">{error}</p>}<button className="primary">Create service case</button></form></section></main>;
}

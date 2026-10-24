"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { loadServiceCases, saveServiceCases, ServiceCase } from "../../caseStore";

type StoredDocument = { id: string; filename: string; content_type: string; document_label: string | null; created_at: string };

export default function ServiceCaseDetailPage() {
  const params = useParams<{ service: string; caseId: string }>();
  const router = useRouter();
  const [item, setItem] = useState<ServiceCase | null>(null);
  const [documents, setDocuments] = useState<StoredDocument[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [uploadingFor, setUploadingFor] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadCaseDocuments(caseId: string) {
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) return;
    const response = await fetch(`/api/v1/organizations/${organizationId}/documents?service_case_id=${caseId}`, { headers: { Authorization: `Bearer ${token}` } });
    if (response.ok) setDocuments(await response.json());
    else setError("You do not have permission to view this case's files.");
  }

  useEffect(() => {
    async function load() {
      const token = localStorage.getItem("taxsphere_session");
      if (!token) { router.replace("/login"); return; }
      const saved = loadServiceCases().find((serviceCase) => serviceCase.id === params.caseId && serviceCase.service === params.service) ?? null;
      setItem(saved);
      if (saved) await loadCaseDocuments(saved.id);
      setLoaded(true);
    }
    void load();
  }, [params.caseId, params.service, router]);

  function updateCase(update: (current: ServiceCase) => ServiceCase) {
    if (!item) return;
    const next = update(item);
    saveServiceCases(loadServiceCases().map((existing) => existing.id === item.id ? next : existing));
    setItem(next);
  }

  async function uploadDocument(event: FormEvent<HTMLFormElement>, label: string) {
    event.preventDefault(); setError(""); setMessage("");
    const formElement = event.currentTarget;
    const file = new FormData(formElement).get("file");
    if (!(file instanceof File) || file.size === 0) { setError("Choose a document first."); return; }
    if (!item) return;
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { setError("Please sign in to upload files."); return; }
    const upload = new FormData();
    upload.append("file", file);
    upload.append("service_case_id", item.id);
    upload.append("document_label", label);
    if (item.clientId) upload.append("client_id", item.clientId);
    setUploadingFor(label);
    try {
      const response = await fetch(`/api/v1/organizations/${organizationId}/documents`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: upload });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Upload failed.");
      formElement.reset();
      setMessage(`${file.name} uploaded and encrypted.`);
      await loadCaseDocuments(item.id);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Upload failed.");
    } finally { setUploadingFor(""); }
  }

  async function downloadDocument(document: StoredDocument) {
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { setError("Please sign in to download files."); return; }
    const response = await fetch(`/api/v1/organizations/${organizationId}/documents/${document.id}/download`, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) { setError("File could not be downloaded."); return; }
    const url = URL.createObjectURL(await response.blob());
    const link = window.document.createElement("a"); link.href = url; link.download = document.filename; link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  if (!loaded) return <main className="module-page"><p className="sub">Loading service case…</p></main>;
  if (!item) return <main className="module-page"><Link className="back" href="/services">← Back to Service Desk</Link><section className="journal"><h1>Case not found</h1><p className="sub">This training case is not saved in this browser.</p></section></main>;

  const isReady = item.completedStep >= item.steps.length;
  return <main className="module-page service-case-detail"><Link className="back" href="/services">← Back to Service Desk</Link><p className="eyebrow">SERVICE CASE · TRAINING WORKFLOW</p><h1>{item.serviceTitle}</h1><p className="sub">{item.clientName} · {item.priority} priority · Created {item.createdAt}</p><p className="demo-banner"><b>Training case:</b> progress is internal tracking. Uploaded files are encrypted in the workspace document store; this does not file a government application.</p>
    <div className="module-grid"><section className="journal"><h2>{item.clientName} · case progress</h2><ol className="step-list">{item.steps.map((step, index) => <li className={index < item.completedStep ? "complete" : index === item.completedStep ? "current" : ""} key={step}><span>{index < item.completedStep ? "✓" : index + 1}</span>{step}</li>)}</ol><p className={isReady ? "ok" : "sub"}>{isReady ? "Prepared for internal review" : `Current stage: ${item.steps[item.completedStep]}`}</p><button className="primary" onClick={() => updateCase((current) => ({ ...current, completedStep: Math.min(current.completedStep + 1, current.steps.length) }))} disabled={isReady}>{isReady ? "All stages marked complete" : "Mark next stage complete"}</button>{item.completedStep > 0 && <button className="case-secondary" onClick={() => updateCase((current) => ({ ...current, completedStep: Math.max(current.completedStep - 1, 0) }))}>Reopen previous stage</button>}{item.note && <p className="tiny">Internal note: {item.note}</p>}</section>
      <section className="journal"><h2>Document checklist</h2><p className="tiny">PDF, JPEG and PNG files (up to 10 MB) are encrypted at rest. Upload status does not mean the document has been reviewed.</p><div className="demo-records">{item.documents.map((label) => { const files = documents.filter((document) => document.document_label === label); const manuallyReceived = item.receivedDocuments.includes(label); return <article key={label}><strong>{label}</strong><small className={files.length ? "ok" : "warning"}>{files.length ? `${files.length} file(s) uploaded · encrypted` : "No file uploaded"}</small>{files.map((file) => <div className="service-file" key={file.id}><small>{file.filename} · {new Date(file.created_at).toLocaleString()}</small><button type="button" onClick={() => void downloadDocument(file)}>Download</button></div>)}<form className="service-upload" onSubmit={(event) => void uploadDocument(event, label)}><label>Upload a file<input type="file" name="file" accept="application/pdf,image/jpeg,image/png" required /></label><button type="submit" disabled={uploadingFor === label}>{uploadingFor === label ? "Uploading…" : "Upload securely"}</button></form><small className={manuallyReceived ? "ok" : "warning"}>Checklist: {manuallyReceived ? "Received · manually confirmed" : "Awaiting manual review"}</small><button className="case-secondary" onClick={() => updateCase((current) => ({ ...current, receivedDocuments: manuallyReceived ? current.receivedDocuments.filter((name) => name !== label) : [...current.receivedDocuments, label] }))}>{manuallyReceived ? "Mark pending" : "Confirm received"}</button></article>; })}</div>{error && <p className="form-error">{error}</p>}{message && <p className="ok">{message}</p>}</section></div>
  </main>;
}

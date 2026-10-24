"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

type Client = { id: string; display_name: string; client_type: string; pan: string | null; email: string | null; mobile: string | null; status: string };
type ClientDocument = { id: string; filename: string; content_type: string; created_at: string; status: string; encrypted_at_rest: boolean };
const apiUrl = "/api/v1";

export default function ClientDetailPage() {
  const { clientId } = useParams<{ clientId: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [documents, setDocuments] = useState<ClientDocument[]>([]);
  const [unassignedDocuments, setUnassignedDocuments] = useState<ClientDocument[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  async function loadClientFiles() {
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { setError("Please sign in to view client files."); return; }
    const headers = { Authorization: `Bearer ${token}` };
    const [clientResponse, documentsResponse, unassignedResponse] = await Promise.all([
      fetch(`${apiUrl}/organizations/${organizationId}/clients/${clientId}`, { headers }),
      fetch(`${apiUrl}/organizations/${organizationId}/documents?client_id=${clientId}`, { headers }),
      fetch(`${apiUrl}/organizations/${organizationId}/documents?unassigned=true`, { headers }),
    ]);
    if (!clientResponse.ok) { setError(clientResponse.status === 404 ? "Client not found in this workspace." : "Client details could not be loaded."); return; }
    if (!documentsResponse.ok || !unassignedResponse.ok) { setError("Client details loaded, but file access is unavailable for your role."); return; }
    setClient(await clientResponse.json());
    setDocuments(await documentsResponse.json());
    setUnassignedDocuments(await unassignedResponse.json());
    setError("");
  }

  useEffect(() => { void loadClientFiles(); }, [clientId]);

  async function uploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setMessage("");
    const formElement = event.currentTarget;
    if (!file) { setError("Choose a PDF, JPEG or PNG file first."); return; }
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { setError("Please sign in to upload client files."); return; }
    const form = new FormData(); form.append("file", file); form.append("client_id", clientId);
    setSaving(true);
    try {
      const response = await fetch(`${apiUrl}/organizations/${organizationId}/documents`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "File could not be uploaded.");
      setFile(null); formElement.reset(); setMessage("File uploaded and encrypted successfully."); await loadClientFiles();
    } catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : "File could not be uploaded."); }
    finally { setSaving(false); }
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) { setFile(event.target.files?.[0] ?? null); }

  async function linkExistingDocument(document: ClientDocument) {
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { setError("Please sign in to link client files."); return; }
    const response = await fetch(`${apiUrl}/organizations/${organizationId}/documents/${document.id}/link`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ client_id: clientId }) });
    const result = await response.json();
    if (!response.ok) { setError(result.detail ?? "File could not be linked."); return; }
    setError(""); setMessage(`${document.filename} linked to this client.`); await loadClientFiles();
  }

  async function downloadDocument(document: ClientDocument) {
    const token = localStorage.getItem("taxsphere_session");
    const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { setError("Please sign in to download client files."); return; }
    const response = await fetch(`${apiUrl}/organizations/${organizationId}/documents/${document.id}/download`, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) { setError("File could not be downloaded."); return; }
    const url = URL.createObjectURL(await response.blob());
    const link = window.document.createElement("a"); link.href = url; link.download = document.filename; link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <main className="workspace client-detail">
    <Link href="/clients" className="back">← Back to clients</Link>
    {client ? <><p className="eyebrow">CLIENT FILE</p><h1>{client.display_name}</h1><p className="sub">{client.client_type} · {client.pan ?? "PAN pending"} · {client.status}</p>
      <section className="journal client-profile"><h2>Client details</h2><div className="client-facts"><p><strong>Email</strong>{client.email ?? "Not added"}</p><p><strong>Mobile</strong>{client.mobile ?? "Not added"}</p><p><strong>Client status</strong>{client.status}</p></div></section>
      <section className="journal"><h2>Client files <span className="count">{documents.length}</span></h2><p className="sub">PDF, JPEG and PNG files are encrypted before database storage.</p>
        {documents.length === 0 ? <div className="empty-files"><strong>No files uploaded</strong><p>Documents you add for this client will appear here with their upload status.</p></div> : <div className="document-list">{documents.map((document) => <article key={document.id} className="document-row"><div><strong>{document.filename}</strong><small>{document.content_type} · {new Date(document.created_at).toLocaleString()}</small></div><div className="document-status"><span className="status-pill">Stored · Encrypted</span><button type="button" onClick={() => void downloadDocument(document)}>Download</button></div></article>)}</div>}
      </section>
      {unassignedDocuments.length > 0 && <section className="journal"><h2>Existing files to review</h2><p className="sub">These workspace files are not linked to a client yet. Link only the files that belong to this client.</p><div className="document-list">{unassignedDocuments.map((document) => <article key={document.id} className="document-row"><div><strong>{document.filename}</strong><small>{document.content_type} · {new Date(document.created_at).toLocaleString()}</small></div><button type="button" onClick={() => void linkExistingDocument(document)}>Link to this client</button></article>)}</div></section>}
      <section className="journal"><h2>Upload a client file</h2><form className="client-form" onSubmit={uploadDocument}><label>Choose file<input type="file" accept="application/pdf,image/jpeg,image/png" onChange={chooseFile} required /></label>{file && <p className="tiny">Selected: {file.name} ({Math.ceil(file.size / 1024)} KB)</p>}{error && <p className="form-error">{error}</p>}{message && <p className="ok">{message}</p>}<button className="primary" disabled={saving}>{saving ? "Uploading..." : "Upload securely"}</button></form></section>
    </> : !error ? <p className="sub">Loading client files...</p> : <p className="form-error">{error}</p>}
  </main>;
}

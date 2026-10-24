"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Integration = { service: string; provider_name: string | null; environment: string; status: string; credential_reference: string | null };
const apiUrl = "/api/v1";

export default function IntegrationsPage() {
  const router = useRouter();
  const [connections, setConnections] = useState<Integration[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  async function load() {
    const token = localStorage.getItem("taxsphere_session"); const organizationId = localStorage.getItem("taxsphere_organization_id");
    if (!token || !organizationId) { router.replace("/login"); return; }
    const response = await fetch(`${apiUrl}/organizations/${organizationId}/integrations`, { headers: { Authorization: `Bearer ${token}` } });
    if (response.ok) setConnections(await response.json());
  }
  useEffect(() => { load(); }, []);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setMessage(""); setSaving(true);
    const token = localStorage.getItem("taxsphere_session"); const organizationId = localStorage.getItem("taxsphere_organization_id"); const form = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${apiUrl}/organizations/${organizationId}/integrations`, { method: "PUT", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ service: form.get("service"), provider_name: form.get("providerName"), environment: form.get("environment"), credential_reference: form.get("credentialReference") || null }) });
      const result = await response.json(); if (!response.ok) throw new Error(result.detail ?? "Unable to save configuration");
      setMessage(result.environment === "sandbox" ? "Sandbox connection profile saved. API secrets were not stored." : "Production profile is marked approval pending. It cannot file until credentials and provider approval are verified."); await load();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to save configuration"); } finally { setSaving(false); }
  }
  async function simulate(service: string) {
    const token = localStorage.getItem("taxsphere_session"); const organizationId = localStorage.getItem("taxsphere_organization_id");
    const response = await fetch(`${apiUrl}/organizations/${organizationId}/integrations/${service}/mock-submission`, { method: "POST", headers: { Authorization: `Bearer ${token}` } }); const result = await response.json(); setMessage(result.message ?? "Simulation failed");
  }
  return <main className="module-page"><a className="back" href="/dashboard">← Back to dashboard</a><p className="eyebrow">LIVE FILING READINESS</p><h1>Government integrations</h1><p className="sub">Configure providers only after commercial agreement and approval. Store API secrets in a production secrets manager—not in this form.</p><p className="demo-banner"><b>Safety gate:</b> this app cannot mark an integration live or file a return from this screen. Verified provider onboarding and acknowledgement are required.</p><div className="module-grid"><section className="journal"><h2>Add integration profile</h2><form className="client-form" onSubmit={save}><label>Service<select name="service" defaultValue="gst"><option value="gst">GST via GSP</option><option value="income_tax">Income Tax via ERI</option></select></label><label>Provider / partner name<input name="providerName" placeholder="Enter after agreement" required /></label><label>Environment<select name="environment" defaultValue="sandbox"><option value="sandbox">Sandbox</option><option value="production">Production (approval pending)</option></select></label><label>Credential reference only<input name="credentialReference" placeholder="e.g. vault://taxsphere/gsp-prod" /></label>{error && <p className="form-error">{error}</p>}{message && <p className="ok">{message}</p>}<button className="primary" disabled={saving}>{saving ? "Saving..." : "Save readiness profile"}</button></form></section><section className="journal"><h2>Required external actions</h2><ol className="step-list"><li className="current"><span>1</span>Sign GSP agreement for GST / approved ERI route for ITR</li><li><span>2</span>Receive sandbox credentials and test specification</li><li><span>3</span>Complete CA review, security testing and provider certification</li><li><span>4</span>Receive production approval and enable verified filing</li></ol></section></div><section className="journal"><h2>Configured profiles <span className="count">{connections.length}</span></h2>{connections.length === 0 ? <p className="sub">No provider selected yet. You can prepare this screen now and enter provider information after you sign an agreement.</p> : <div className="return-list">{connections.map((item) => <article key={item.service}><strong>{item.service === "gst" ? "GST / GSP" : "Income Tax / ERI"} · {item.status.replaceAll("_", " ")}</strong><p>{item.provider_name} · {item.environment}</p><small>{item.credential_reference ?? "No credential reference stored"}</small><br /><button type="button" onClick={() => simulate(item.service)}>Run safe sandbox simulation</button></article>)}</div>}</section></main>;
}

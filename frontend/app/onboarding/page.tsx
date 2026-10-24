"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = "/api/v1";

export default function OnboardingPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${apiUrl}/auth/register`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ full_name: form.get("fullName"), email: form.get("email"), password: form.get("password"), organization_name: form.get("organizationName") }) });
      const responseBody = await response.text();
      const session = responseBody ? JSON.parse(responseBody) : {};
      if (!response.ok) throw new Error(session.detail ?? "Unable to create your workspace");
      const organizationsResponse = await fetch(`${apiUrl}/organizations`, { headers: { Authorization: `Bearer ${session.access_token}` } });
      const organizations = await organizationsResponse.json();
      localStorage.setItem("taxsphere_session", session.access_token); localStorage.setItem("taxsphere_organization_id", organizations[0].id);
      router.push("/clients");
    } catch (caughtError) { setError(caughtError instanceof SyntaxError ? "Service temporarily unavailable. Start Docker Desktop and the TaxSphere database, then try again." : caughtError instanceof Error ? caughtError.message : "Unable to create your workspace"); } finally { setSaving(false); }
  }
  return <main className="onboarding"><section><p className="eyebrow">TAXSPHERE INDIA</p><h1>Create your CA workspace</h1><p className="sub">Start managing client records in a securely isolated organization.</p><form onSubmit={submit}><label>Full name<input name="fullName" required minLength={2} /></label><label>Work email<input name="email" type="email" required /></label><label>Organization / CA firm<input name="organizationName" required minLength={2} /></label><label>Password<input name="password" type="password" required minLength={12} /></label>{error && <p className="form-error">{error}</p>}<button className="primary" disabled={saving}>{saving ? "Creating workspace..." : "Create workspace"}</button></form><p className="tiny">MVP note: live government filing is not enabled from this workspace.</p></section></main>;
}

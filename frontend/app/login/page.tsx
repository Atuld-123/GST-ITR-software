"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { FlashNotice, queueFlashNotice } from "../flash-notice";

const apiUrl = "/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setSaving(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${apiUrl}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: form.get("email"), password: form.get("password") }) });
      const responseBody = await response.text();
      const session = responseBody ? JSON.parse(responseBody) : {};
      if (!response.ok) throw new Error(session.detail ?? "Unable to sign in");
      const organizationsResponse = await fetch(`${apiUrl}/organizations`, { headers: { Authorization: `Bearer ${session.access_token}` } });
      const organizations = await organizationsResponse.json();
      if (!organizations[0]) throw new Error("No organization membership was found");
      localStorage.setItem("taxsphere_session", session.access_token); localStorage.setItem("taxsphere_organization_id", organizations[0].id);
      queueFlashNotice("Login successful");
      router.push("/dashboard");
    } catch (caughtError) { setError(caughtError instanceof SyntaxError ? "Service temporarily unavailable. Start Docker Desktop and the TaxSphere database, then try again." : caughtError instanceof Error ? caughtError.message : "Unable to sign in"); } finally { setSaving(false); }
  }
  return <main className="onboarding"><FlashNotice /><section><p className="eyebrow">TAXSPHERE INDIA DESKTOP</p><h1>Admin sign in</h1><p className="sub">This workspace is for authorized organization administrators and employees only.</p><form onSubmit={submit}><label>Work email<input name="email" type="email" required autoComplete="email" /></label><label>Password<input name="password" type="password" required autoComplete="current-password" /></label>{error && <p className="form-error">{error}</p>}<button className="primary" disabled={saving}>{saving ? "Signing in..." : "Sign in"}</button></form><p className="tiny">New organization? Use the administrator workspace setup once.</p><a className="back" href="/onboarding">Create administrator workspace</a></section></main>;
}

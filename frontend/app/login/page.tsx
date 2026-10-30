"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { FlashNotice, queueFlashNotice } from "../flash-notice";

const apiUrl = "/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setSaving(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${apiUrl}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: form.get("email"), password: form.get("password") }) });
      const responseBody = await response.text();
      const session = responseBody ? JSON.parse(responseBody) : {};
      if (!response.ok) throw new Error(session.detail ?? "Unable to sign in");
      const organizationsResponse = await fetch(`${apiUrl}/organizations`, { headers: { Authorization: `Bearer ${session.access_token}` } });
      if (!organizationsResponse.ok) {
        const organizationBody = await organizationsResponse.text();
        let detail = "Unable to load your organization. Please try again.";
        try { detail = JSON.parse(organizationBody).detail ?? detail; } catch {}
        throw new Error(detail);
      }
      const organizations = await organizationsResponse.json();
      if (!organizations[0]) throw new Error("No organization membership was found");
      localStorage.setItem("taxsphere_session", session.access_token); localStorage.setItem("taxsphere_organization_id", organizations[0].id);
      queueFlashNotice("Login successful");
      router.push("/dashboard");
    } catch (caughtError) { setError(caughtError instanceof TypeError || caughtError instanceof SyntaxError ? "Could not reach the TaxSphere API. Check that taxsphere-api is Live, wait for it to start, then try again." : caughtError instanceof Error ? caughtError.message : "Unable to sign in"); } finally { setSaving(false); }
  }
  return <main className="onboarding"><FlashNotice /><section><p className="eyebrow">TAXSPHERE INDIA DESKTOP</p><h1>Admin sign in</h1><p className="sub">This workspace is for authorized organization administrators and employees only.</p><form onSubmit={submit}><label>Work email<input name="email" type="email" required autoComplete="email" /></label><label>Password<div className="password-field"><input name="password" type={showPassword ? "text" : "password"} required autoComplete="current-password" /><button className="password-toggle" type="button" onClick={() => setShowPassword((shown) => !shown)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8"/><path d="M9.9 5.2A10.8 10.8 0 0112 5c5.5 0 9 7 9 7a15 15 0 01-3.2 4.1M6.2 6.2C3.9 7.6 2 12 2 12s3.5 7 10 7a10.5 10.5 0 004-.8"/></svg> : <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>}</button></div></label>{error && <p className="form-error">{error}</p>}<button className="primary" disabled={saving}>{saving ? "Signing in..." : "Sign in"}</button></form><p className="tiny">New organization? Use the administrator workspace setup once.</p><a className="back" href="/onboarding">Create administrator workspace</a></section></main>;
}

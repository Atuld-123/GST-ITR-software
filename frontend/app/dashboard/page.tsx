"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FlashNotice, queueFlashNotice } from "../flash-notice";

const modules = [
  ["Dashboard", "/dashboard"], ["My Clients", "/clients"], ["Service Desk", "/services"], ["GST", "/gst"], ["Income Tax", "/itr"], ["TDS / TCS", "/modules/tds-tcs"], ["Accounting", "/accounting"], ["Invoicing", "/modules/invoicing"], ["Reconciliation", "/reconciliation"], ["Reports", "/modules/reports"], ["Compliance Calendar", "/modules/compliance-calendar"], ["Documents", "/modules/documents"], ["Notices", "/modules/notices"], ["Tasks", "/modules/tasks"], ["Integrations", "/integrations"], ["Settings", "/modules/settings"],
];

export default function Home() {
  const router = useRouter();
  const [checkingSession, setCheckingSession] = useState(true);
  const [workspaceReady, setWorkspaceReady] = useState(false);
  const [financialYear, setFinancialYear] = useState("2026-27");

  useEffect(() => {
    if (!localStorage.getItem("taxsphere_session")) {
      router.replace("/login");
      return;
    }
    setWorkspaceReady(true);
    setFinancialYear(localStorage.getItem("taxsphere_financial_year") ?? "2026-27");
    setCheckingSession(false);
  }, [router]);

  function changeFinancialYear(value: string) {
    setFinancialYear(value);
    localStorage.setItem("taxsphere_financial_year", value);
  }

  function signOut() {
    localStorage.removeItem("taxsphere_session");
    localStorage.removeItem("taxsphere_organization_id");
    queueFlashNotice("Logout successful");
    router.replace("/login");
  }

  if (checkingSession) return <main className="page-loading">Checking secure session...</main>;

  return <main className="shell"><FlashNotice /><aside><div className="brand">TaxSphere <span>India</span></div><nav>{modules.map(([name, path]) => <a className={name === "Dashboard" ? "active" : path === "#" ? "disabled" : ""} href={path} aria-disabled={path === "#"} key={name}>{name}</a>)}</nav></aside><section><header><input aria-label="Global search" placeholder="Search clients, invoices, returns..." /><label className="year-select">Financial year<select aria-label="Financial year" value={financialYear} onChange={(event) => changeFinancialYear(event.target.value)}><option value="2025-26">FY 2025-26</option><option value="2026-27">FY 2026-27</option><option value="2027-28">FY 2027-28</option></select></label><button type="button">Organization</button><button type="button" className="top-link" onClick={signOut}>Sign out</button></header><div className="content"><p className="eyebrow">COMPLIANCE OVERVIEW · FY {financialYear}</p><h1>{workspaceReady ? "Your compliance workspace" : "Welcome to TaxSphere"}</h1><p className="sub">Manage your CA firm, clients, GST and accounting from one secure workspace.</p><div className="cards">{[["Sales", "Rs. 0.00"], ["Input tax credit", "Rs. 0.00"], ["Open tasks", "0"], ["Upcoming filings", "0"]].map(([label, value]) => <article key={label}><p>{label}</p><strong>{value}</strong><small>Data updates as work is recorded</small></article>)}</div><div className="grid"><article><h2>{workspaceReady ? "Available now" : "Set up your workspace"}</h2><p>{workspaceReady ? "Client management, GST sales invoices, GSTR-1 preparation, accounting journals, and GSTR-2B reconciliation are ready to test." : "Create your organization once, then use the sidebar to manage your work."}</p><a className="primary action" href={workspaceReady ? "/clients" : "/login"}>{workspaceReady ? "Open My Clients" : "Admin sign in"}</a></article><article><h2>Test checklist</h2><ol><li>Login as administrator</li><li>Create a client</li><li>Add GST registration and sales invoice</li><li>Prepare GSTR-1 summary</li><li>Record purchase and GSTR-2B data</li><li>Run reconciliation</li></ol></article></div></div></section></main>;
}

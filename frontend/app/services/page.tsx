"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loadServiceCases, ServiceCase } from "./caseStore";

const services = [
  ["gst-registration", "GST Registration", "New registration, amendment and document checklist"],
  ["gst-return", "GST Return Preparation", "GSTR-1, GSTR-3B preparation and review workflow"],
  ["gst-refund", "GST Refund", "Refund eligibility, documents and status tracker"],
  ["gst-notice", "GST Notice Solution", "Notice response checklist and internal review"],
  ["pf-registration", "PF Registration & Returns", "Employer registration and monthly compliance workflow"],
  ["udyam", "Udyam (MSME) Registration", "Eligibility details and application document checklist"],
  ["trademark", "Trademark & Brand", "Trademark application, brand logo and renewal tracker"],
  ["iso", "ISO Certificate", "Certification documents, audit and renewal workflow"],
  ["itr", "Income Tax Return", "ITR document collection and preparation checklist"],
  ["tds", "TDS Filing & Refund", "TDS data, challan and return readiness workflow"],
  ["audit", "Balance Sheet & Audit", "Accounting close, CA certification and audit checklist"],
  ["loan", "Loan File & Advisor", "Financial profile, document collection and progress tracker"],
  ["fssai", "FSSAI & Labour Licence", "Food and labour licence application workflow"],
  ["iec", "IEC / CEPC / RCMC", "Import-export registration and certificate tracker"],
];

export default function ServicesPage() {
  const router = useRouter();
  const [cases, setCases] = useState<ServiceCase[]>([]);
  useEffect(() => {
    if (!localStorage.getItem("taxsphere_session")) router.replace("/login");
    else setCases(loadServiceCases());
  }, [router]);

  return <main className="module-page"><a className="back" href="/dashboard">← Back to dashboard</a><p className="eyebrow">CLIENT SERVICE DESK</p><h1>Service workflows</h1><p className="sub">Create and track service cases for your firm.</p><p className="demo-banner"><b>Training mode:</b> case progress and checklist confirmations are saved in this browser. No government application or filing is submitted.</p>
    {cases.length > 0 && <section className="journal"><h2>My service cases <span className="count">{cases.length}</span></h2><div className="service-case-list">{cases.map((item) => <article key={item.id}><Link href={`/services/${item.service}/${item.id}`} className="service-case-link"><strong>{item.clientName} · {item.serviceTitle}</strong><p>Priority: {item.priority} · Documents received: {item.receivedDocuments.length}/{item.documents.length}</p><small>{item.completedStep >= item.steps.length ? "Prepared for internal review" : `In progress · ${item.steps[item.completedStep] ?? "Review"}`} · {item.createdAt}</small><span>Open case →</span></Link></article>)}</div></section>}
    <h2 className="service-section-title">Start a service case</h2><div className="service-grid">{services.map(([slug, title, description]) => <a className="service-card" href={`/services/${slug}`} key={slug}><p className="eyebrow">TRAINING WORKFLOW</p><h2>{title}</h2><p>{description}</p><span>Open workflow →</span></a>)}</div>
  </main>;
}

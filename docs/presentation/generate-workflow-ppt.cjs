const pptxgen = require("../../frontend/node_modules/pptxgenjs");
const path = require("path");
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "TaxSphere India";
pptx.title = "TaxSphere India - Admin and Employee Workflow";
pptx.lang = "hi-IN";

const color = { navy: "102A43", teal: "078A84", text: "10233C", muted: "627D98", pale: "EAF3F8", white: "FFFFFF" };

function header(slide, title, area) {
  slide.background = { color: color.white };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.42, fill: { color: color.navy }, line: { color: color.navy } });
  slide.addText(area.toUpperCase(), { x: 0.72, y: 0.7, w: 5.5, h: 0.18, fontSize: 10, bold: true, charSpacing: 1.3, color: color.teal, margin: 0 });
  slide.addText(title, { x: 0.72, y: 1.02, w: 12, h: 0.45, fontSize: 26, bold: true, color: color.text, margin: 0 });
  slide.addShape(pptx.ShapeType.line, { x: 0.72, y: 1.72, w: 11.9, h: 0, line: { color: "D9E2EC" } });
  slide.addText("TaxSphere India | Internal admin and employee training", { x: 0.72, y: 7.05, w: 6.5, h: 0.14, fontSize: 8, color: color.muted, margin: 0 });
}

function slide(title, area, points, note) {
  const page = pptx.addSlide();
  header(page, title, area);
  page.addText(points.map((point) => ({ text: point, options: { bullet: { indent: 16 }, hanging: 4, breakLine: true } })), { x: 0.95, y: 2.0, w: 11.35, h: 3.9, fontSize: 18, color: color.text, paraSpaceAfterPt: 15, margin: 0.04 });
  if (note) {
    page.addShape(pptx.ShapeType.roundRect, { x: 0.95, y: 6.05, w: 11.35, h: 0.55, rectRadius: 0.06, fill: { color: color.pale }, line: { color: "C7D9E8" } });
    page.addText(note, { x: 1.15, y: 6.23, w: 10.95, h: 0.15, fontSize: 10, italic: true, color: color.muted, margin: 0 });
  }
}

const cover = pptx.addSlide();
cover.background = { color: color.navy };
cover.addText("TaxSphere\nIndia", { x: 0.85, y: 0.8, w: 4, h: 0.9, fontSize: 30, bold: true, color: color.white, margin: 0 });
cover.addText("Admin & Employee\nWorkflow Guide", { x: 0.85, y: 2.25, w: 7, h: 1.2, fontSize: 32, bold: true, color: color.white, margin: 0 });
cover.addText("Internal compliance operations | Current desktop MVP", { x: 0.85, y: 3.85, w: 7, h: 0.25, fontSize: 15, color: "B5C7D9", margin: 0 });

function screenshotSlide(number, title, instruction, file) {
  const page = pptx.addSlide();
  header(page, `Step ${number}: ${title}`, "Screen walkthrough");
  page.addImage({ path: path.resolve(__dirname, "screenshots", file), x: 0.7, y: 1.95, w: 8.9, h: 4.95 });
  page.addShape(pptx.ShapeType.roundRect, { x: 9.9, y: 2.1, w: 2.65, h: 3.65, rectRadius: 0.08, fill: { color: color.pale }, line: { color: "C7D9E8" } });
  page.addText(instruction, { x: 10.18, y: 2.45, w: 2.1, h: 2.7, fontSize: 15, color: color.text, valign: "mid", margin: 0.03 });
}

screenshotSlide(1, "Dashboard", "Login ke baad yahi main screen open hoti hai. Sidebar se working module select karein.", "dashboard.png");
screenshotSlide(2, "Admin Login", "Existing admin or employee approved work email aur password enter karta hai.", "login.png");
screenshotSlide(3, "Create Workspace", "First-time only: Admin ID, organization/CA firm aur password create karein.", "onboarding.png");
screenshotSlide(4, "My Clients", "Client ka legal name, entity type, PAN aur contact details save karein.", "clients.png");
screenshotSlide(5, "GST Workspace", "GSTIN add karein, sales invoice validate karein aur prepared GSTR-1 summary dekhein.", "gst.png");
screenshotSlide(6, "Accounting", "Debit aur credit lines add karke balanced journal voucher prepare karein.", "accounting.png");
screenshotSlide(7, "Reconciliation", "Purchase register aur GSTR-2B data match karke result aur explanation review karein.", "reconciliation.png");

slide("Application purpose", "Overview", ["Internal desktop workspace for your organization’s GST, accounting and client compliance operations.", "Only organization admins and authorized employees use the software.", "Clients do not receive a login in this desktop edition.", "Current live modules: Clients, GST invoices, GSTR-1 preparation, Accounting journals and GSTR-2B reconciliation."], "Prepared return/report is different from legally filed return.");
slide("First-time admin account creation", "Admin setup", ["Click Create administrator workspace once.", "Enter full name, firm/organization name, work email and strong password.", "This creates your Admin ID and an isolated organization workspace.", "Next time, use Admin sign in with the same email and password."], "If email already exists, sign in rather than creating a duplicate workspace.");
slide("Daily admin and employee login", "Login", ["Open the TaxSphere desktop application.", "Select Admin sign in.", "Enter authorized work email and password.", "After successful login, the dashboard opens automatically.", "Use the left sidebar for My Clients, GST, Accounting and Reconciliation."], "Never share login credentials with an unauthorized person.");
slide("Client workflow", "My Clients", ["Open My Clients.", "Add client name, entity type, PAN, email and mobile number.", "Choose correct entity type: individual, proprietorship, partnership, LLP, company, trust or other.", "PAN is unique inside the organization to prevent duplicate client profiles.", "Verify source documents before saving client information."], "Create/select a client before beginning a compliance job.");
slide("GST invoices and GSTR-1", "GST", ["Add active GST registration: GSTIN, legal name and state code.", "Enter sales invoices with place of supply, recipient, HSN/SAC, taxable value and GST rate.", "System calculates CGST/SGST for intra-state supplies and IGST for inter-state supplies.", "Prepare current-month GSTR-1 summary after validated invoices are entered."], "GSTR-1 remains Prepared until an authorized GSTN/GSP filing integration confirms submission.");
slide("Accounting journals", "Accounting", ["Open Accounting and create a journal voucher.", "Enter debit and credit account lines plus narration/reference.", "Posting is allowed only when debit total equals credit total.", "Use balanced entries for receipts, payments, expenses and adjustments."], "Review voucher evidence before posting any accounting entry.");
slide("Purchase vs GSTR-2B reconciliation", "Reconciliation", ["Select GST registration and tax period.", "Record purchase-register invoices from books.", "Import or enter GSTR-2B invoice data.", "Run reconciliation to compare GSTIN, normalized invoice number, taxable value and tax amount.", "Review exact match, value mismatch, missing in books and missing in GSTR-2B explanations."], "ITC eligibility requires professional review; matching does not by itself establish eligibility.");
slide("Demo checklist", "Testing", ["Login as administrator.", "Create a sample client.", "Add GST registration and sales invoice.", "Prepare GSTR-1 summary.", "Create one balanced accounting journal.", "Add purchase and GSTR-2B entries, then run reconciliation."], "Use this sequence when presenting the current MVP to management.");
slide("Not ready yet", "Important", ["ITR tax computation and ITR filing workflow.", "TDS/TCS, PF, FSSAI, Udyam, IEC, trademark, ISO and loan workflows.", "Document uploads, reminders, WhatsApp/SMS/email integrations.", "Live GST/Income Tax submission, ARN capture, acknowledgement and e-verification."], "Do not commit unavailable software workflows to clients until implementation and testing are complete.");
slide("End-to-end standard process", "Summary", ["Admin login", "Create or select client", "Open relevant module", "Collect verified information", "Enter and validate data", "Internal review", "Prepare return/report/reconciliation", "Record filing only after verified portal acknowledgement"], "Keep approvals and supporting documents under your internal document policy.");

pptx.writeFile({ fileName: path.resolve(__dirname, "TaxSphere_Admin_Employee_Workflow.pptx") });

import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "TaxSphere India", description: "Tax and compliance workspace" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

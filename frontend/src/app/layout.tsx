import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MVM – Migraine Vulnerability Modeling",
  description: "Threshold-crossing latent state-space model",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

import "./globals.css";

export const metadata = {
  title: "Self-Healing Production Incident Agent",
  description: "Autonomous AI SRE incident response dashboard"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="bg-[#030712]">
      <body className="min-h-screen bg-[#030712] text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}

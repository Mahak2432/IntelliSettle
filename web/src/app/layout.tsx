import type { Metadata, Viewport } from "next";
import { Anek_Devanagari } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const anek = Anek_Devanagari({
  variable: "--font-anek",
  subsets: ["devanagari", "latin"],
  axes: ["wdth"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "IntelliSettle: crop loss claims settled in hours",
  description:
    "AI-verified crop insurance claims for Indian farmers. Weather, satellite radar and news checked in minutes; officers approve in one click.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f2f5f3" },
    { media: "(prefers-color-scheme: dark)", color: "#0e141c" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // next-themes sets the theme class before hydration, so the attribute differs from the server render.
    <html lang="hi" className={`${anek.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full flex flex-col">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

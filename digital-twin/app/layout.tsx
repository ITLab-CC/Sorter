import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KI-Sorter · Digitaler Zwilling",
  description: "Interaktives 3D-Modell des KI-Murmelsortierers, aufgebaut aus den 3MF-Dateien des Projekts.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}

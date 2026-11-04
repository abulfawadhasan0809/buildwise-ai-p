import "./globals.css";
import { Bricolage_Grotesque } from "next/font/google";
const f = Bricolage_Grotesque({ subsets: ["latin"], variable: "--f" });
export const metadata = { title: "BuildWise AI", description: "Speak your dream home. Watch AI design it." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body className={f.className}>{children}</body></html>;
}

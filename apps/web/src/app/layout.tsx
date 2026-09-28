import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Noto_Sans_JP, Shippori_Mincho_B1 } from "next/font/google";

import { FixtureNotice } from "@/components/domain/fixture-notice";
import { SiteFooter } from "@/components/domain/site-footer";
import { SiteHeader } from "@/components/domain/site-header";
import { getDataset } from "@/lib/data";

import "./globals.css";

// Japanese fonts have no subset list; skip preload and let unicode-range split the files.
const notoSansJp = Noto_Sans_JP({ variable: "--font-noto-sans-jp", weight: ["400", "500", "700"], preload: false });
const shippori = Shippori_Mincho_B1({ variable: "--font-shippori", weight: ["500", "700"], preload: false });
const plexSans = IBM_Plex_Sans({ variable: "--font-plex-sans", weight: ["400", "500", "600"], subsets: ["latin"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", weight: ["400"], subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "YOHAKU TOKYO — 東京の「何もない」を、データで見つける。", template: "%s | YOHAKU TOKYO" },
  description: "東京都・区市町村のオープンデータから、駅周辺の“目的地の少なさ”を数値化する。",
};

export const viewport: Viewport = {
  themeColor: "#f4f1ea",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  const dataset = getDataset();
  return (
    <html
      lang="ja"
      className={`${notoSansJp.variable} ${shippori.variable} ${plexSans.variable} ${plexMono.variable}`}
    >
      <body className="flex min-h-dvh flex-col">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-ink focus:px-3 focus:py-2 focus:text-paper"
        >
          本文へスキップ
        </a>
        <SiteHeader />
        <FixtureNotice isFixture={dataset.isFixture} fixtureFeatures={dataset.fixtureFeatures} />
        <main id="main" className="flex-1">
          {children}
        </main>
        <SiteFooter generatedAt={dataset.generatedAt} version={dataset.scoring.version} />
      </body>
    </html>
  );
}

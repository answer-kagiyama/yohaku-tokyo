import Link from "next/link";

import { Wordmark } from "./wordmark";

export function SiteFooter({ generatedAt, version }: { generatedAt: string; version: string }) {
  return (
    <footer className="mt-24 border-t border-rule-strong">
      <div className="page-container grid gap-6 py-10 text-label text-ink-muted md:grid-cols-[1fr_auto]">
        <div className="space-y-3">
          <Wordmark />
          <p className="max-w-(--yk-measure)">
            東京都・区市町村のオープンデータ上で、駅周辺に“目的地となりうる施設・機能”が
            相対的に少ない状態を「余白」と呼び、数値化しています。主観的な評価ではありません。
          </p>
        </div>
        <dl className="caption grid grid-cols-[auto_auto] gap-x-4 gap-y-1 self-end text-ink-faint">
          <dt>Scoring</dt>
          <dd className="tnum normal-case">v{version}</dd>
          <dt>Generated</dt>
          <dd className="tnum normal-case">{generatedAt.slice(0, 10)}</dd>
          <dt>Method</dt>
          <dd className="normal-case">
            <Link href="/methodology" className="underline underline-offset-4 hover:text-ink">
              算出方法
            </Link>
          </dd>
          <dt>Data</dt>
          <dd className="normal-case">
            <Link href="/data" className="underline underline-offset-4 hover:text-ink">
              データ台帳
            </Link>
          </dd>
        </dl>
      </div>
    </footer>
  );
}

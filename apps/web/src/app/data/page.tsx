import type { Metadata } from "next";

import { ProvenanceTable } from "@/components/domain/provenance-table";
import { SectionHeading } from "@/components/domain/section-heading";
import { FEATURE_KEYS, FEATURE_META } from "@/domain/features";
import { getProvenance } from "@/lib/data";

export const metadata: Metadata = { title: "データ台帳" };

export default function DataPage() {
  const p = getProvenance();
  const stats = new Map(p.features.map((f) => [f.key, f]));
  return (
    <article className="page-container pt-10 md:pt-16">
      <header className="mb-12 max-w-(--yk-measure) border-b border-rule-strong pb-6">
        <p className="caption text-ink-faint">Data register · データ台帳</p>
        <h1 className="mt-2 font-display text-title font-semibold text-ink md:text-[2.25rem]">データ台帳</h1>
        <p className="mt-4 text-body text-ink-muted">
          東京都オープンデータカタログを特徴量ごとに自動で探索し、採用したデータセットの一覧です。
          すべて取得日時と件数を記録しています。不採用・要確認のものは件数のみ示します。
        </p>
        <p className="tnum mt-2 text-[0.75rem] text-ink-faint">生成 {p.generatedAt.slice(0, 10)}</p>
      </header>

      <div className="space-y-16">
        {FEATURE_KEYS.filter((k) => stats.has(k)).map((k) => {
          const s = stats.get(k)!;
          const rows = p.datasets.filter((d) => d.feature === k);
          return (
            <section key={k} aria-labelledby={`data-${k}`}>
              <SectionHeading caption={`${FEATURE_META[k].labelEn} · ${s.accepted} datasets`} title={FEATURE_META[k].label} id={`data-${k}`} />
              <dl className="mb-4 flex flex-wrap gap-x-6 gap-y-1 text-label text-ink-muted">
                {(
                  [
                    ["候補", s.candidates],
                    ["採用", s.accepted],
                    ["要確認", s.review],
                    ["不採用", s.rejected],
                  ] as const
                ).map(([label, value]) => (
                  <div key={label} className="flex gap-1.5">
                    <dt>{label}</dt>
                    <dd className="tnum text-ink">{value.toLocaleString("ja-JP")}</dd>
                  </div>
                ))}
              </dl>
              <ProvenanceTable datasets={rows} />
            </section>
          );
        })}

        <section aria-labelledby="services">
          <SectionHeading caption="External · 外部のデータ・サービス" title="外部のデータ・サービス" id="services" />
          <ul className="divide-y divide-rule border-y border-rule">
            {p.services.map((s) => (
              <li key={s.url} className="py-3">
                <p className="text-label font-medium text-ink">{s.name}</p>
                <p className="text-[0.75rem] text-ink-muted">{s.use}</p>
                <p className="font-mono text-[0.6875rem] break-all text-ink-faint">{s.url}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </article>
  );
}

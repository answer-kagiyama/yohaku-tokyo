import type { Metadata } from "next";

import { MethodologyPanel } from "@/components/domain/methodology-panel";
import { getDataset } from "@/lib/data";

export const metadata: Metadata = { title: "算出方法" };

export default function MethodologyPage() {
  const dataset = getDataset();
  return (
    <article className="page-container pt-10 md:pt-16">
      <header className="mb-10 max-w-(--yk-measure) border-b border-rule-strong pb-6">
        <p className="caption text-ink-faint">Methodology · v{dataset.scoring.version}</p>
        <h1 className="mt-2 font-display text-title font-semibold text-ink md:text-[2.25rem]">算出方法</h1>
        <p className="mt-4 text-body text-ink-muted">
          「何もない」を、東京都・区市町村のオープンデータ上で駅周辺に“目的地となりうる施設・機能”が
          相対的に少ない状態と定義し、次の 3 段階で YOHAKU SCORE（0〜100）を算出します。
        </p>
      </header>
      <MethodologyPanel
        weights={dataset.scoring.weights}
        radiusMeters={dataset.radiusMeters}
        version={dataset.scoring.version}
      />
      <section aria-labelledby="formula" className="mt-12 max-w-(--yk-measure)">
        <h2 id="formula" className="mb-3 font-display text-heading font-semibold text-ink">
          計算式
        </h2>
        <pre className="overflow-x-auto rounded-sm border border-rule bg-paper-sunken p-4 font-mono text-[0.8125rem] leading-relaxed text-ink">
{`percentile_f = (平均順位 − 1) ÷ (駅数 − 1) × 100
low_f        = 100 − percentile_f
YOHAKU SCORE = Σ(w_f × low_f) ÷ Σ(w_f)    ※欠損 f を除く
coverage     = 利用可能な重み ÷ 全重み   （0.5 未満は判定不能）`}
        </pre>
      </section>
    </article>
  );
}

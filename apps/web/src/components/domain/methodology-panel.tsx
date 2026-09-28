import Link from "next/link";

import { FEATURE_KEYS, FEATURE_META, lowKey } from "@/domain/features";
import type { Weights } from "@/domain/schema";

type Props = {
  weights: Weights;
  radiusMeters: number;
  version: string;
  compact?: boolean;
};

const STEPS = (radius: number) => [
  {
    no: "01",
    title: "数える",
    body: `各駅から半径 ${radius}m の範囲にある、観光・文化・公共施設・公園・図書館をオープンデータから数え、駅の乗降人員を加える。`,
  },
  {
    no: "02",
    title: "比べる",
    body: "特徴量ごとに全駅の中での相対順位（percentile rank, 0〜100）へ変換する。外れ値に強く、説明しやすい。",
  },
  {
    no: "03",
    title: "反転して重ねる",
    body: "「少なさ」= 100 − percentile を重み付きで平均する。欠損した特徴量は 0 とみなさず、重みから除外する。",
  },
];

export function MethodologyPanel({ weights, radiusMeters, version, compact = false }: Props) {
  return (
    <div className="space-y-8">
      <ol className="grid gap-6 md:grid-cols-3 md:gap-8">
        {STEPS(radiusMeters).map((step) => (
          <li key={step.no} className="border-t border-ink pt-3">
            <p className="tnum caption text-vermilion">Step {step.no}</p>
            <h3 className="mt-1 font-display text-heading font-semibold text-ink">{step.title}</h3>
            <p className="mt-2 text-label leading-relaxed text-ink-muted">{step.body}</p>
          </li>
        ))}
      </ol>

      {!compact && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[20rem] border-y-2 border-rule-strong text-label">
              <caption className="caption mb-2 text-left text-ink-faint">Weights · 重み（v{version}・仮仕様）</caption>
              <thead className="bg-paper-sunken">
                <tr className="border-b border-rule-strong text-ink-muted">
                  <th scope="col" className="px-3 py-2 text-left font-medium">特徴量</th>
                  <th scope="col" className="px-3 py-2 text-left font-medium">内容</th>
                  <th scope="col" className="px-3 py-2 text-right font-medium">重み</th>
                </tr>
              </thead>
              <tbody>
                {FEATURE_KEYS.map((key) => (
                  <tr key={key} className="border-b border-rule last:border-0">
                    <th scope="row" className="px-3 py-2.5 text-left font-medium text-ink">{FEATURE_META[key].label}</th>
                    <td className="px-3 py-2.5 text-ink-muted">{FEATURE_META[key].description}</td>
                    <td className="tnum px-3 py-2.5 text-right text-ink">{Math.round(weights[lowKey(key)] * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="space-y-3 border-l-2 border-vermilion bg-paper-sunken px-4 py-3 text-label text-ink-muted">
            <p className="font-medium text-ink">この指数が言っていないこと</p>
            <ul className="list-disc space-y-1 pl-5">
              <li>「つまらない駅」「行く価値がない駅」という評価ではありません。</li>
              <li>オープンデータに載っていない店や風景は数えられていません。</li>
              <li>データ取得に失敗した項目を「施設数 0」とは扱いません。欠損として表示します。</li>
              <li>値のある駅が 3 駅未満の項目は順位に意味がないため、全駅でスコアから外します（比較不能）。</li>
              <li>
                値のない項目の重みは、残りの項目に比例して配り直します（実効重み）。定義上の重みは変えません。
              </li>
              <li>
                駅数が少ない間は、順位が重みの設定に左右されます。各駅に「重みを ±50% 変えたときの順位の幅」を表示しています。
              </li>
              <li>区ごとにデータの粒度が違うため、施設の種類を揃えて数えています（例: 公共施設は地域の集会・交流施設のみ）。</li>
              <li>AI / LLM はスコアの計算に関与しません。同じデータからは常に同じ値が出ます。</li>
            </ul>
          </div>
        </>
      )}

      {compact && (
        <p className="text-label">
          <Link href="/methodology" className="underline decoration-rule-input underline-offset-4 hover:decoration-vermilion">
            算出方法の詳細と、この指数の限界 →
          </Link>
        </p>
      )}
    </div>
  );
}

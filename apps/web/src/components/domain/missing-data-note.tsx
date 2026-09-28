import { FEATURE_META } from "@/domain/features";
import type { MissingReason } from "@/domain/stations";

const COVERAGE = { uncovered: "データなし", partial: "位置不明あり" } as const;

type Props = { reasons: MissingReason[]; coverage: number; scored: boolean };

/** Explains which data is missing and where — the honest answer to "why no score?". */
export function MissingDataNote({ reasons, coverage, scored }: Props) {
  if (reasons.length === 0) return null;
  return (
    <div className="border-l-2 border-vermilion bg-paper-sunken px-4 py-3 text-label text-ink-muted">
      <p className="font-medium text-ink">
        {scored
          ? "一部の項目はデータが揃わず、スコアから外しています。"
          : `判定に必要なデータが揃っていません（使える項目の重み ${Math.round(coverage * 100)}%、必要 50%）。`}
      </p>
      <ul className="mt-2 space-y-1">
        {reasons.map((r) => (
          <li key={r.key}>
            <span className="font-medium text-ink">{FEATURE_META[r.key].label}</span>
            {"："}
            {r.notComparable
              ? "値のある駅が少なく比較不能"
              : r.municipalities.length > 0
                ? r.municipalities.map((m) => `${m.name}（${COVERAGE[m.coverage]}）`).join("、")
                : "データなし"}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[0.75rem] text-ink-faint">
        500m 圏に掛かる区のオープンデータが揃わない項目は、0 件とみなさず欠損として扱います。
      </p>
    </div>
  );
}

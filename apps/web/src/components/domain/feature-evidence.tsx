import { FEATURE_META, type FeatureKey } from "@/domain/features";
import type { Evidence, FacilityEvidence, RidershipEvidence } from "@/domain/schema";

const COORD_LABEL = { source: "元データの座標", geocode: "住所から推定" } as const;
const COVERAGE_LABEL = { covered: "揃っている", partial: "位置不明あり", uncovered: "データなし" } as const;

/** The data behind a feature value — raw data the reader can check. */
export function FeatureEvidence({ feature, evidence }: { feature: FeatureKey; evidence: Evidence }) {
  return evidence.kind === "ridership" ? (
    <RidershipEvidenceView feature={feature} evidence={evidence} />
  ) : (
    <FacilityEvidenceView feature={feature} evidence={evidence} />
  );
}

function RidershipEvidenceView({ feature, evidence }: { feature: FeatureKey; evidence: RidershipEvidence }) {
  const meta = FEATURE_META[feature];
  return (
    <div>
      <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-display text-heading font-semibold text-ink">{meta.label}</span>
        <span className="text-label text-ink-muted">
          {evidence.count === null ? (
            <span className="font-medium text-vermilion">駅別の統計に該当なし（欠損）</span>
          ) : (
            <>
              <span className="tnum font-medium text-ink">{evidence.count.toLocaleString("ja-JP")}</span> {meta.unit}
            </>
          )}
        </span>
      </p>
      {evidence.lines.length > 0 && (
        <ol className="mt-3 divide-y divide-rule border-y border-rule">
          {evidence.lines.map((l) => (
            <li key={`${l.operator}-${l.line}`} className="grid grid-cols-[1fr_auto] items-baseline gap-x-3 py-2">
              <span className="min-w-0 text-label text-ink">
                {l.line}
                <span className="ml-2 text-[0.6875rem] text-ink-faint">{l.operator}</span>
              </span>
              <span className="tnum text-label text-ink-muted">{l.annualThousands.toLocaleString("ja-JP")} 千人/年</span>
            </li>
          ))}
        </ol>
      )}
      <p className="mt-2 text-[0.75rem] text-ink-faint">
        {evidence.measure}。{evidence.fiscalYear} 年度の年間乗車人員 ÷ 年度の日数。
      </p>
    </div>
  );
}

function FacilityEvidenceView({ feature, evidence }: { feature: FeatureKey; evidence: FacilityEvidence }) {
  const meta = FEATURE_META[feature];
  const complete = evidence.status === "complete";
  return (
    <div>
      <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-display text-heading font-semibold text-ink">{meta.label}</span>
        <span className="text-label text-ink-muted">
          半径 <span className="tnum">{evidence.radiusMeters}</span>m 内{" "}
          {complete ? (
            <>
              <span className="tnum font-medium text-ink">{evidence.count}</span> {meta.unit}
            </>
          ) : (
            <span className="font-medium text-vermilion">件数は欠損扱い</span>
          )}
        </span>
      </p>

      {!complete && (
        <p className="mt-2 border-l-2 border-vermilion bg-paper-sunken px-3 py-2 text-[0.75rem] text-ink-muted">
          圏内に掛かる区市町村のデータが揃っていないため、0 や不完全な数では数えていません。確認できた施設は
          <span className="tnum"> {evidence.lowerBound} </span>件（下限）です。
        </p>
      )}

      {evidence.facilities.length > 0 && (
        <ol className="mt-3 divide-y divide-rule border-y border-rule">
          {evidence.facilities.map((f, i) => (
            <li key={`${f.name}-${i}`} className="grid grid-cols-[1fr_auto] items-baseline gap-x-3 py-2">
              <span className="min-w-0 text-label text-ink">
                {f.name}
                <span className="ml-2 text-[0.6875rem] text-ink-faint">{COORD_LABEL[f.coordSource]}</span>
              </span>
              <span className="tnum text-label text-ink-muted">{Math.round(f.distanceM)} m</span>
            </li>
          ))}
        </ol>
      )}

      <p className="mt-2 text-[0.75rem] text-ink-faint">
        対象の区市町村:{" "}
        {evidence.municipalities
          .map(
            (m) =>
              `${m.name}（${COVERAGE_LABEL[m.coverage]}${
                m.coverage === "covered" && m.unlocated ? `、区全体で位置不明 ${m.unlocated} 件は計数外` : ""
              }）`,
          )
          .join("、")}
      </p>
    </div>
  );
}

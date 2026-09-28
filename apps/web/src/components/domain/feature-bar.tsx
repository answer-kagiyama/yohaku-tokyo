import { FEATURE_META, type FeatureKey } from "@/domain/features";
import { formatRaw } from "@/domain/stations";
import { cn } from "@/lib/utils";

type Props = {
  feature: FeatureKey;
  raw: number | null;
  percentile: number | null;
  /** The value is a fictional fixture, not real data. */
  isSample?: boolean;
  className?: string;
};

/**
 * One inspection value of the karte. Bar length = percentile (how much the station HAS, relative
 * to the others). Missing data is drawn as hatching — never as an empty (zero) bar.
 */
export function FeatureBar({ feature, raw, percentile, isSample = false, className }: Props) {
  const meta = FEATURE_META[feature];
  const missing = raw === null;
  // A value exists but too few stations have one to rank it (docs/scoring.md §2).
  const notComparable = raw !== null && percentile === null;
  const unranked = missing || notComparable;
  return (
    <div className={cn("grid grid-cols-[7.5rem_1fr_3rem] items-center gap-x-3 py-2", className)}>
      <div className="min-w-0">
        <p className="text-label font-medium whitespace-nowrap text-ink">{meta.label}</p>
        <p className="tnum truncate text-[0.6875rem] text-ink-faint">
          {missing ? "欠損" : `${formatRaw(raw)} ${meta.unit}`}
          {isSample && <span className="ml-1 text-ink-muted">· サンプル</span>}
          {notComparable && <span className="ml-1 text-ink-muted">· 比較不能</span>}
        </p>
      </div>
      <div
        role="meter"
        aria-label={`${meta.label}の周辺比（percentile）`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={unranked ? undefined : (percentile ?? undefined)}
        aria-valuetext={missing ? "データ欠損" : notComparable ? "比較不能" : `${percentile} パーセンタイル`}
        className={cn("relative h-2 rounded-sm", unranked ? "bg-missing" : "bg-data-track")}
      >
        {!unranked && (
          <span className="absolute inset-y-0 left-0 rounded-sm bg-data" style={{ width: `${percentile}%` }} />
        )}
      </div>
      <p className={cn("tnum text-right text-label", unranked ? "text-ink-faint" : "text-ink")}>
        {unranked ? "—" : `P${Math.round(percentile!)}`}
      </p>
    </div>
  );
}

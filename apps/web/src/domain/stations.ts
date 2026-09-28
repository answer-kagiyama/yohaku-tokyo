import { FEATURE_KEYS, type FeatureKey, lowKey } from "./features";
import type { Station, Weights } from "./schema";

export type SortKey = "yohaku" | "name" | FeatureKey;
export type SortDirection = "asc" | "desc";
export type SortState = { key: SortKey; direction: SortDirection };

const collator = new Intl.Collator("ja");

function sortValue(station: Station, key: SortKey): number | string | null {
  if (key === "yohaku") return station.scores.yohaku;
  // Kanji collation does not follow reading order; the romanized name is a reading proxy.
  if (key === "name") return (station.nameEn ?? station.name).toLowerCase();
  return station.normalized[key];
}

/** Stable sort. Missing values (null) always go last regardless of direction. */
export function sortStations(stations: readonly Station[], sort: SortState): Station[] {
  const sign = sort.direction === "asc" ? 1 : -1;
  return [...stations].sort((a, b) => {
    const va = sortValue(a, sort.key);
    const vb = sortValue(b, sort.key);
    if (va === null && vb === null) return 0;
    if (va === null) return 1;
    if (vb === null) return -1;
    if (typeof va === "string" && typeof vb === "string") return sign * collator.compare(va, vb);
    return sign * ((va as number) - (vb as number));
  });
}

export function filterStations(stations: readonly Station[], query: string): Station[] {
  const q = query.trim().toLowerCase();
  if (!q) return [...stations];
  return stations.filter(
    (s) =>
      s.name.includes(q) ||
      (s.nameEn?.toLowerCase().includes(q) ?? false) ||
      s.id.includes(q),
  );
}

export function rankByScore(stations: readonly Station[], limit: number): Station[] {
  return sortStations(
    stations.filter((s) => s.scores.yohaku !== null),
    { key: "yohaku", direction: "desc" },
  ).slice(0, limit);
}

/** The feature with the highest percentile — what the station relatively "has". */
export function getDominantFeature(station: Station): FeatureKey | null {
  let best: FeatureKey | null = null;
  for (const key of FEATURE_KEYS) {
    const v = station.normalized[key];
    if (v === null) continue;
    if (best === null || v > (station.normalized[best] as number)) best = key;
  }
  return best;
}

export type FeatureRow = {
  key: FeatureKey;
  raw: number | null;
  percentile: number | null;
  low: number | null;
  weight: number;
  /** Weight after redistributing unavailable features (null if this one is unavailable). */
  effectiveWeight: number | null;
  /** Points this feature contributes to the YOHAKU SCORE (null if missing). */
  contribution: number | null;
  missing: boolean;
};

export function getFeatureBreakdown(station: Station, weights: Weights): FeatureRow[] {
  const available = FEATURE_KEYS.filter((k) => station.scores[lowKey(k)] !== null);
  const covered = available.reduce((sum, k) => sum + weights[lowKey(k)], 0);
  return FEATURE_KEYS.map((key) => {
    const low = station.scores[lowKey(key)];
    const weight = weights[lowKey(key)];
    return {
      key,
      raw: station.raw[key],
      percentile: station.normalized[key],
      low,
      weight,
      effectiveWeight: low === null || covered === 0 ? null : weight / covered,
      contribution: low === null || covered === 0 ? null : (weight * low) / covered,
      missing: station.raw[key] === null,
    };
  });
}

export type ScoreBand = { key: "large" | "medium" | "small" | "unknown"; label: string };

export function getScoreBand(score: number | null): ScoreBand {
  if (score === null) return { key: "unknown", label: "判定不能" };
  if (score >= 67) return { key: "large", label: "余白 大" };
  if (score >= 34) return { key: "medium", label: "余白 中" };
  return { key: "small", label: "余白 小" };
}

export function formatScore(score: number | null): string {
  return score === null ? "—" : score.toFixed(1);
}

export function formatRaw(value: number | null): string {
  return value === null ? "欠損" : value.toLocaleString("ja-JP");
}

export function formatObservationNo(index: number): string {
  return `No. ${String(index + 1).padStart(3, "0")}`;
}

export function formatRanking(ranking: { rank: number; of: number; range: [number, number] }): {
  rank: string;
  range: string;
  stable: boolean;
} {
  const [lo, hi] = ranking.range;
  return {
    rank: `${ranking.of} 駅中 ${ranking.rank} 位`,
    range: lo === hi ? `${lo} 位` : `${lo}〜${hi} 位`,
    stable: lo === hi,
  };
}

export type MissingReason = {
  key: FeatureKey;
  /** Municipalities in the 500m radius whose data is missing or incomplete. */
  municipalities: { name: string; coverage: "partial" | "uncovered" }[];
  /** A value exists but too few stations have one (docs/scoring.md §2). */
  notComparable: boolean;
};

/** Why features are missing — for stations that cannot be scored (or partly scored). */
export function getMissingReasons(station: Station): MissingReason[] {
  const out: MissingReason[] = [];
  for (const key of FEATURE_KEYS) {
    if (station.normalized[key] !== null) continue;
    const ev = station.evidence[key];
    const municipalities =
      ev?.kind === "facilities"
        ? ev.municipalities
            .filter((m) => m.coverage !== "covered")
            .map((m) => ({ name: m.name, coverage: m.coverage as "partial" | "uncovered" }))
        : [];
    out.push({ key, municipalities, notComparable: station.raw[key] !== null });
  }
  return out;
}

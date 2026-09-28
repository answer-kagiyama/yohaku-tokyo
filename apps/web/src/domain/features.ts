/**
 * Feature definitions. Keys and order must match pipeline/src/station_pipeline/config.py
 * (order is the tie-break order for the dominant feature — docs/scoring.md §5).
 */
export const FEATURE_KEYS = [
  "tourism",
  "culture",
  "publicFacility",
  "park",
  "library",
  "stationUsage",
] as const;

export type FeatureKey = (typeof FEATURE_KEYS)[number];
export type LowScoreKey = `${FeatureKey}Low`;

export const lowKey = (key: FeatureKey): LowScoreKey => `${key}Low`;

export type FeatureMeta = {
  label: string;
  labelEn: string;
  unit: string;
  description: string;
};

export const FEATURE_META: Record<FeatureKey, FeatureMeta> = {
  tourism: {
    label: "観光",
    labelEn: "Tourism",
    unit: "件",
    description: "半径内の観光施設・名所の数",
  },
  culture: {
    label: "文化",
    labelEn: "Culture",
    unit: "件",
    description: "半径内の文化財・文化施設の数",
  },
  publicFacility: {
    label: "公共施設",
    labelEn: "Public",
    unit: "件",
    description: "半径内の公共施設（地域センター・区民館など）の数",
  },
  park: {
    label: "公園",
    labelEn: "Park",
    unit: "件",
    description: "半径内の公園・児童遊園・緑地の数",
  },
  library: {
    label: "図書館",
    labelEn: "Library",
    unit: "館",
    description: "半径内の図書館の数",
  },
  stationUsage: {
    label: "駅利用",
    labelEn: "Ridership",
    unit: "人/日",
    description: "1 日平均乗車人員（全社・全線の合算。JR は乗車のみ公表のため乗車に統一）",
  },
};

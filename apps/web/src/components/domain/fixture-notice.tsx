import { FEATURE_KEYS, FEATURE_META, type FeatureKey } from "@/domain/features";

type Props = { isFixture: boolean; fixtureFeatures: FeatureKey[] };

/** Footnote while any feature is still a fixture — sample values must never pass as real data. */
export function FixtureNotice({ isFixture, fixtureFeatures }: Props) {
  if (!isFixture) return null;
  const sample = fixtureFeatures.length > 0 ? fixtureFeatures : [...FEATURE_KEYS];
  const real = FEATURE_KEYS.filter((k) => !sample.includes(k));
  const label = (keys: readonly FeatureKey[]) => keys.map((k) => FEATURE_META[k].label).join("・");
  return (
    <div role="note" className="border-b border-rule bg-paper-sunken">
      <p className="page-container py-2 text-label text-ink-muted">
        <span className="mr-1.5 font-semibold text-vermilion">※</span>
        {real.length > 0 && (
          <>
            <strong className="font-medium text-ink">{label(real)}</strong>は東京都オープンデータに基づく実データ。
          </>
        )}
        <strong className="font-medium text-ink">{label(sample)}</strong>
        は開発用の架空のサンプル値です。スコアはまだ参考値です。
      </p>
    </div>
  );
}

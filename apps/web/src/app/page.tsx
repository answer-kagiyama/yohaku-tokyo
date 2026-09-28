import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { MethodologyPanel } from "@/components/domain/methodology-panel";
import { SectionHeading } from "@/components/domain/section-heading";
import { Button } from "@/components/ui/button";
import { FEATURE_META } from "@/domain/features";
import { formatObservationNo, formatScore, getDominantFeature, getScoreBand, rankByScore } from "@/domain/stations";
import { getDataset, getStationIndex } from "@/lib/data";

export default function HomePage() {
  const dataset = getDataset();
  const featured = rankByScore(dataset.stations, 3);
  const sourceCount = new Set(dataset.stations.flatMap((s) => s.sources.map((src) => src.id))).size;

  return (
    <>
      {/* Masthead */}
      <section aria-labelledby="hero-title" className="ruled-paper border-b border-rule">
        <div className="page-container grid gap-10 pt-14 pb-16 md:pt-24 md:pb-24 lg:grid-cols-[1fr_16rem] lg:items-end">
          <div>
            <p className="caption text-ink-faint">Field notes on Tokyo&apos;s empty spaces</p>
            <h1
              id="hero-title"
              className="mt-4 font-display text-[2.25rem] leading-[1.25] font-semibold text-ink sm:text-[3rem] md:text-[3.75rem]"
            >
              {/* Phrase-level spans so Japanese wraps at 文節 boundaries, never orphaning 「を、」. */}
              <span className="inline-block">東京の</span>
              <span className="inline-block">「何もない」を、</span>
              <br />
              <span className="inline-block">データで</span>
              <span className="inline-block">見つける。</span>
            </h1>
            <p className="mt-6 max-w-(--yk-measure) text-body text-ink-muted">
              駅から半径 {dataset.radiusMeters}m に、観光・文化・公共施設といった“目的地”がどれだけあるか。
              オープンデータを数え、比べ、少なさを「余白」として記録します。
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
              <Button asChild size="lg">
                <Link href="/stations">
                  駅の記録を見る
                  <ArrowRight data-icon="inline-end" strokeWidth={1.5} />
                </Link>
              </Button>
              <Button asChild variant="link">
                <Link href="/methodology">算出方法</Link>
              </Button>
            </div>
          </div>

          {/* Colophon — the dataset at a glance, as a document spec rather than KPI tiles */}
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 border-t border-ink pt-3 text-label">
            <dt className="caption self-center text-ink-faint">Stations</dt>
            <dd className="tnum text-right text-ink">{dataset.stations.length} 駅</dd>
            <dt className="caption self-center text-ink-faint">Radius</dt>
            <dd className="tnum text-right text-ink">{dataset.radiusMeters} m</dd>
            <dt className="caption self-center text-ink-faint">Sources</dt>
            <dd className="tnum text-right text-ink">{sourceCount} 件</dd>
            <dt className="caption self-center text-ink-faint">Method</dt>
            <dd className="text-right text-ink">percentile rank</dd>
          </dl>
        </div>
      </section>

      {/* Featured */}
      <section aria-labelledby="featured-title" className="page-container mt-16 md:mt-24">
        <SectionHeading caption="Featured · 余白の大きい駅" title="注目の余白" id="featured-title">
          <Link href="/stations" className="shrink-0 pb-1 text-label text-ink-muted underline underline-offset-4 hover:text-ink">
            すべての駅
          </Link>
        </SectionHeading>
        <ol>
          {featured.map((s, rank) => {
            const dominant = getDominantFeature(s);
            return (
              <li key={s.id} className="border-b border-rule">
                <Link
                  href={`/stations/${s.id}`}
                  className="group grid grid-cols-[2rem_1fr_auto] items-baseline gap-x-4 py-5 md:grid-cols-[3rem_1fr_12rem_8rem] md:py-6"
                >
                  <span className="tnum text-heading text-ink-faint">{rank + 1}</span>
                  <span className="min-w-0">
                    <span className="tnum caption block text-ink-faint">
                      {formatObservationNo(getStationIndex(s.id))} · {s.municipality}
                    </span>
                    <span className="font-display text-[1.75rem] leading-tight font-semibold text-ink group-hover:underline group-hover:underline-offset-[6px] md:text-[2.25rem]">
                      {s.name}
                    </span>
                    <span className="caption ml-3 text-ink-faint">{s.nameEn}</span>
                  </span>
                  <span className="hidden text-label text-ink-muted md:block">
                    {getScoreBand(s.scores.yohaku).label}
                    {dominant && <span className="block text-ink-faint">目立つもの: {FEATURE_META[dominant].label}</span>}
                  </span>
                  <span className="tnum text-right text-[2rem] leading-none font-medium text-vermilion md:text-[2.75rem]">
                    {formatScore(s.scores.yohaku)}
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
      </section>

      {/* What is the index */}
      <section aria-labelledby="index-title" className="page-container mt-20 md:mt-28">
        <SectionHeading caption="The index · 何もなさ指数とは" title="「何もない」は、主観ではなく相対値" id="index-title" />
        <p className="mb-10 max-w-(--yk-measure) text-body text-ink-muted">
          YOHAKU SCORE は 0〜100。高いほど、オープンデータ上で駅の周りに“目的地”が相対的に少ないことを示します。
          すべての数値に元データと出典があり、同じデータからは常に同じ値が出ます。
        </p>
        <MethodologyPanel
          weights={dataset.scoring.weights}
          radiusMeters={dataset.radiusMeters}
          version={dataset.scoring.version}
          compact
        />
      </section>
    </>
  );
}

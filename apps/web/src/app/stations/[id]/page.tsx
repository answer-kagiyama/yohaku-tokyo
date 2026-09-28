import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { DataSourceList } from "@/components/domain/data-source-list";
import { FeatureBar } from "@/components/domain/feature-bar";
import { FeatureBreakdownTable } from "@/components/domain/feature-breakdown-table";
import { FeatureEvidence } from "@/components/domain/feature-evidence";
import { MissingDataNote } from "@/components/domain/missing-data-note";
import { MethodologyPanel } from "@/components/domain/methodology-panel";
import { SectionHeading } from "@/components/domain/section-heading";
import { StationScore } from "@/components/domain/station-score";
import { FEATURE_KEYS, FEATURE_META } from "@/domain/features";
import {
  formatObservationNo,
  getDominantFeature,
  getFeatureBreakdown,
  getMissingReasons,
} from "@/domain/stations";
import { getAllStations, getDataset, getStationById, getStationIndex } from "@/lib/data";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllStations().map((s) => ({ id: s.id }));
}

export async function generateMetadata({ params }: PageProps<"/stations/[id]">): Promise<Metadata> {
  const { id } = await params;
  const station = getStationById(id);
  return station ? { title: `${station.name}駅のカルテ` } : {};
}

export default async function StationPage({ params }: PageProps<"/stations/[id]">) {
  const { id } = await params;
  const station = getStationById(id);
  if (!station) notFound();

  const dataset = getDataset();
  const rows = getFeatureBreakdown(station, dataset.scoring.weights);
  const dominant = getDominantFeature(station);
  const sample = dataset.fixtureFeatures;
  const evidenced = FEATURE_KEYS.filter((k) => station.evidence[k]);

  return (
    <article className="page-container pt-6 md:pt-10">
      <Link
        href="/stations"
        className="-ml-1 inline-flex h-11 items-center gap-1 px-1 text-label text-ink-muted hover:text-ink"
      >
        <ArrowLeft aria-hidden className="size-4" strokeWidth={1.5} />
        駅一覧
      </Link>

      <div className="mt-2 grid grid-cols-[minmax(0,1fr)] gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
        {/* Left: header + findings. Sticky on desktop. */}
        <div className="min-w-0 lg:sticky lg:top-8 lg:self-start">
          <header className="border-b border-rule-strong pb-5">
            <p className="tnum caption text-ink-faint">
              Station karte · {formatObservationNo(getStationIndex(station.id))}
              {station.municipality && ` · ${station.municipality}`}
            </p>
            <h1 className="mt-2 font-display text-display font-semibold text-ink md:text-[4rem]">{station.name}</h1>
            <p className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span className="caption text-ink-muted">{station.nameEn}</span>
              <span className="font-mono text-[0.6875rem] text-ink-faint">
                {station.lat.toFixed(4)}°N {station.lng.toFixed(4)}°E
              </span>
            </p>
            {station.lines.length > 0 && (
              <p className="mt-3 text-[0.75rem] leading-relaxed text-ink-muted">{station.lines.join(" / ")}</p>
            )}
          </header>

          <section aria-label="所見" className="pt-5">
            <StationScore
              score={station.scores.yohaku}
              coverage={station.scores.coverage}
              ranking={station.ranking}
            />
            <MissingDataNote
              reasons={getMissingReasons(station)}
              coverage={station.scores.coverage}
              scored={station.scores.yohaku !== null}
            />
            <p className="mt-4 text-label text-ink-muted">
              半径 {dataset.radiusMeters}m 内の目的地を比較対象 {dataset.stations.length} 駅と比べた値です。
              {dominant && (
                <>
                  この駅で相対的に目立つのは<strong className="font-medium text-ink">「{FEATURE_META[dominant].label}」</strong>。
                </>
              )}
            </p>
          </section>
        </div>

        {/* Right: inspection values, table, sources, method */}
        <div className="min-w-0 space-y-14">
          <section aria-labelledby="values-title">
            <SectionHeading caption="Inspection values · 周辺比" title="検査値" id="values-title" as="h2" className="mb-2" />
            <p className="mb-2 text-[0.75rem] text-ink-faint">
              バーの長さは比較対象駅の中での多さ（percentile）。短いほど「何もない」。斜線はデータ欠損または比較不能。
              {sample.length > 0 && "「サンプル」は架空の値。"}
            </p>
            <div className="divide-y divide-rule">
              {rows.map((r) => (
                <FeatureBar
                  key={r.key}
                  feature={r.key}
                  raw={r.raw}
                  percentile={r.percentile}
                  isSample={sample.includes(r.key)}
                />
              ))}
            </div>
          </section>

          {evidenced.length > 0 && (
            <section aria-labelledby="evidence-title">
              <SectionHeading caption="Evidence · 実データの根拠" title="根拠" id="evidence-title" />
              <div className="space-y-8">
                {evidenced.map((k) => (
                  <FeatureEvidence key={k} feature={k} evidence={station.evidence[k]!} />
                ))}
              </div>
            </section>
          )}

          <section aria-labelledby="breakdown-title">
            <SectionHeading caption="Breakdown · 内訳" title="スコアの内訳" id="breakdown-title" />
            <FeatureBreakdownTable rows={rows} score={station.scores.yohaku} sampleFeatures={sample} />
          </section>

          <section aria-labelledby="sources-title">
            <SectionHeading caption="Sources · 出典" title="出典" id="sources-title" />
            <DataSourceList sources={station.sources} />
          </section>

          <section aria-labelledby="method-title">
            <SectionHeading caption="Methodology · 算出方法" title="算出方法" id="method-title" />
            <MethodologyPanel
              weights={dataset.scoring.weights}
              radiusMeters={dataset.radiusMeters}
              version={dataset.scoring.version}
              compact
            />
          </section>
        </div>
      </div>
    </article>
  );
}

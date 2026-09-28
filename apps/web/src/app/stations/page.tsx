import type { Metadata } from "next";

import { SectionHeading } from "@/components/domain/section-heading";
import { StationLedger } from "@/features/stations/station-ledger";
import { getDataset } from "@/lib/data";

export const metadata: Metadata = { title: "駅一覧" };

export default function StationsPage() {
  const dataset = getDataset();
  const observationIndex = Object.fromEntries(dataset.stations.map((s, i) => [s.id, i]));
  return (
    <div className="page-container pt-10 md:pt-16">
      <SectionHeading caption="Station explorer · 観測駅一覧" title="駅一覧" as="h2" className="mb-3" />
      <h1 className="sr-only">駅一覧</h1>
      <p className="mb-8 max-w-(--yk-measure) text-label text-ink-muted">
        半径 {dataset.radiusMeters}m の目的地の少なさで並べた、観測中の駅の台帳です。駅名を選ぶと、その駅のカルテを開きます。
      </p>
      <StationLedger stations={dataset.stations} observationIndex={observationIndex} />
    </div>
  );
}

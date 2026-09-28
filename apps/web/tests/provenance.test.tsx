import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProvenanceTable } from "@/components/domain/provenance-table";
import raw from "@/data/provenance.json";
import { parseProvenance, type ProvenanceDataset } from "@/domain/provenance";

const base: ProvenanceDataset = {
  feature: "park",
  datasetId: "a",
  name: "都市公園・都立公園一覧",
  organization: "台東区",
  license: "CC-BY-4.0",
  sourceUrl: "https://catalog.data.metro.tokyo.lg.jp/dataset/a",
  status: "accepted",
  autoStatus: "accepted",
  reviewNote: null,
  reason: "r",
  ingest: { status: "ok", retrievedAt: "2026-09-28T01:00:00Z", rows: 63, located: 63, unlocated: 0, excluded: 0 },
};

describe("provenance.json", () => {
  it("parses and lists only accepted datasets", () => {
    const p = parseProvenance(raw);
    expect(p.datasets.length).toBeGreaterThan(0);
    expect(p.features.map((f) => f.key)).toContain("park");
  });
});

describe("ProvenanceTable", () => {
  it("links to the catalog and shows ingest stats", () => {
    render(<ProvenanceTable datasets={[base]} />);
    const link = screen.getByRole("link", { name: /都市公園・都立公園一覧/ });
    expect(link).toHaveAttribute("href", base.sourceUrl);
    const row = screen.getAllByRole("row")[1];
    expect(within(row).getByText("2026-09-28")).toBeInTheDocument();
    expect(within(row).getAllByText("63")).toHaveLength(2);
    expect(within(row).getByText("取得済み")).toBeInTheDocument();
  });

  it("marks human-reviewed acceptance and non-facility sources", () => {
    render(
      <ProvenanceTable
        datasets={[
          { ...base, datasetId: "b", autoStatus: "rejected", reviewNote: "文京区には文化財一覧がない" },
          { ...base, datasetId: "c", name: "東京都統計年鑑", ingest: null },
        ]}
      />,
    );
    expect(screen.getByText("人手で採用: 文京区には文化財一覧がない")).toBeInTheDocument();
    expect(screen.getByText("統計表（施設リスト以外）")).toBeInTheDocument();
  });
});

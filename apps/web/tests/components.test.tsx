import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataSourceList } from "@/components/domain/data-source-list";
import { FeatureBar } from "@/components/domain/feature-bar";
import { FeatureBreakdownTable } from "@/components/domain/feature-breakdown-table";
import { MethodologyPanel } from "@/components/domain/methodology-panel";
import { MissingDataNote } from "@/components/domain/missing-data-note";
import { StationScore } from "@/components/domain/station-score";
import { getFeatureBreakdown } from "@/domain/stations";

import { makeDataset, makeStation } from "./factories";

const weights = makeDataset([]).scoring.weights;

describe("StationScore", () => {
  it("renders the score and band", () => {
    render(<StationScore score={91.7} coverage={1} />);
    expect(screen.getByLabelText("スコア 91.7 / 100")).toHaveTextContent("91.7");
    expect(screen.getByText("余白 大")).toBeInTheDocument();
    expect(screen.queryByText(/データ充足率/)).not.toBeInTheDocument();
  });

  it("shows coverage when data is partially missing", () => {
    render(<StationScore score={50} coverage={0.9} />);
    expect(screen.getByText(/データ充足率/)).toHaveTextContent("90%");
  });

  it("shows rank and its sensitivity range", () => {
    render(<StationScore score={50} coverage={0.75} ranking={{ rank: 2, of: 5, range: [2, 3] }} />);
    expect(screen.getByText("5 駅中 2 位")).toBeInTheDocument();
    expect(screen.getByText("2〜3 位")).toBeInTheDocument();
  });

  it("renders an undeterminable score", () => {
    render(<StationScore score={null} coverage={0.3} />);
    expect(screen.getByLabelText("スコア判定不能")).toHaveTextContent("—");
    expect(screen.getByText("判定不能")).toBeInTheDocument();
  });
});

describe("FeatureBar", () => {
  it("renders raw value, unit and percentile", () => {
    render(<FeatureBar feature="culture" raw={6} percentile={75} />);
    expect(screen.getByText("文化")).toBeInTheDocument();
    expect(screen.getByText("6 件")).toBeInTheDocument();
    const meter = screen.getByRole("meter");
    expect(meter).toHaveAttribute("aria-valuenow", "75");
    expect(screen.getByText("P75")).toBeInTheDocument();
  });

  it("distinguishes missing data from zero", () => {
    const { container } = render(
      <>
        <FeatureBar feature="library" raw={null} percentile={null} />
        <FeatureBar feature="park" raw={0} percentile={0} />
      </>,
    );
    const [missing, zero] = screen.getAllByRole("meter");
    expect(missing).toHaveAttribute("aria-valuetext", "データ欠損");
    expect(missing).not.toHaveAttribute("aria-valuenow");
    expect(missing.className).toContain("bg-missing");
    expect(zero).toHaveAttribute("aria-valuenow", "0");
    expect(zero.className).not.toContain("bg-missing");
    expect(within(container).getByText("欠損")).toBeInTheDocument();
    expect(within(container).getByText("0 件")).toBeInTheDocument();
  });
});

describe("FeatureBreakdownTable", () => {
  it("lists every feature and the total score", () => {
    const station = makeStation({ id: "a" });
    render(<FeatureBreakdownTable rows={getFeatureBreakdown(station, weights)} score={50} />);
    const rows = screen.getAllByRole("row");
    expect(rows).toHaveLength(1 + 6 + 1); // header + features + total
    expect(screen.getByText("YOHAKU SCORE")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "実効重み" })).toBeInTheDocument();
    expect(screen.getAllByText("25.0%")).toHaveLength(1); // full coverage: effective = defined
  });
});

describe("MethodologyPanel", () => {
  it("renders the weights table with all features", () => {
    render(<MethodologyPanel weights={weights} radiusMeters={500} version="0.1.0-mvp" />);
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(7);
    expect(within(table).getByText("観光")).toBeInTheDocument();
    expect(within(table).getByText("25%")).toBeInTheDocument();
    expect(screen.getByText(/半径 500m/)).toBeInTheDocument();
    expect(screen.getByText(/施設数 0/)).toBeInTheDocument();
  });

  it("compact mode links to the full methodology", () => {
    render(<MethodologyPanel weights={weights} radiusMeters={500} version="x" compact />);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /算出方法の詳細/ })).toHaveAttribute("href", "/methodology");
  });
});

describe("DataSourceList", () => {
  it("renders fixture sources without a link and marks them as samples", () => {
    render(<DataSourceList sources={makeStation({ id: "a" }).sources} />);
    expect(screen.getByText("サンプル")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText(/URL なし/)).toBeInTheDocument();
  });

  it("labels a source without features as the station master", () => {
    render(
      <DataSourceList
        sources={[{ id: "mlit-n02", name: "国土数値情報 鉄道データ（N02）", organization: "国土交通省", url: "https://n02", license: "CC BY 4.0", features: [], kind: "opendata" }]}
      />,
    );
    expect(screen.getByText("対象: 駅の位置・路線")).toBeInTheDocument();
  });

  it("links real sources in a new tab", () => {
    render(
      <DataSourceList
        sources={[
          { id: "p", name: "台東区 公園一覧", organization: "台東区", url: "https://example.org/parks.csv", license: "CC BY 4.0", features: ["park"], kind: "opendata" },
        ]}
      />,
    );
    const link = screen.getByRole("link", { name: /台東区 公園一覧/ });
    expect(link).toHaveAttribute("href", "https://example.org/parks.csv");
    expect(link).toHaveAttribute("target", "_blank");
    expect(screen.getByText("対象: 公園")).toBeInTheDocument();
  });
});

describe("MissingDataNote", () => {
  it("explains an unscored station", () => {
    render(
      <MissingDataNote
        scored={false}
        coverage={0.4}
        reasons={[{ key: "culture", municipalities: [{ name: "渋谷区", coverage: "uncovered" }], notComparable: false }]}
      />,
    );
    expect(screen.getByText(/使える項目の重み 40%、必要 50%/)).toBeInTheDocument();
    expect(screen.getByText(/渋谷区（データなし）/)).toBeInTheDocument();
  });

  it("renders nothing when nothing is missing", () => {
    const { container } = render(<MissingDataNote scored coverage={1} reasons={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FeatureBar } from "@/components/domain/feature-bar";
import { FeatureEvidence } from "@/components/domain/feature-evidence";
import { FixtureNotice } from "@/components/domain/fixture-notice";
import type { Evidence, FacilityEvidence } from "@/domain/schema";

const complete: FacilityEvidence = {
  kind: "facilities",
  status: "complete",
  radiusMeters: 500,
  count: 2,
  lowerBound: 2,
  municipalities: [
    { code: "13101", name: "千代田区", coverage: "covered", unlocated: 0 },
    { code: "13106", name: "台東区", coverage: "covered", unlocated: 7 },
  ],
  facilities: [
    { name: "秋葉原公園", distanceM: 135.1, coordSource: "geocode" },
    { name: "練塀公園", distanceM: 403.4, coordSource: "source" },
  ],
};

describe("FeatureEvidence", () => {
  it("lists facilities with distance and coordinate provenance", () => {
    render(<FeatureEvidence feature="park" evidence={complete} />);
    expect(screen.getByText("公園")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText("135 m")).toBeInTheDocument();
    expect(screen.getByText("住所から推定")).toBeInTheDocument();
    expect(screen.getByText("元データの座標")).toBeInTheDocument();
    expect(
      screen.getByText(/千代田区（揃っている）、台東区（揃っている、区全体で位置不明 7 件は計数外）/),
    ).toBeInTheDocument();
  });

  it("explains an incomplete count instead of showing a number", () => {
    render(
      <FeatureEvidence
        feature="park"
        evidence={{
          ...complete,
          status: "incomplete",
          count: null,
          lowerBound: 2,
          municipalities: [{ code: "13103", name: "港区", coverage: "uncovered", unlocated: 0 }],
        }}
      />,
    );
    expect(screen.getByText("件数は欠損扱い")).toBeInTheDocument();
    expect(screen.getByText(/下限/)).toHaveTextContent("2");
    expect(screen.getByText(/港区（データなし）/)).toBeInTheDocument();
  });
});

describe("FeatureEvidence (ridership)", () => {
  const ridership: Evidence = {
    kind: "ridership",
    status: "complete",
    count: 338658,
    fiscalYear: 2024,
    measure: "1日平均乗車人員（全社・全線の合算）",
    lines: [
      { operator: "JR東日本", line: "東北本線", annualThousands: 80819 },
      { operator: "東京地下鉄株式会社", line: "日比谷線", annualThousands: 20138 },
    ],
  };

  it("shows the per-line breakdown and the measure", () => {
    render(<FeatureEvidence feature="stationUsage" evidence={ridership} />);
    expect(screen.getByText("338,658")).toBeInTheDocument();
    expect(screen.getByText("80,819 千人/年")).toBeInTheDocument();
    expect(screen.getByText("日比谷線")).toBeInTheDocument();
    expect(screen.getByText(/2024 年度/)).toBeInTheDocument();
  });

  it("marks a station missing from the tables", () => {
    render(<FeatureEvidence feature="stationUsage" evidence={{ ...ridership, count: null, status: "incomplete", lines: [] }} />);
    expect(screen.getByText(/該当なし（欠損）/)).toBeInTheDocument();
  });
});

describe("FixtureNotice", () => {
  it("says which features are real and which are samples", () => {
    render(<FixtureNotice isFixture fixtureFeatures={["tourism", "culture", "publicFacility", "library", "stationUsage"]} />);
    const note = screen.getByRole("note");
    expect(note).toHaveTextContent("公園は東京都オープンデータに基づく実データ");
    expect(note).toHaveTextContent("観光・文化・公共施設・図書館・駅利用は開発用の架空のサンプル値");
  });

  it("treats everything as sample when the list is empty", () => {
    render(<FixtureNotice isFixture fixtureFeatures={[]} />);
    expect(screen.getByRole("note")).not.toHaveTextContent("実データ");
  });

  it("renders nothing for real data", () => {
    const { container } = render(<FixtureNotice isFixture={false} fixtureFeatures={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("FeatureBar not comparable", () => {
  it("shows the raw value but no rank, and does not call it missing", () => {
    render(<FeatureBar feature="tourism" raw={8} percentile={null} />);
    expect(screen.getByText(/8 件/)).toBeInTheDocument();
    expect(screen.getByText("· 比較不能")).toBeInTheDocument();
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuetext", "比較不能");
    expect(screen.queryByText("欠損")).not.toBeInTheDocument();
  });
});

describe("FeatureBar sample marker", () => {
  it("marks fixture values", () => {
    render(<FeatureBar feature="tourism" raw={3} percentile={50} isSample />);
    expect(screen.getByText("· サンプル")).toBeInTheDocument();
  });
});

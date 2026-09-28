import { describe, expect, it } from "vitest";

import {
  filterStations,
  formatRanking,
  getMissingReasons,
  getDominantFeature,
  getFeatureBreakdown,
  getScoreBand,
  rankByScore,
  sortStations,
} from "@/domain/stations";

import { makeStation } from "./factories";

const a = makeStation({ id: "a", name: "秋葉原", nameEn: "Akihabara", scores: { ...makeStation({ id: "x" }).scores, yohaku: 20 } });
const b = makeStation({ id: "b", name: "浅草橋", nameEn: "Asakusabashi", scores: { ...makeStation({ id: "x" }).scores, yohaku: 90 } });
const c = makeStation({ id: "c", name: "神田", nameEn: "Kanda", scores: { ...makeStation({ id: "x" }).scores, yohaku: null } });

describe("sortStations", () => {
  it("sorts by score descending", () => {
    expect(sortStations([a, b, c], { key: "yohaku", direction: "desc" }).map((s) => s.id)).toEqual(["b", "a", "c"]);
  });

  it("sorts by score ascending, nulls always last", () => {
    expect(sortStations([c, b, a], { key: "yohaku", direction: "asc" }).map((s) => s.id)).toEqual(["a", "b", "c"]);
  });

  it("sorts by Japanese name", () => {
    expect(sortStations([c, a, b], { key: "name", direction: "asc" }).map((s) => s.name)).toEqual(["秋葉原", "浅草橋", "神田"]);
  });

  it("sorts by a feature percentile", () => {
    const x = makeStation({ id: "x", normalized: { ...a.normalized, park: 10 } });
    const y = makeStation({ id: "y", normalized: { ...a.normalized, park: 90 } });
    const z = makeStation({ id: "z", normalized: { ...a.normalized, park: null } });
    expect(sortStations([x, z, y], { key: "park", direction: "desc" }).map((s) => s.id)).toEqual(["y", "x", "z"]);
  });

  it("does not mutate input", () => {
    const input = [a, b];
    sortStations(input, { key: "yohaku", direction: "desc" });
    expect(input.map((s) => s.id)).toEqual(["a", "b"]);
  });
});

describe("filterStations", () => {
  it("matches Japanese name", () => {
    expect(filterStations([a, b, c], "神田").map((s) => s.id)).toEqual(["c"]);
  });
  it("matches English name case-insensitively", () => {
    expect(filterStations([a, b, c], "aki").map((s) => s.id)).toEqual(["a"]);
  });
  it("returns all for blank query", () => {
    expect(filterStations([a, b, c], "  ")).toHaveLength(3);
  });
});

describe("rankByScore", () => {
  it("returns top N by score, excluding null", () => {
    expect(rankByScore([a, b, c], 2).map((s) => s.id)).toEqual(["b", "a"]);
  });
});

describe("getDominantFeature", () => {
  it("returns the highest percentile feature", () => {
    const s = makeStation({ id: "s", normalized: { tourism: 10, culture: 80, publicFacility: 20, park: 30, library: 0, stationUsage: 40 } });
    expect(getDominantFeature(s)).toBe("culture");
  });
  it("breaks ties by feature order", () => {
    const s = makeStation({ id: "s", normalized: { tourism: 50, culture: 50, publicFacility: 50, park: 50, library: 50, stationUsage: 50 } });
    expect(getDominantFeature(s)).toBe("tourism");
  });
  it("ignores missing and returns null when all missing", () => {
    const s = makeStation({ id: "s", normalized: { tourism: null, culture: null, publicFacility: null, park: null, library: null, stationUsage: null } });
    expect(getDominantFeature(s)).toBeNull();
  });
});

describe("getFeatureBreakdown", () => {
  it("returns one row per feature with weight and contribution", () => {
    const rows = getFeatureBreakdown(a, { tourismLow: 0.25, cultureLow: 0.2, publicFacilityLow: 0.15, parkLow: 0.1, libraryLow: 0.1, stationUsageLow: 0.2 });
    expect(rows).toHaveLength(6);
    const tourism = rows[0];
    expect(tourism.key).toBe("tourism");
    expect(tourism.weight).toBe(0.25);
    expect(tourism.low).toBe(50);
    // contribution = weight * low / sum(available weights) = 0.25 * 50 / 1
    expect(tourism.contribution).toBeCloseTo(12.5);
  });

  it("marks missing features and renormalizes contribution", () => {
    const s = makeStation({
      id: "m",
      raw: { ...a.raw, library: null },
      normalized: { ...a.normalized, library: null },
      scores: { ...a.scores, libraryLow: null, coverage: 0.9 },
    });
    const rows = getFeatureBreakdown(s, { tourismLow: 0.25, cultureLow: 0.2, publicFacilityLow: 0.15, parkLow: 0.1, libraryLow: 0.1, stationUsageLow: 0.2 });
    const library = rows.find((r) => r.key === "library")!;
    expect(library.missing).toBe(true);
    expect(library.contribution).toBeNull();
    const total = rows.reduce((sum, r) => sum + (r.contribution ?? 0), 0);
    expect(total).toBeCloseTo(50);
  });
});

describe("effective weights in the breakdown", () => {
  it("redistributes the weight of a missing feature", () => {
    const s = makeStation({
      id: "m",
      raw: { ...a.raw, tourism: null },
      normalized: { ...a.normalized, tourism: null },
      scores: { ...a.scores, tourismLow: null, coverage: 0.75 },
    });
    const rows = getFeatureBreakdown(s, { tourismLow: 0.25, cultureLow: 0.2, publicFacilityLow: 0.15, parkLow: 0.1, libraryLow: 0.1, stationUsageLow: 0.2 });
    expect(rows[0].effectiveWeight).toBeNull();
    expect(rows[1].effectiveWeight).toBeCloseTo(0.2 / 0.75);
    expect(rows.reduce((t, r) => t + (r.effectiveWeight ?? 0), 0)).toBeCloseTo(1);
  });
});

describe("getMissingReasons", () => {
  it("names the municipalities without data, and flags not-comparable values", () => {
    const s = makeStation({
      id: "shibuya",
      raw: { ...a.raw, culture: null, tourism: 3 },
      normalized: { ...a.normalized, culture: null, tourism: null },
      evidence: {
        culture: {
          kind: "facilities",
          status: "incomplete",
          radiusMeters: 500,
          count: null,
          lowerBound: 0,
          municipalities: [
            { code: "13113", name: "渋谷区", coverage: "uncovered", unlocated: 0 },
            { code: "13104", name: "新宿区", coverage: "covered", unlocated: 0 },
          ],
          facilities: [],
        },
      },
    });
    expect(getMissingReasons(s)).toEqual([
      { key: "tourism", municipalities: [], notComparable: true },
      { key: "culture", municipalities: [{ name: "渋谷区", coverage: "uncovered" }], notComparable: false },
    ]);
  });
});

describe("formatRanking", () => {
  it("formats stable and unstable ranks", () => {
    expect(formatRanking({ rank: 1, of: 5, range: [1, 1] })).toEqual({ rank: "5 駅中 1 位", range: "1 位", stable: true });
    expect(formatRanking({ rank: 2, of: 5, range: [2, 3] }).range).toBe("2〜3 位");
  });
});

describe("getScoreBand", () => {
  it.each([
    [90, "large"],
    [67, "large"],
    [66.9, "medium"],
    [34, "medium"],
    [33.9, "small"],
    [null, "unknown"],
  ] as const)("%s -> %s", (score, band) => {
    expect(getScoreBand(score).key).toBe(band);
  });
});

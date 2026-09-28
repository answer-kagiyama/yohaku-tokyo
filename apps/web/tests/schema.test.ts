import { describe, expect, it } from "vitest";

import raw from "@/data/stations.json";
import { FEATURE_KEYS } from "@/domain/features";
import { parseStationsDataset } from "@/domain/schema";

describe("parseStationsDataset", () => {
  it("parses the bundled stations.json", () => {
    const data = parseStationsDataset(raw);
    expect(data.stations.length).toBeGreaterThanOrEqual(5);
    expect(data.radiusMeters).toBe(500);
    expect(data.isFixture).toBe(data.fixtureFeatures.length > 0);
  });

  it("keeps null (missing) distinct from 0 everywhere", () => {
    const data = parseStationsDataset(raw);
    for (const s of data.stations) {
      for (const k of FEATURE_KEYS) {
        // missing is never ranked; a real 0 is ranked unless the whole feature is not comparable
        if (s.raw[k] === null) expect(s.normalized[k]).toBeNull();
        const comparable = data.stations.filter((x) => x.raw[k] !== null).length >= 3;
        if (s.raw[k] !== null && comparable) expect(typeof s.normalized[k]).toBe("number");
      }
    }
  });

  it("has the same feature keys as the pipeline output", () => {
    const data = parseStationsDataset(raw);
    for (const s of data.stations) {
      expect(Object.keys(s.raw).sort()).toEqual([...FEATURE_KEYS].sort());
    }
  });

  it("evidence agrees with raw values (complete -> count, incomplete -> null)", () => {
    const data = parseStationsDataset(raw);
    for (const s of data.stations) {
      for (const k of FEATURE_KEYS) {
        const ev = s.evidence[k];
        if (!ev) continue;
        if (ev.status === "incomplete") expect(s.raw[k]).toBeNull();
        else expect(s.raw[k]).toBe(ev.count);
        if (ev.kind === "facilities" && ev.status === "complete") {
          expect(ev.facilities).toHaveLength(ev.count!);
          expect(ev.radiusMeters).toBe(data.radiusMeters);
        }
      }
    }
  });

  it("ranking and effective weights are consistent with scores", () => {
    const data = parseStationsDataset(raw);
    for (const s of data.stations) {
      if (s.scores.yohaku === null) continue;
      const r = s.ranking!;
      expect(r.range[0]).toBeLessThanOrEqual(r.rank);
      expect(r.range[1]).toBeGreaterThanOrEqual(r.rank);
      const ew = Object.values(s.effectiveWeights!).filter((v): v is number => v !== null);
      expect(ew.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 2);
    }
    const best = data.stations.find((s) => s.ranking?.rank === 1)!;
    expect(best.scores.yohaku).toBe(Math.max(...data.stations.map((s) => s.scores.yohaku ?? -1)));
  });

  it("real features carry opendata sources with URLs", () => {
    const data = parseStationsDataset(raw);
    for (const s of data.stations) {
      for (const src of s.sources.filter((x) => x.kind === "opendata")) expect(src.url).toMatch(/^https:\/\//);
      const real = FEATURE_KEYS.filter((k) => !data.fixtureFeatures.includes(k) && s.raw[k] !== null);
      for (const k of real) expect(s.sources.some((src) => src.features.includes(k))).toBe(true);
    }
  });

  it("rejects an unknown coordinate source in evidence", () => {
    const bad = structuredClone(raw) as { stations: { evidence: { park: { facilities: { coordSource: string }[] } } }[] };
    bad.stations[0].evidence.park.facilities[0].coordSource = "guess";
    expect(() => parseStationsDataset(bad)).toThrow();
  });

  it("rejects scores outside 0-100", () => {
    const bad = structuredClone(raw) as typeof raw;
    bad.stations[0].scores.yohaku = 120;
    expect(() => parseStationsDataset(bad)).toThrow();
  });

  it("rejects a station without sources", () => {
    const bad = structuredClone(raw) as { stations: { sources: unknown[] }[] };
    bad.stations[0].sources = [];
    expect(() => parseStationsDataset(bad)).toThrow();
  });

  it("rejects duplicate station ids", () => {
    const bad = structuredClone(raw) as { stations: unknown[] };
    bad.stations.push(bad.stations[0]);
    expect(() => parseStationsDataset(bad)).toThrow(/duplicate/);
  });
});

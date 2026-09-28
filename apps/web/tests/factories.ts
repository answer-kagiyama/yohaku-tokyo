import type { Station, StationsDataset } from "@/domain/schema";

export function makeStation(overrides: Partial<Station> & { id: string }): Station {
  return {
    name: overrides.id,
    nameEn: null,
    lat: 35.7,
    lng: 139.77,
    municipality: null,
    lines: [],
    raw: { tourism: 1, culture: 1, publicFacility: 1, park: 1, library: 1, stationUsage: 1 },
    normalized: { tourism: 50, culture: 50, publicFacility: 50, park: 50, library: 50, stationUsage: 50 },
    semantic: {},
    scores: {
      yohaku: 50,
      tourismLow: 50,
      cultureLow: 50,
      publicFacilityLow: 50,
      parkLow: 50,
      libraryLow: 50,
      stationUsageLow: 50,
      coverage: 1,
    },
    sources: [{ id: "fixture-sample", name: "テスト用サンプル値", organization: "YOHAKU TOKYO", url: null, license: "N/A", features: [], kind: "fixture" }],
    ...overrides,
    evidence: overrides.evidence ?? {},
    ranking: overrides.ranking ?? null,
  };
}

export function makeDataset(stations: Station[]): StationsDataset {
  return {
    generatedAt: "2026-09-27T00:00:00Z",
    radiusMeters: 500,
    isFixture: true,
    fixtureFeatures: [],
    scoring: {
      version: "0.1.0-mvp",
      method: "percentile-rank",
      weights: {
        tourismLow: 0.25,
        cultureLow: 0.2,
        publicFacilityLow: 0.15,
        parkLow: 0.1,
        libraryLow: 0.1,
        stationUsageLow: 0.2,
      },
    },
    stations,
  };
}

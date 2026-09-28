import { z } from "zod";

import { FEATURE_KEYS, type FeatureKey, type LowScoreKey } from "./features";

const percent = z.number().min(0).max(100);
const nullablePercent = percent.nullable();

const featureRecord = <T extends z.ZodType>(value: T) =>
  z.object(Object.fromEntries(FEATURE_KEYS.map((k) => [k, value])) as Record<FeatureKey, T>);

const lowRecord = Object.fromEntries(
  FEATURE_KEYS.map((k) => [`${k}Low`, nullablePercent]),
) as Record<LowScoreKey, typeof nullablePercent>;

const nullableShare = z.number().min(0).max(1).nullable();
const weightShareRecord = Object.fromEntries(
  FEATURE_KEYS.map((k) => [`${k}Low`, nullableShare]),
) as Record<LowScoreKey, typeof nullableShare>;

export const sourceSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  organization: z.string().nullable().optional(),
  url: z.string().url().nullable().optional(),
  license: z.string().nullable().optional(),
  features: z.array(z.enum(FEATURE_KEYS)).default([]),
  kind: z.enum(["fixture", "opendata", "api"]),
});

export const facilityEvidenceSchema = z.object({
  kind: z.literal("facilities"),
  status: z.enum(["complete", "incomplete"]),
  radiusMeters: z.number().positive(),
  count: z.number().int().nonnegative().nullable(),
  lowerBound: z.number().int().nonnegative(),
  municipalities: z.array(
    z.object({
      code: z.string(),
      name: z.string(),
      coverage: z.enum(["covered", "partial", "uncovered"]),
      unlocated: z.number().int().nonnegative().default(0),
    }),
  ),
  facilities: z.array(
    z.object({
      name: z.string(),
      distanceM: z.number().nonnegative(),
      coordSource: z.enum(["source", "geocode"]),
    }),
  ),
});

export const ridershipEvidenceSchema = z.object({
  kind: z.literal("ridership"),
  status: z.enum(["complete", "incomplete"]),
  count: z.number().int().nonnegative().nullable(),
  fiscalYear: z.number().int(),
  measure: z.string(),
  lines: z.array(z.object({ operator: z.string(), line: z.string(), annualThousands: z.number() })),
});

export const evidenceSchema = z.discriminatedUnion("kind", [facilityEvidenceSchema, ridershipEvidenceSchema]);

export const stationSchema = z.object({
  id: z.string().regex(/^[a-z0-9-]+$/),
  name: z.string().min(1),
  nameEn: z.string().nullable().default(null),
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
  municipality: z.string().nullable().default(null),
  lines: z.array(z.string()).default([]),
  raw: featureRecord(z.number().nonnegative().nullable()),
  normalized: featureRecord(nullablePercent),
  semantic: z.record(z.string(), z.unknown()),
  scores: z.object({
    yohaku: nullablePercent,
    ...lowRecord,
    coverage: z.number().min(0).max(1),
  }),
  sources: z.array(sourceSchema).min(1),
  /** Weights after redistributing unavailable features (ADR 0009). */
  effectiveWeights: z.object(weightShareRecord).optional(),
  /** Rank by YOHAKU SCORE and its range under ±50% weight changes (spec 0006). */
  ranking: z
    .object({
      rank: z.number().int().positive(),
      of: z.number().int().positive(),
      range: z.tuple([z.number().int().positive(), z.number().int().positive()]),
    })
    .nullable()
    .default(null),
  /** Real-data evidence per feature (spec 0004). Absent for fixture features. */
  evidence: z.partialRecord(z.enum(FEATURE_KEYS), evidenceSchema).default({}),
});

export const stationsDatasetSchema = z
  .object({
    generatedAt: z.string(),
    radiusMeters: z.number().positive(),
    isFixture: z.boolean().default(false),
    /** Features whose values are still fictional sample values. */
    fixtureFeatures: z.array(z.enum(FEATURE_KEYS)).default([]),
    scoring: z.object({
      version: z.string(),
      method: z.string(),
      weights: z.object(
        Object.fromEntries(FEATURE_KEYS.map((k) => [`${k}Low`, z.number().min(0)])) as Record<
          LowScoreKey,
          z.ZodNumber
        >,
      ),
    }),
    stations: z.array(stationSchema),
  })
  .superRefine((data, ctx) => {
    const seen = new Set<string>();
    for (const s of data.stations) {
      if (seen.has(s.id)) {
        ctx.addIssue({ code: "custom", message: `duplicate station id: ${s.id}` });
      }
      seen.add(s.id);
    }
  });

export type Source = z.infer<typeof sourceSchema>;
export type Evidence = z.infer<typeof evidenceSchema>;
export type FacilityEvidence = z.infer<typeof facilityEvidenceSchema>;
export type RidershipEvidence = z.infer<typeof ridershipEvidenceSchema>;
export type Station = z.infer<typeof stationSchema>;
export type StationsDataset = z.infer<typeof stationsDatasetSchema>;
export type Weights = StationsDataset["scoring"]["weights"];

/** Validates stations.json. Throws on schema mismatch so `next build` fails (ADR 0002). */
export function parseStationsDataset(input: unknown): StationsDataset {
  return stationsDatasetSchema.parse(input);
}

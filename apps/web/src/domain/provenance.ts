import { z } from "zod";

import { FEATURE_KEYS } from "./features";

const featureKey = z.enum(FEATURE_KEYS);

export const provenanceSchema = z.object({
  generatedAt: z.string(),
  catalog: z.string().nullable(),
  features: z.array(
    z.object({
      key: featureKey,
      candidates: z.number().int().nonnegative(),
      accepted: z.number().int().nonnegative(),
      review: z.number().int().nonnegative(),
      rejected: z.number().int().nonnegative(),
    }),
  ),
  datasets: z.array(
    z.object({
      feature: featureKey,
      datasetId: z.string(),
      name: z.string(),
      organization: z.string().nullable(),
      license: z.string().nullable(),
      sourceUrl: z.string().url(),
      status: z.literal("accepted"),
      autoStatus: z.enum(["accepted", "review", "rejected"]),
      reviewNote: z.string().nullable(),
      reason: z.string().nullable(),
      ingest: z
        .object({
          status: z.enum(["ok", "degraded", "failed", "out-of-scope", "no-matching-rows"]),
          retrievedAt: z.string().nullable().optional(),
          rows: z.number().int().nullable().optional(),
          located: z.number().int(),
          unlocated: z.number().int().nullable().optional(),
          excluded: z.number().int().nullable().optional(),
          error: z.string().nullable().optional(),
        })
        .nullable(),
    }),
  ),
  services: z.array(z.object({ name: z.string(), use: z.string(), url: z.string().url() })),
});

export type Provenance = z.infer<typeof provenanceSchema>;
export type ProvenanceDataset = Provenance["datasets"][number];

export function parseProvenance(input: unknown): Provenance {
  return provenanceSchema.parse(input);
}

export const INGEST_STATUS_LABEL = {
  ok: "取得済み",
  degraded: "位置不明が多い",
  failed: "取得失敗",
  "out-of-scope": "位置変換の対象外",
  "no-matching-rows": "該当する施設なし",
} as const;

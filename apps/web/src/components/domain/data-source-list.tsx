import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { FEATURE_META } from "@/domain/features";
import type { Source } from "@/domain/schema";

const KIND_LABEL: Record<Source["kind"], string> = {
  fixture: "サンプル",
  opendata: "オープンデータ",
  api: "API",
};

/** Sources as numbered footnotes. Provenance must always be visible. */
export function DataSourceList({ sources }: { sources: Source[] }) {
  return (
    <ol className="divide-y divide-rule border-y border-rule">
      {sources.map((src, i) => (
        <li key={src.id} className="grid grid-cols-[2rem_1fr] gap-x-2 py-3">
          <span className="tnum text-label text-ink-faint">[{i + 1}]</span>
          <div className="min-w-0 space-y-1">
            <p className="flex flex-wrap items-center gap-2 text-label font-medium text-ink">
              {src.url ? (
                <a
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-0.5 underline decoration-rule-input underline-offset-4 hover:decoration-vermilion"
                >
                  {src.name}
                  <ArrowUpRight aria-hidden className="size-3.5" strokeWidth={1.5} />
                  <span className="sr-only">（新しいタブで開く）</span>
                </a>
              ) : (
                src.name
              )}
              <Badge variant={src.kind === "fixture" ? "destructive" : "outline"}>{KIND_LABEL[src.kind]}</Badge>
            </p>
            <p className="text-[0.75rem] text-ink-muted">
              {[src.organization, src.license && `ライセンス: ${src.license}`].filter(Boolean).join(" · ")}
              {!src.url && " · URL なし"}
            </p>
            <p className="text-[0.75rem] text-ink-faint">
              対象:{" "}
              {src.features.length > 0
                ? src.features.map((f) => FEATURE_META[f].label).join("・")
                : "駅の位置・路線"}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}

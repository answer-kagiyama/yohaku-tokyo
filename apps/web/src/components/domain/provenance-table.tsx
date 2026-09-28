import { ArrowUpRight } from "lucide-react";

import { INGEST_STATUS_LABEL, type ProvenanceDataset } from "@/domain/provenance";
import { cn } from "@/lib/utils";

const num = (v: number | null | undefined) => (v === null || v === undefined ? "—" : v.toLocaleString("ja-JP"));

/** Accepted datasets of one feature, as a register (spec 0007). */
export function ProvenanceTable({ datasets }: { datasets: ProvenanceDataset[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[44rem] border-y-2 border-rule-strong text-label">
        <thead className="bg-paper-sunken">
          <tr className="border-b border-rule-strong text-ink-muted">
            <th scope="col" className="px-3 py-2 text-left font-medium">組織</th>
            <th scope="col" className="px-3 py-2 text-left font-medium">データセット</th>
            <th scope="col" className="px-3 py-2 text-left font-medium">取得日</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">行数</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">位置あり</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">除外</th>
            <th scope="col" className="px-3 py-2 text-left font-medium">状態</th>
          </tr>
        </thead>
        <tbody>
          {datasets.map((d) => (
            <tr key={`${d.feature}-${d.datasetId}`} className="border-b border-rule align-top last:border-0">
              <td className="px-3 py-2.5 whitespace-nowrap text-ink-muted">{d.organization ?? "—"}</td>
              <td className="px-3 py-2.5">
                <a
                  href={d.sourceUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-0.5 text-ink underline decoration-rule-input underline-offset-4 hover:decoration-vermilion"
                >
                  {d.name}
                  <ArrowUpRight aria-hidden className="size-3.5" strokeWidth={1.5} />
                  <span className="sr-only">（新しいタブで開く）</span>
                </a>
                {d.autoStatus !== "accepted" && (
                  <p className="mt-0.5 text-[0.6875rem] text-vermilion">
                    人手で採用{d.reviewNote ? `: ${d.reviewNote}` : ""}
                  </p>
                )}
              </td>
              <td className="tnum px-3 py-2.5 whitespace-nowrap text-ink-muted">
                {d.ingest?.retrievedAt?.slice(0, 10) ?? "—"}
              </td>
              <td className="tnum px-3 py-2.5 text-right">{num(d.ingest?.rows)}</td>
              <td className="tnum px-3 py-2.5 text-right">{d.ingest ? num(d.ingest.located) : "—"}</td>
              <td className="tnum px-3 py-2.5 text-right text-ink-muted">{num(d.ingest?.excluded)}</td>
              <td
                className={cn(
                  "px-3 py-2.5 whitespace-nowrap",
                  d.ingest?.status === "failed" ? "text-vermilion" : "text-ink-muted",
                )}
              >
                {d.ingest ? INGEST_STATUS_LABEL[d.ingest.status] : "統計表（施設リスト以外）"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

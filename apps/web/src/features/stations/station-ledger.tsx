"use client";

import { ArrowDown, ArrowUp, ChevronRight, Search } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { ScoreMeter } from "@/components/domain/score-meter";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FEATURE_KEYS, FEATURE_META } from "@/domain/features";
import type { Station } from "@/domain/schema";
import {
  filterStations,
  formatObservationNo,
  formatScore,
  getDominantFeature,
  type SortKey,
  type SortState,
  sortStations,
} from "@/domain/stations";
import { cn } from "@/lib/utils";

const SORT_OPTIONS: { value: string; label: string; sort: SortState }[] = [
  { value: "yohaku-desc", label: "スコアが高い順", sort: { key: "yohaku", direction: "desc" } },
  { value: "yohaku-asc", label: "スコアが低い順", sort: { key: "yohaku", direction: "asc" } },
  { value: "name-asc", label: "駅名順", sort: { key: "name", direction: "asc" } },
  ...FEATURE_KEYS.map((k) => ({
    value: `${k}-desc`,
    label: `${FEATURE_META[k].label}が多い順`,
    sort: { key: k, direction: "desc" } as SortState,
  })),
];

type Props = {
  stations: Station[];
  /** Observation numbers keyed by station id (stable dataset order). */
  observationIndex: Record<string, number>;
};

export function StationLedger({ stations, observationIndex }: Props) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortState>({ key: "yohaku", direction: "desc" });

  const visible = useMemo(() => sortStations(filterStations(stations, query), sort), [stations, query, sort]);

  const toggleSort = (key: SortKey) =>
    setSort((prev) =>
      prev.key === key
        ? { key, direction: prev.direction === "desc" ? "asc" : "desc" }
        : { key, direction: key === "name" ? "asc" : "desc" },
    );

  const selectValue = `${sort.key}-${sort.direction}`;
  const hasSelectOption = SORT_OPTIONS.some((o) => o.value === selectValue);

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <label htmlFor="station-search" className="caption mb-1 block text-ink-faint">
            Search · 駅名で探す
          </label>
          <Search aria-hidden className="pointer-events-none absolute bottom-3.5 left-3 size-4 text-ink-faint" strokeWidth={1.5} />
          <Input
            id="station-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="例: 神田 / kanda"
            className="pl-9"
            autoComplete="off"
          />
        </div>
        <div className="w-full sm:w-auto lg:hidden">
          <span id="sort-label" className="caption mb-1 block text-ink-faint">
            Sort · 並べ替え
          </span>
          <Select
            value={hasSelectOption ? selectValue : undefined}
            onValueChange={(v) => {
              const opt = SORT_OPTIONS.find((o) => o.value === v);
              if (opt) setSort(opt.sort);
            }}
          >
            <SelectTrigger aria-labelledby="sort-label" className="w-full sm:w-56">
              <SelectValue placeholder="並べ替え" />
            </SelectTrigger>
            <SelectContent>
              {SORT_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <p className="caption mb-2 text-ink-faint" aria-live="polite">
        {visible.length} / {stations.length} stations · {stations.filter((s) => s.scores.yohaku !== null).length} scored
      </p>

      {visible.length === 0 ? (
        <p className="border-y-2 border-rule-strong py-10 text-center text-ink-muted">
          「{query}」に一致する駅はありません。
        </p>
      ) : (
        <>
          {/* Desktop: statistical table */}
          <div className="hidden overflow-x-auto lg:block">
            <table className="w-full border-y-2 border-rule-strong text-label">
              <caption className="sr-only">駅一覧。列見出しのボタンで並べ替えできます。</caption>
              <thead className="bg-paper-sunken">
                <tr className="border-b border-rule-strong text-ink-muted">
                  <th scope="col" className="w-20 px-3 py-2 text-left font-medium">No.</th>
                  <SortableHeader label="駅名" sortKey="name" sort={sort} onSort={toggleSort} align="left" />
                  <SortableHeader label="YOHAKU SCORE" sortKey="yohaku" sort={sort} onSort={toggleSort} align="left" />
                  <th scope="col" className="px-3 py-2 text-left font-medium whitespace-nowrap">目立つもの</th>
                  {FEATURE_KEYS.map((k) => (
                    <SortableHeader key={k} label={FEATURE_META[k].label} sortKey={k} sort={sort} onSort={toggleSort} align="right" />
                  ))}
                </tr>
              </thead>
              <tbody>
                {visible.map((s) => {
                  const dominant = getDominantFeature(s);
                  return (
                    <tr key={s.id} className="group relative border-b border-rule transition-colors duration-150 last:border-0 hover:bg-paper-sunken/70">
                      <td className="tnum px-3 py-3 text-ink-faint">{formatObservationNo(observationIndex[s.id])}</td>
                      <td className="px-3 py-3">
                        <Link
                          href={`/stations/${s.id}`}
                          className="font-display text-heading font-semibold text-ink after:absolute after:inset-0 group-hover:underline group-hover:underline-offset-4"
                        >
                          {s.name}
                        </Link>
                        <span className="caption ml-2 text-ink-faint">{s.nameEn}</span>
                      </td>
                      <td className="px-3 py-3">
                        <ScoreMeter score={s.scores.yohaku} />
                      </td>
                      <td className="px-3 py-3 text-ink-muted">{dominant ? FEATURE_META[dominant].label : "—"}</td>
                      {FEATURE_KEYS.map((k) => (
                        <td key={k} className={cn("tnum px-3 py-3 text-right", s.normalized[k] === null ? "text-ink-faint" : "text-ink")}>
                          {s.raw[k] === null ? "欠損" : s.normalized[k] === null ? "—" : Math.round(s.normalized[k])}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-2 text-[0.75rem] text-ink-faint">
              特徴量の列は percentile（0〜100、比較対象駅の中での多さ）。「欠損」はデータなし、「—」は値のある駅が少なく比較不能。
            </p>
          </div>

          {/* Mobile / tablet: ruled list */}
          <ol className="border-y-2 border-rule-strong lg:hidden">
            {visible.map((s) => {
              const dominant = getDominantFeature(s);
              return (
                <li key={s.id} className="border-b border-rule last:border-0">
                  <Link
                    href={`/stations/${s.id}`}
                    className="grid min-h-16 grid-cols-[1fr_auto_auto] items-center gap-x-3 py-3 transition-colors duration-150 active:bg-paper-sunken"
                  >
                    <span className="min-w-0">
                      <span className="tnum caption block text-ink-faint">{formatObservationNo(observationIndex[s.id])}</span>
                      <span className="font-display text-heading font-semibold text-ink">{s.name}</span>
                      <span className="block truncate text-[0.75rem] text-ink-muted">
                        {s.nameEn}
                        {dominant && ` · 目立つもの: ${FEATURE_META[dominant].label}`}
                      </span>
                    </span>
                    <span className="text-right">
                      <span className="tnum block text-title font-medium text-ink">{formatScore(s.scores.yohaku)}</span>
                      {s.scores.yohaku === null && <span className="block text-[0.6875rem] text-ink-faint">判定不能</span>}
                    </span>
                    <ChevronRight aria-hidden className="size-4 text-ink-faint" strokeWidth={1.5} />
                  </Link>
                </li>
              );
            })}
          </ol>
        </>
      )}
    </div>
  );
}

function SortableHeader({
  label,
  sortKey,
  sort,
  onSort,
  align,
}: {
  label: string;
  sortKey: SortKey;
  sort: SortState;
  onSort: (key: SortKey) => void;
  align: "left" | "right";
}) {
  const active = sort.key === sortKey;
  const Icon = sort.direction === "asc" ? ArrowUp : ArrowDown;
  return (
    <th
      scope="col"
      aria-sort={active ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}
      className={cn("px-1 py-1 font-medium", align === "right" ? "text-right" : "text-left")}
    >
      <button
        type="button"
        onClick={() => onSort(sortKey)}
        className={cn(
          "inline-flex h-8 items-center gap-1 rounded-sm px-2 whitespace-nowrap transition-colors duration-150 hover:text-ink",
          active && "text-ink",
        )}
      >
        {label}
        <Icon aria-hidden className={cn("size-3.5", active ? "opacity-100" : "opacity-0")} strokeWidth={1.5} />
      </button>
    </th>
  );
}

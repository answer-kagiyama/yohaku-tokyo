import type { Station } from "@/domain/schema";
import { formatRanking, formatScore, getScoreBand } from "@/domain/stations";
import { cn } from "@/lib/utils";

type Props = {
  score: number | null;
  coverage: number;
  ranking?: Station["ranking"];
  size?: "lg" | "md";
  className?: string;
};

/** The YOHAKU SCORE: the one place on a page where vermilion carries meaning. */
export function StationScore({ score, coverage, ranking = null, size = "lg", className }: Props) {
  const band = getScoreBand(score);
  return (
    <div className={cn("mb-4 space-y-1", className)}>
      <p className="caption text-ink-faint">Yohaku Score · 何もなさ指数</p>
      <p className="flex items-baseline gap-2">
        <span
          className={cn(
            "tnum font-medium tracking-tight",
            score === null ? "text-ink-faint" : "text-vermilion",
            size === "lg" ? "text-score md:text-[6rem]" : "text-[2.75rem] leading-none",
          )}
          aria-label={score === null ? "スコア判定不能" : `スコア ${formatScore(score)} / 100`}
        >
          {formatScore(score)}
        </span>
        <span aria-hidden className="tnum text-label text-ink-faint">
          / 100
        </span>
      </p>
      <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-label">
        <span className="border border-ink px-1.5 py-0.5 leading-none font-medium text-ink">{band.label}</span>
        {ranking && (
          <span className="text-ink">
            <span className="tnum">{formatRanking(ranking).rank}</span>
            <span className="ml-1 text-ink-muted">
              （重みを ±50% 変えると{" "}
              <span className="tnum">{formatRanking(ranking).range}</span>）
            </span>
          </span>
        )}
        {coverage < 1 && (
          <span className="text-ink-muted">
            データ充足率 <span className="tnum">{Math.round(coverage * 100)}%</span>（欠損を除いて算出）
          </span>
        )}
      </p>
    </div>
  );
}

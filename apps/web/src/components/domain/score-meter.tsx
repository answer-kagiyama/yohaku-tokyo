import { formatScore } from "@/domain/stations";
import { cn } from "@/lib/utils";

/** Compact score for lists: number + thin bar. */
export function ScoreMeter({ score }: { score: number | null }) {
  return (
    <div className="flex items-center gap-3">
      <span className="tnum w-10 text-right text-heading font-medium text-ink">{formatScore(score)}</span>
      {score === null && <span className="text-[0.75rem] text-ink-faint">判定不能</span>}
      <span
        aria-hidden
        className={cn("relative hidden h-1.5 w-24 rounded-sm bg-data-track sm:block", score === null && "sm:hidden")}
      >
        {score !== null && (
          <span className="absolute inset-y-0 left-0 rounded-sm bg-vermilion" style={{ width: `${score}%` }} />
        )}
      </span>
    </div>
  );
}

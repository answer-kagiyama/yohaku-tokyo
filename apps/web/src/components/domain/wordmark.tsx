import { cn } from "@/lib/utils";

/** Logotype: the wordmark with a small empty frame — the "margin" (余白) — marked in vermilion. */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 text-ink sm:gap-2.5", className)}>
      <span aria-hidden className="relative inline-block size-4 border border-ink">
        <span className="absolute right-0.5 bottom-0.5 size-1 bg-vermilion" />
      </span>
      <span className="tnum text-[0.875rem] font-semibold tracking-[0.14em] sm:text-[0.9375rem] sm:tracking-[0.22em]">
        YOHAKU<span className="ml-1 font-normal text-ink-muted sm:ml-1.5">TOKYO</span>
      </span>
    </span>
  );
}

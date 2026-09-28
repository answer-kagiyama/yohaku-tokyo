import Link from "next/link";

export default function NotFound() {
  return (
    <div className="page-container py-24">
      <p className="caption text-ink-faint">404 · Not found</p>
      <h1 className="mt-2 font-display text-title font-semibold text-ink">この駅の記録は見つかりませんでした。</h1>
      <p className="mt-6 text-label">
        <Link href="/stations" className="underline underline-offset-4 hover:text-vermilion">
          駅一覧へ戻る
        </Link>
      </p>
    </div>
  );
}

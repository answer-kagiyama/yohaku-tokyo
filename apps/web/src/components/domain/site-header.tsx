import Link from "next/link";

import { Wordmark } from "./wordmark";

const NAV = [
  { href: "/stations", label: "駅一覧" },
  { href: "/methodology", label: "算出方法" },
  { href: "/data", label: "データ" },
];

export function SiteHeader() {
  return (
    <header className="border-b border-rule-strong">
      <div className="page-container flex h-14 items-center justify-between gap-2">
        <Link href="/" aria-label="YOHAKU TOKYO ホーム" className="-mx-1 px-1 py-2">
          <Wordmark />
        </Link>
        <nav aria-label="メイン">
          <ul className="flex items-center text-label sm:gap-1">
            {NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="inline-flex h-11 items-center px-1.5 whitespace-nowrap text-ink-muted sm:px-2.5 underline-offset-[6px] transition-colors duration-150 hover:text-ink hover:underline"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}

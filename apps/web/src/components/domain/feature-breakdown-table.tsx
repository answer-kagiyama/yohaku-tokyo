import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FEATURE_META } from "@/domain/features";
import type { FeatureRow } from "@/domain/stations";
import { formatRaw } from "@/domain/stations";

const num = (v: number | null, digits = 1) => (v === null ? "—" : v.toFixed(digits));

/** raw → percentile → low → weight → contribution, as a statistical table. */
type Props = { rows: FeatureRow[]; score: number | null; sampleFeatures?: readonly string[] };

export function FeatureBreakdownTable({ rows, score, sampleFeatures = [] }: Props) {
  return (
    <Table>
      <TableCaption>
        percentile は比較対象駅の中での相対順位（0〜100）。少なさ = 100 − percentile。
        実効重み = 重み ÷ 値のある特徴量の重みの合計（値のない特徴量の重みは残りに再配分）。寄与 = 実効重み × 少なさ。
      </TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead scope="col">特徴量</TableHead>
          <TableHead scope="col" className="text-right">raw</TableHead>
          <TableHead scope="col" className="text-right">percentile</TableHead>
          <TableHead scope="col" className="text-right">少なさ</TableHead>
          <TableHead scope="col" className="text-right">重み</TableHead>
          <TableHead scope="col" className="text-right">実効重み</TableHead>
          <TableHead scope="col" className="text-right">寄与</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="tnum">
        {rows.map((r) => (
          <TableRow key={r.key}>
            <TableCell className="font-sans font-medium">
              {FEATURE_META[r.key].label}
              <span className="ml-1.5 text-[0.6875rem] text-ink-faint">{FEATURE_META[r.key].unit}</span>
              {sampleFeatures.includes(r.key) && (
                <span className="ml-1.5 text-[0.6875rem] text-ink-faint">（サンプル）</span>
              )}
            </TableCell>
            <TableCell className={r.missing ? "text-right text-vermilion" : "text-right"}>{formatRaw(r.raw)}</TableCell>
            <TableCell className="text-right">{num(r.percentile)}</TableCell>
            <TableCell className="text-right">{num(r.low)}</TableCell>
            <TableCell className="text-right text-ink-muted">{Math.round(r.weight * 100)}%</TableCell>
            <TableCell className="text-right">
              {r.effectiveWeight === null ? "—" : `${(r.effectiveWeight * 100).toFixed(1)}%`}
            </TableCell>
            <TableCell className="text-right">{num(r.contribution)}</TableCell>
          </TableRow>
        ))}
        <TableRow className="border-t-2 border-rule-strong hover:bg-transparent">
          <TableCell colSpan={6} className="font-sans font-medium">
            YOHAKU SCORE
          </TableCell>
          <TableCell className="text-right font-semibold text-vermilion">{num(score)}</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}

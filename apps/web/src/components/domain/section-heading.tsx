import { cn } from "@/lib/utils";

type Props = {
  caption: string;
  title: string;
  id?: string;
  as?: "h2" | "h3";
  className?: string;
  children?: React.ReactNode;
};

/** English caption + Japanese heading + heavy rule, like a section of a statistical report. */
export function SectionHeading({ caption, title, id, as: Tag = "h2", className, children }: Props) {
  return (
    <div className={cn("mb-6 border-b border-rule-strong pb-2", className)}>
      <p className="caption text-ink-faint">{caption}</p>
      <div className="flex items-end justify-between gap-4">
        <Tag id={id} className="font-display text-title font-semibold text-ink">
          {title}
        </Tag>
        {children}
      </div>
    </div>
  );
}

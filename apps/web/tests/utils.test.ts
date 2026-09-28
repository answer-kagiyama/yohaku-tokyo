import { describe, expect, it } from "vitest";

import { cn } from "@/lib/utils";

describe("cn", () => {
  it("keeps a type-scale token and a color token together", () => {
    expect(cn("text-label", "text-paper")).toBe("text-label text-paper");
    expect(cn("text-vermilion", "text-score")).toBe("text-vermilion text-score");
  });

  it("still merges conflicting sizes and colors", () => {
    expect(cn("text-label", "text-body")).toBe("text-body");
    expect(cn("text-ink", "text-vermilion")).toBe("text-vermilion");
  });
});

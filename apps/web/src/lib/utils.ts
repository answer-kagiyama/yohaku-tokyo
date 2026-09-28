import { createCn } from "cn/config"

/**
 * Class merger aware of the project's type-scale tokens (docs/design-system.md §3).
 * Without this, `text-label` (size) and `text-paper` (color) are treated as the same
 * group and one silently drops the other.
 */
export const cn = createCn({
  extend: {
    classGroups: {
      "font-size": [
        { text: ["score", "display", "title", "heading", "body", "label", "caption"] },
      ],
    },
  },
})

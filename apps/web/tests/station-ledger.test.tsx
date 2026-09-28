import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import raw from "@/data/stations.json";
import { parseStationsDataset } from "@/domain/schema";
import { StationLedger } from "@/features/stations/station-ledger";

const dataset = parseStationsDataset(raw);
const index = Object.fromEntries(dataset.stations.map((s, i) => [s.id, i]));

// The desktop table is the first table in the DOM; the mobile list mirrors it.
const tableStationNames = () =>
  within(screen.getByRole("table"))
    .getAllByRole("link")
    .map((a) => a.textContent);

describe("StationLedger", () => {
  it("lists all stations sorted by score descending by default", () => {
    render(<StationLedger stations={dataset.stations} observationIndex={index} />);
    const expected = [...dataset.stations]
      .sort((a, b) => (b.scores.yohaku ?? -1) - (a.scores.yohaku ?? -1))
      .map((s) => s.name);
    expect(tableStationNames()).toEqual(expected);
    const total = dataset.stations.length;
    const scored = dataset.stations.filter((s) => s.scores.yohaku !== null).length;
    expect(screen.getByText(`${total} / ${total} stations · ${scored} scored`)).toBeInTheDocument();
  });

  it("toggles sort direction from the column header", async () => {
    const user = userEvent.setup();
    render(<StationLedger stations={dataset.stations} observationIndex={index} />);
    const header = screen.getByRole("button", { name: /YOHAKU SCORE/ });
    await user.click(header);
    const lowest = [...dataset.stations].sort((a, b) => (a.scores.yohaku ?? 999) - (b.scores.yohaku ?? 999))[0];
    expect(tableStationNames()[0]).toBe(lowest.name);
    expect(header.closest("th")).toHaveAttribute("aria-sort", "ascending");
  });

  it("sorts by a feature", async () => {
    const user = userEvent.setup();
    render(<StationLedger stations={dataset.stations} observationIndex={index} />);
    await user.click(screen.getByRole("button", { name: /^文化/ }));
    const top = Math.max(...dataset.stations.map((s) => s.normalized.culture ?? -1));
    const first = dataset.stations.find((s) => s.name === tableStationNames()[0])!;
    expect(first.normalized.culture).toBe(top);
  });

  it("filters by English name", async () => {
    const user = userEvent.setup();
    render(<StationLedger stations={dataset.stations} observationIndex={index} />);
    await user.type(screen.getByLabelText(/駅名で探す/), "ueno");
    expect(tableStationNames()).toEqual(["上野"]);
    const total = dataset.stations.length;
    expect(screen.getByText(new RegExp(`^1 / ${total} stations`))).toBeInTheDocument();
  });

  it("shows an empty state", async () => {
    const user = userEvent.setup();
    render(<StationLedger stations={dataset.stations} observationIndex={index} />);
    await user.type(screen.getByLabelText(/駅名で探す/), "存在しない駅");
    expect(screen.getByText(/一致する駅はありません/)).toBeInTheDocument();
  });

  it("links each station to its detail page", () => {
    render(<StationLedger stations={dataset.stations} observationIndex={index} />);
    expect(within(screen.getByRole("table")).getByRole("link", { name: "上野" })).toHaveAttribute("href", "/stations/ueno");
  });

  it("shows missing values as 欠損 in the table", () => {
    render(<StationLedger stations={dataset.stations} observationIndex={index} />);
    const missing = dataset.stations.flatMap((s) => Object.values(s.raw)).filter((v) => v === null).length;
    expect(within(screen.getByRole("table")).queryAllByText("欠損")).toHaveLength(missing);
  });
});

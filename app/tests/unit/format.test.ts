import { describe, expect, it } from "vitest";
import {
  formatPercent,
  formatPeriod,
  formatRatio,
  parsePeriod,
} from "$lib/data/format";

describe("format helpers", () => {
  it("formats percentages", () => {
    expect(formatPercent(0.0325, 2)).toBe("3.25%");
  });

  it("formats ratios", () => {
    expect(formatRatio(6.92381, 2)).toBe("6.92");
  });

  it("formats periods", () => {
    expect(formatPeriod("2025Q4")).toBe("2025 Q4");
  });

  it("parses periods to quarter-midpoint dates", () => {
    expect(parsePeriod("2025Q4").toISOString()).toBe(
      "2025-12-15T00:00:00.000Z",
    );
  });
});

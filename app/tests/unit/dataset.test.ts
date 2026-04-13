import { describe, expect, it } from "vitest";
import { assertAligned, dataset } from "$lib/data/dataset";

describe("dataset alignment", () => {
  it("keeps the committed dataset aligned", () => {
    expect(assertAligned(dataset)).toBe(dataset);
  });

  it("throws on misalignment", () => {
    expect(() =>
      assertAligned({
        ...dataset,
        series: {
          ...dataset.series,
          fcf_yield: {
            ...dataset.series.fcf_yield,
            values: [0.1],
          },
        },
      }),
    ).toThrow(/does not align/);
  });
});

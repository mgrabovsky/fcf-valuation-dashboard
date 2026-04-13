import rawDataset from "../../../../data/v1/dataset.json";
import type { Dataset } from "$lib/types/dataset";

function assertAligned(dataset: Dataset): Dataset {
  if (!import.meta.env.DEV) {
    return dataset;
  }
  const expectedLength = dataset.periods.length;
  for (const [key, series] of Object.entries(dataset.series)) {
    if (series.values.length !== expectedLength) {
      throw new Error(`${key} does not align with periods.`);
    }
  }
  return dataset;
}

const dataset = assertAligned(rawDataset as Dataset);

export { assertAligned, dataset };

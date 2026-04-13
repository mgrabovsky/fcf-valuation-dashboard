export function formatPercent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatRatio(value: number, digits = 2): string {
  return value.toFixed(digits);
}

export function formatPeriod(period: string): string {
  return `${period.slice(0, 4)} ${period.slice(4)}`;
}

export function parsePeriod(period: string): Date {
  const year = Number.parseInt(period.slice(0, 4), 10);
  const quarter = Number.parseInt(period.slice(-1), 10);
  const month = quarter * 3 - 1;
  return new Date(Date.UTC(year, month, 15));
}

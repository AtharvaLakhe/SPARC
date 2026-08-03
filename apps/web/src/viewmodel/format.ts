/* Presentation-safe formatting.
 *
 * The single rule this file exists to enforce: **a missing measurement is never
 * rendered as a number.** `null` in a metric means the observation could not be
 * made — cloud, no common-valid coverage, failed gate — and printing it as "0"
 * or "—" without explanation converts an absence of evidence into an apparent
 * finding of no change. Every formatter here returns a discriminated result so
 * a component physically cannot print the number without handling the other
 * case. */

export type Formatted =
  | { kind: 'value'; text: string }
  | { kind: 'unavailable'; text: string; reason: string | null };

export const UNAVAILABLE_TEXT = 'Unavailable';

export function formatNumber(
  value: number | null,
  opts: { unit?: string; digits?: number; reason?: string | null; signed?: boolean } = {},
): Formatted {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return { kind: 'unavailable', text: UNAVAILABLE_TEXT, reason: opts.reason ?? null };
  }
  const digits = opts.digits ?? 2;
  const sign = opts.signed && value > 0 ? '+' : '';
  const num = value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return { kind: 'value', text: opts.unit ? `${sign}${num} ${unitLabel(opts.unit)}` : `${sign}${num}` };
}

export function formatPercent(
  value: number | null,
  opts: { reason?: string | null; signed?: boolean } = {},
): Formatted {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return { kind: 'unavailable', text: UNAVAILABLE_TEXT, reason: opts.reason ?? null };
  }
  const sign = opts.signed && value > 0 ? '+' : '';
  return { kind: 'value', text: `${sign}${value.toFixed(2)}%` };
}

/** km2 is stored machine-readable; render it as a unit a person reads. */
export function unitLabel(unit: string): string {
  if (unit === 'km2') return 'km²';
  if (unit === 'celsius') return '°C';
  return unit;
}

export function formatDateRange(startDate: string, endDate: string): string {
  return `${startDate} to ${endDate}`;
}

/** Direction words, deliberately neutral: the contract calls all three P0
 *  indicators `context-dependent`, so "improved"/"worsened" would be a claim
 *  the method does not support. */
export function changeWord(absoluteChange: number | null): string {
  if (absoluteChange === null || !Number.isFinite(absoluteChange)) return 'not comparable';
  if (Math.abs(absoluteChange) < 1e-9) return 'no measured change';
  return absoluteChange > 0 ? 'higher' : 'lower';
}

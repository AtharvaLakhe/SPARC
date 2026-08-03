/* One error taxonomy for both transports.
 *
 * Components must not branch on `instanceof TypeError` or read `response.status`
 * — that is how transport details leak into presentation. They branch on `kind`,
 * and every kind below has a designed, keyboard-reachable recovery state in
 * src/features/StateViews.tsx. Adding a kind without a view is a bug. */

import type { ProblemDetails } from '../contract/types';

export type DataErrorKind =
  | 'offline'          // browser reports no connectivity
  | 'unreachable'      // request never completed — API process down, CORS, DNS
  | 'not-found'        // no precomputed result for this selection
  | 'invalid-input'    // 400/422 — the selection itself is rejected
  | 'rate-limited'     // 429
  | 'upstream'         // 502/503 — dependency unavailable
  | 'server'           // 5xx
  | 'contract'         // response did not satisfy the frozen schema
  | 'cancelled';       // superseded by a newer request

export class DataError extends Error {
  readonly kind: DataErrorKind;
  readonly problem: ProblemDetails | null;
  readonly detail: string[];

  constructor(kind: DataErrorKind, message: string, opts: {
    problem?: ProblemDetails | null;
    detail?: string[];
  } = {}) {
    super(message);
    this.name = 'DataError';
    this.kind = kind;
    this.problem = opts.problem ?? null;
    this.detail = opts.detail ?? [];
  }
}

export function kindForStatus(status: number): DataErrorKind {
  if (status === 404 || status === 410) return 'not-found';
  if (status === 400 || status === 422 || status === 413) return 'invalid-input';
  if (status === 429) return 'rate-limited';
  if (status === 502 || status === 503) return 'upstream';
  if (status >= 500) return 'server';
  return 'server';
}

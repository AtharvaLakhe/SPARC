/* Shared presentation primitives.
 *
 * Two accessibility rules are enforced structurally here rather than left to
 * each screen to remember:
 *
 *  1. Status is never carried by colour alone. Every quality/status pill emits
 *     a text label; colour is redundant reinforcement. This is a WCAG 1.4.1
 *     requirement and it is also just how the thing stays readable printed,
 *     projected, or by anyone with a colour vision deficiency.
 *  2. An unavailable measurement renders as the word "Unavailable" plus its
 *     reason — never a dash, never a zero. `<Value>` takes the discriminated
 *     result from the formatters so it cannot be bypassed. */

import type { ReactNode } from 'react';
import type { QualityLevel, ResultStatus } from '../contract/types';
import type { Formatted } from '../viewmodel/format';

export function Value({ value }: { value: Formatted }) {
  if (value.kind === 'value') return <span className="value">{value.text}</span>;
  return (
    <span className="value value--unavailable">
      <abbr title={value.reason ?? 'No value was produced for this measurement.'}>
        {value.text}
      </abbr>
    </span>
  );
}

const QUALITY_TEXT: Record<QualityLevel, string> = {
  high: 'High quality',
  medium: 'Medium quality',
  low: 'Low quality',
  unknown: 'Quality unknown',
};

const QUALITY_SCORE: Record<QualityLevel, number> = {
  high: 3,
  medium: 2,
  low: 1,
  unknown: 0,
};

export function QualityPill({ level }: { level: QualityLevel }) {
  return (
    <span className={`pill pill--quality pill--${level}`}>
      <span aria-hidden="true" className="pill__glyph">
        {[0, 1, 2].map((index) => (
          <i key={index} className={index < QUALITY_SCORE[level] ? 'is-active' : undefined} />
        ))}
      </span>
      {QUALITY_TEXT[level]}
    </span>
  );
}

const STATUS_TEXT: Record<ResultStatus, string> = {
  complete: 'Complete',
  partial: 'Partial',
  unavailable: 'Unavailable',
  failed: 'Failed',
};

export function StatusPill({ status }: { status: ResultStatus }) {
  return <span className={`pill pill--status pill--${status}`}>{STATUS_TEXT[status]}</span>;
}

export function Callout({
  tone,
  title,
  children,
}: {
  tone: 'info' | 'warn' | 'stop';
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className={`callout callout--${tone}`} role={tone === 'stop' ? 'alert' : undefined}>
      <p className="callout__title">{title}</p>
      {children ? <div className="callout__body">{children}</div> : null}
    </div>
  );
}

/** Definition row used by the evidence and provenance tables. */
export function Row({ label, children, note }: { label: string; children: ReactNode; note?: string }) {
  return (
    <div className="row">
      <dt className="row__label">
        {label}
        {note ? <span className="row__note">{note}</span> : null}
      </dt>
      <dd className="row__value">{children}</dd>
    </div>
  );
}

export function VisuallyHidden({ children }: { children: ReactNode }) {
  return <span className="sr-only">{children}</span>;
}

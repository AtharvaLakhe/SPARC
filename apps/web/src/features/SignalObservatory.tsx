/* The primary comparison is presented as one explorable instrument instead of
 * four unrelated KPI cells. Baseline, comparison, and change remain the same
 * immutable values; the controls only change which reading is in focus. */

import { useState, type CSSProperties } from 'react';
import type { Formatted } from '../viewmodel/format';
import type { DetailView } from '../viewmodel/mapper';
import { styleFor } from '../indicators';
import { Callout, StatusPill, Value } from './Primitives';

type SignalMode = 'baseline' | 'comparison' | 'change';

function textOf(value: Formatted): string {
  return value.text;
}

function yearOf(range: string): string {
  return range.match(/\b\d{4}\b/)?.[0] ?? 'Period';
}

function widthFor(value: number | null, max: number): string {
  if (value === null || !Number.isFinite(value)) return '0%';
  return `${Math.max(4, (Math.abs(value) / max) * 100)}%`;
}

function modeReading(detail: DetailView, mode: SignalMode) {
  if (mode === 'baseline') {
    return {
      eyebrow: 'Baseline observation',
      value: detail.metric.baseline,
      supporting: detail.baseline.range,
      context: detail.baseline.sceneCount === null ? 'Scene count unavailable' : `${detail.baseline.sceneCount} source scenes`,
    };
  }
  if (mode === 'comparison') {
    return {
      eyebrow: 'Comparison observation',
      value: detail.metric.comparison,
      supporting: detail.comparison.range,
      context: detail.comparison.sceneCount === null ? 'Scene count unavailable' : `${detail.comparison.sceneCount} source scenes`,
    };
  }
  return {
    eyebrow: 'Estimated movement',
    value: detail.metric.absoluteChange,
    supporting: `${textOf(detail.metric.percentChange)} relative to baseline`,
    context: `Comparison is ${detail.metric.direction} than baseline`,
  };
}

export function SignalObservatory({ detail, id }: { detail: DetailView; id?: string }) {
  const [mode, setMode] = useState<SignalMode>(() =>
    detail.metric.changeUnavailable ? 'baseline' : 'change',
  );
  const accent = styleFor(detail.indicatorId).accent;
  const rawMax = Math.max(
    Math.abs(detail.metric.baselineRaw ?? 0),
    Math.abs(detail.metric.comparisonRaw ?? 0),
    1,
  );
  const baselineWidth = widthFor(detail.metric.baselineRaw, rawMax);
  const comparisonWidth = widthFor(detail.metric.comparisonRaw, rawMax);
  const reading = modeReading(detail, mode);
  const visualStyle = {
    '--signal-accent': accent,
    '--signal-baseline-width': baselineWidth,
    '--signal-comparison-width': comparisonWidth,
  } as CSSProperties;

  return (
    <section id={id} className="panel signal-observatory" aria-labelledby={`${id ?? 'signal'}-heading`} style={visualStyle}>
      <header className="signal-observatory__header">
        <div>
          <p className="signal-observatory__kicker">01 / comparison signal</p>
          <h2 id={`${id ?? 'signal'}-heading`}>{detail.indicatorName}</h2>
          <p className="signal-observatory__lede">{detail.proxyLabel}</p>
        </div>
        <StatusPill status={detail.status} />
      </header>

      {detail.partial || detail.status === 'partial' ? (
        <Callout tone="warn" title="Partial result">
          <p>
            At least one period did not meet its gate. Available observations are
            shown; missing observations remain explicitly unavailable.
          </p>
        </Callout>
      ) : null}

      <div className={`signal-observatory__stage signal-observatory__stage--${mode}`}>
        <p className="sr-only">
          Baseline {textOf(detail.metric.baseline)}. Comparison {textOf(detail.metric.comparison)}.
          Estimated change {textOf(detail.metric.absoluteChange)}, {textOf(detail.metric.percentChange)}.
        </p>

        <div className="signal-observatory__field" aria-hidden="true">
          <span className="signal-field__datum" />
          <span className="signal-field__trace signal-field__trace--baseline" />
          <span className="signal-field__trace signal-field__trace--comparison" />
        </div>

        <div className="signal-observatory__readout" aria-live="polite">
          <span>{reading.eyebrow}</span>
          <strong><Value value={reading.value} /></strong>
          <small>{reading.supporting}</small>
          <small>{reading.context}</small>
        </div>

        <div className="signal-observatory__planes" role="group" aria-label="Compare analysis periods">
          <button type="button"
            className={`signal-plane signal-plane--baseline${mode === 'baseline' ? ' is-active' : ''}`}
            aria-pressed={mode === 'baseline'} onClick={() => setMode('baseline')}>
            <span className="signal-plane__head">
              <b>Baseline / {yearOf(detail.baseline.range)}</b>
              <strong><Value value={detail.metric.baseline} /></strong>
            </span>
            <span className="signal-plane__track" aria-hidden="true">
              <i style={{ '--plane-width': baselineWidth } as CSSProperties} />
            </span>
            <small>{detail.baseline.sceneCount === null ? 'Scene count unavailable' : `${detail.baseline.sceneCount} source scenes`}</small>
          </button>

          <button type="button" className={`signal-observatory__delta${mode === 'change' ? ' is-active' : ''}`}
            aria-pressed={mode === 'change'} disabled={detail.metric.changeUnavailable}
            onClick={() => setMode('change')}>
            <span>Period movement</span>
            <strong><Value value={detail.metric.percentChange} /></strong>
            <i aria-hidden="true">{detail.metric.direction === 'lower' ? '↓' : detail.metric.direction === 'higher' ? '↑' : '→'}</i>
          </button>

          <button type="button"
            className={`signal-plane signal-plane--comparison${mode === 'comparison' ? ' is-active' : ''}`}
            aria-pressed={mode === 'comparison'} onClick={() => setMode('comparison')}>
            <span className="signal-plane__head">
              <b>Comparison / {yearOf(detail.comparison.range)}</b>
              <strong><Value value={detail.metric.comparison} /></strong>
            </span>
            <span className="signal-plane__track" aria-hidden="true">
              <i style={{ '--plane-width': comparisonWidth } as CSSProperties} />
            </span>
            <small>{detail.comparison.sceneCount === null ? 'Scene count unavailable' : `${detail.comparison.sceneCount} source scenes`}</small>
          </button>
        </div>

        <p className="signal-observatory__scale-note">
          Field length is relative to the larger period. Printed values are authoritative.
        </p>
      </div>

      {detail.metric.unavailableReason ? (
        <Callout tone="warn" title="Why a value is missing">
          <p>{detail.metric.unavailableReason}</p>
          <p>A missing value is not zero and does not mean “no change”.</p>
        </Callout>
      ) : null}
    </section>
  );
}

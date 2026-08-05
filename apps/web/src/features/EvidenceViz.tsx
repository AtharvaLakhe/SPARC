/* Interactive evidence field.
 *
 * The visuals below only encode values present in the comparison contract.
 * Coverage is a one-dimensional aggregate scale (explicitly not a map), scene
 * particles are one-for-one while counts fit the instrument, and sensitivity
 * is shown on labelled linear scales. No synthetic spatial texture is created. */

import { useId, useState, type CSSProperties } from 'react';
import type { Formatted } from '../viewmodel/format';
import type { DetailView } from '../viewmodel/mapper';
import { styleFor } from '../indicators';
import { Value } from './Primitives';

type DiagnosticMode = 'coverage' | 'inputs' | 'sensitivity';
type CoverageScale = 'full' | 'tail';
type SceneFocus = 'baseline' | 'comparison';
type SensitivityScale = 'detail' | 'full';

const MISSING_VALUE: Formatted = {
  kind: 'unavailable',
  text: 'Unavailable',
  reason: 'This evidence field was not supplied.',
};

const FIELD_LINES = Array.from({ length: 48 }, (_, index) => index);
const MAX_SCENE_MARKS = 240;

function valueFor(detail: DetailView, label: string): Formatted {
  return detail.quality.rows.find((row) => row.label === label)?.value ?? MISSING_VALUE;
}

function numberOf(value: Formatted): number | null {
  if (value.kind !== 'value') return null;
  const match = value.text.replaceAll(',', '').match(/[+-]?\d+(?:\.\d+)?/);
  if (!match) return null;
  const parsed = Number(match[0]);
  return Number.isFinite(parsed) ? parsed : null;
}

function clampPercent(value: number | null): number {
  return Math.min(100, Math.max(0, value ?? 0));
}

function CoverageDiagnostic({ detail }: { detail: DetailView }) {
  const commonValid = valueFor(detail, 'Common-valid coverage');
  const sceneCoverage = valueFor(detail, 'Scene coverage');
  const commonValidNumber = numberOf(commonValid);
  const [scale, setScale] = useState<CoverageScale>(() =>
    commonValidNumber !== null && commonValidNumber >= 99 ? 'tail' : 'full',
  );
  const notCommonValid = commonValidNumber === null ? null : Math.max(0, 100 - commonValidNumber);
  const fullPosition = clampPercent(commonValidNumber);
  const tailPosition = commonValidNumber === null
    ? 0
    : clampPercent((commonValidNumber - 99) * 100);
  const markerPosition = scale === 'tail' ? tailPosition : fullPosition;
  const fieldStyle = { '--field-marker': `${markerPosition}%` } as CSSProperties;

  return (
    <article className="diagnostic diagnostic--coverage">
      <header className="diagnostic__head">
        <div>
          <p className="diagnostic__eyebrow">Common observation footprint</p>
          <h4>Where does the comparison have support?</h4>
          <p className="diagnostic__lead">
            This is an aggregate district scale, not a pixel map. The illuminated
            field ends exactly at the reported common-valid percentage.
          </p>
        </div>
        <div className="diagnostic__scale-switch" role="group" aria-label="Coverage scale">
          <button type="button" className={scale === 'full' ? 'is-active' : undefined}
            aria-pressed={scale === 'full'} onClick={() => setScale('full')}>
            0—100%
          </button>
          <button type="button" className={scale === 'tail' ? 'is-active' : undefined}
            aria-pressed={scale === 'tail'} disabled={commonValidNumber === null}
            onClick={() => setScale('tail')}>
            Inspect last 1%
          </button>
        </div>
      </header>

      <div className={`coverage-field coverage-field--${scale}`} style={fieldStyle}>
        <div className="coverage-field__axis" aria-hidden="true">
          {scale === 'tail' ? <><span>99.00</span><span>99.50</span><span>100.00%</span></>
            : <><span>0</span><span>50</span><span>100%</span></>}
        </div>
        <div
          className="coverage-field__plot"
          role="img"
          aria-label={scale === 'tail'
            ? `Last one percent magnified. Common-valid coverage is ${commonValid.text}.`
            : `Full zero to one hundred percent scale. Common-valid coverage is ${commonValid.text}.`}
        >
          <span className="coverage-field__valid" aria-hidden="true" />
          <span className="coverage-field__unknown" aria-hidden="true" />
          <span className="coverage-field__marker" aria-hidden="true">
            <b>{commonValid.text}</b>
          </span>
          <span className="coverage-field__scan" aria-hidden="true" />
        </div>
        <p className="coverage-field__caption">
          {scale === 'tail'
            ? 'Last 1% magnified ×100. The underlying remainder is not enlarged in the reported value.'
            : 'Full district aggregate. The unobserved tail is intentionally almost invisible at this scale.'}
        </p>
      </div>

      <dl className="diagnostic__readouts">
        <div><dt>Valid in both periods</dt><dd><Value value={commonValid} /></dd></div>
        <div><dt>Scene coverage</dt><dd><Value value={sceneCoverage} /></dd></div>
        <div><dt>Not common-valid</dt><dd>{notCommonValid === null ? 'Unavailable' : `${notCommonValid.toFixed(2)}%`}</dd></div>
      </dl>
      <p className="diagnostic__truth">
        Cloud is a separate input diagnostic. The remainder here is unknown,
        never evidence of “no change”.
      </p>
    </article>
  );
}

function SceneSwarm({
  label,
  count,
  active,
  onSelect,
  comparison = false,
}: {
  label: string;
  count: number | null;
  active: boolean;
  onSelect: () => void;
  comparison?: boolean;
}) {
  const markCount = Math.min(MAX_SCENE_MARKS, Math.max(0, Math.round(count ?? 0)));
  return (
    <button
      type="button"
      className={`scene-swarm${active ? ' is-active' : ''}${comparison ? ' scene-swarm--comparison' : ''}`}
      aria-pressed={active}
      aria-label={`${label}: ${count === null ? 'scene count unavailable' : `${count} source scenes`}`}
      onClick={onSelect}
    >
      <span className="scene-swarm__label"><b>{label}</b><strong>{count ?? 'Unavailable'}</strong></span>
      <span className="scene-swarm__points" aria-hidden="true">
        {Array.from({ length: markCount }, (_, index) => (
          <i key={index} />
        ))}
      </span>
    </button>
  );
}

function InputsDiagnostic({ detail }: { detail: DetailView }) {
  const [focus, setFocus] = useState<SceneFocus>('comparison');
  const baseline = valueFor(detail, 'Scenes — baseline');
  const comparison = valueFor(detail, 'Scenes — comparison');
  const cloud = valueFor(detail, 'Cloud');
  const nodata = valueFor(detail, 'No data');
  const baselineNumber = numberOf(baseline);
  const comparisonNumber = numberOf(comparison);
  const oneMarkPerScene = Math.max(baselineNumber ?? 0, comparisonNumber ?? 0) <= MAX_SCENE_MARKS;
  const focusedPeriod = focus === 'baseline' ? detail.baseline : detail.comparison;
  const source = detail.provenance.sources[0];

  return (
    <article className="diagnostic diagnostic--inputs">
      <header className="diagnostic__head">
        <div>
          <p className="diagnostic__eyebrow">Source scene field</p>
          <h4>Two observation windows, exposed side by side.</h4>
          <p className="diagnostic__lead">
            Select either field to inspect its period. Cloud and no-data remain
            independent quality signals; they are not stacked into the scene count.
          </p>
        </div>
        <p className="diagnostic__source">
          <span>Primary source</span>
          <strong>{source?.mission ?? source?.provider ?? 'Unavailable'}</strong>
          <small>{source?.collection ?? 'Collection not supplied'}</small>
        </p>
      </header>

      <div className="scene-fields">
        <SceneSwarm label="Baseline" count={baselineNumber} active={focus === 'baseline'}
          onSelect={() => setFocus('baseline')} />
        <SceneSwarm label="Comparison" count={comparisonNumber} active={focus === 'comparison'}
          comparison onSelect={() => setFocus('comparison')} />
      </div>

      <div className="scene-inspector" aria-live="polite">
        <span>{focus === 'baseline' ? 'Baseline window' : 'Comparison window'}</span>
        <strong>{focusedPeriod.range}</strong>
        <small>{focusedPeriod.compositeMethod ?? 'Composite method unavailable'}</small>
        <small>{oneMarkPerScene ? 'Each dash represents one source scene.' : `Fields are capped at ${MAX_SCENE_MARKS} marks; printed counts are authoritative.`}</small>
      </div>

      <dl className="diagnostic__readouts">
        <div><dt>Baseline scenes</dt><dd><Value value={baseline} /></dd></div>
        <div><dt>Comparison scenes</dt><dd><Value value={comparison} /></dd></div>
        <div><dt>Cloud diagnostic</dt><dd><Value value={cloud} /></dd></div>
        <div><dt>No-data diagnostic</dt><dd><Value value={nodata} /></dd></div>
      </dl>
    </article>
  );
}

function SensitivityDiagnostic({ detail }: { detail: DetailView }) {
  const sensitivity = valueFor(detail, 'Threshold sensitivity');
  const sensitivityNumber = numberOf(sensitivity);
  const [scale, setScale] = useState<SensitivityScale>(() =>
    sensitivityNumber !== null && sensitivityNumber <= 1 ? 'detail' : 'full',
  );
  const fullPosition = clampPercent(sensitivityNumber);
  const detailPosition = clampPercent((sensitivityNumber ?? 0) * 100);
  const markerPosition = scale === 'detail' ? detailPosition : fullPosition;
  const fieldStyle = { '--field-marker': `${markerPosition}%` } as CSSProperties;
  const reading = sensitivityNumber === null
    ? 'No threshold-movement value is available.'
    : sensitivityNumber < 1
      ? 'The reported result moves by less than one percentage point across the documented threshold range.'
      : `The reported result moves by ${sensitivityNumber.toFixed(2)} percentage points across the documented threshold range.`;

  return (
    <article className="diagnostic diagnostic--sensitivity">
      <header className="diagnostic__head">
        <div>
          <p className="diagnostic__eyebrow">Threshold response</p>
          <h4>How far does the answer move?</h4>
          <p className="diagnostic__lead">{reading} This is sensitivity, not real-world accuracy.</p>
        </div>
        <div className="diagnostic__scale-switch" role="group" aria-label="Sensitivity scale">
          <button type="button" className={scale === 'detail' ? 'is-active' : undefined}
            aria-pressed={scale === 'detail'} disabled={sensitivityNumber === null}
            onClick={() => setScale('detail')}>0—1% detail</button>
          <button type="button" className={scale === 'full' ? 'is-active' : undefined}
            aria-pressed={scale === 'full'} onClick={() => setScale('full')}>0—100%</button>
        </div>
      </header>

      <div className={`response-field response-field--${scale}`} style={fieldStyle}>
        <div className="response-field__lines" aria-hidden="true">
          {FIELD_LINES.map((line) => <i key={line} />)}
        </div>
        <div className="response-field__axis" aria-hidden="true">
          {scale === 'detail' ? <><span>0</span><span>0.5</span><span>1.0%</span></>
            : <><span>0</span><span>50</span><span>100%</span></>}
        </div>
        <div className="response-field__marker" role="img"
          aria-label={`Reported threshold sensitivity is ${sensitivity.text}`}>
          <span>Reported movement</span>
          <strong><Value value={sensitivity} /></strong>
        </div>
      </div>

      <p className="diagnostic__truth">
        The detail lens magnifies only the labelled 0–1% scale. No threshold
        curve is drawn because the package contains the reported movement, not
        the underlying response series.
      </p>
    </article>
  );
}

export function EvidenceViz({ detail, id }: { detail: DetailView; id?: string }) {
  const [mode, setMode] = useState<DiagnosticMode>('coverage');
  const panelId = useId();
  const accent = styleFor(detail.indicatorId).accent;
  const visualStyle = { '--signal-accent': accent } as CSSProperties;
  const commonValid = valueFor(detail, 'Common-valid coverage');
  const baselineScenes = valueFor(detail, 'Scenes — baseline');
  const comparisonScenes = valueFor(detail, 'Scenes — comparison');
  const sensitivity = valueFor(detail, 'Threshold sensitivity');

  return (
    <section id={id} className="panel evidence-studio" aria-labelledby={`${panelId}-heading`} style={visualStyle}>
      <header className="evidence-studio__header">
        <p className="detail-section__kicker">03 / evidence field</p>
        <h3 id={`${panelId}-heading`}>Read the signal from three angles.</h3>
        <p>
          Each lens reconfigures the instrument around the same immutable values.
          Use the in-view controls to inspect dense ranges without distorting them.
        </p>
      </header>

      <div className="evidence-studio__workspace">
        <div className="evidence-studio__controls" role="group" aria-label="Choose evidence lens">
          <button type="button" className={mode === 'coverage' ? 'is-active' : undefined}
            aria-pressed={mode === 'coverage'} onClick={() => setMode('coverage')}>
            <span>01</span><strong>Coverage</strong><small>{commonValid.text}</small>
          </button>
          <button type="button" className={mode === 'inputs' ? 'is-active' : undefined}
            aria-pressed={mode === 'inputs'} onClick={() => setMode('inputs')}>
            <span>02</span><strong>Inputs</strong><small>{baselineScenes.text} / {comparisonScenes.text}</small>
          </button>
          <button type="button" className={mode === 'sensitivity' ? 'is-active' : undefined}
            aria-pressed={mode === 'sensitivity'} onClick={() => setMode('sensitivity')}>
            <span>03</span><strong>Sensitivity</strong><small>{sensitivity.text}</small>
          </button>
        </div>

        <div className="evidence-studio__canvas" aria-live="polite">
          {mode === 'coverage' ? <CoverageDiagnostic detail={detail} /> : null}
          {mode === 'inputs' ? <InputsDiagnostic detail={detail} /> : null}
          {mode === 'sensitivity' ? <SensitivityDiagnostic detail={detail} /> : null}
        </div>
      </div>
    </section>
  );
}

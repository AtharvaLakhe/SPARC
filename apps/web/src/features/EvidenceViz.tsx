/* Evidence at a glance.
 *
 * The quality panel is a table of nine numbers, which is complete but not
 * graspable — the complaint it answers is "this looks clustered". These three
 * visuals sit above it and answer the questions a reader actually has first:
 * how much of the district was actually seen, how far the answer moves if you
 * move the threshold, and how big the change is against the baseline.
 *
 * None of them replaces a number. Every figure is still printed beside its
 * shape, and the table below is unchanged — this is a way in, not a substitute.
 */

import type { DetailView } from '../viewmodel/mapper';
import { styleFor } from '../indicators';

/** Observed / cloud / no-data as one stacked bar. */
function CoverageBar({ detail }: { detail: DetailView }) {
  const rows = detail.quality.rows;
  const num = (label: string): number | null => {
    const r = rows.find((x) => x.label === label);
    return r && r.value.kind === 'value' ? parseFloat(r.value.text) : null;
  };
  const valid = num('Common-valid coverage');
  const cloud = num('Cloud');
  const nodata = num('No data');
  if (valid === null) return null;
  const rest = Math.max(0, 100 - valid);
  const c = Math.min(cloud ?? 0, rest);
  const n = Math.min(nodata ?? 0, Math.max(0, rest - c));

  return (
    <div className="viz">
      <p className="viz__title">What was actually observed</p>
      <div className="viz__stack" role="img"
        aria-label={`${valid.toFixed(1)} percent observed validly in both periods, ${c.toFixed(1)} percent cloud, ${n.toFixed(1)} percent no data`}>
        <span className="viz__seg viz__seg--valid" style={{ width: `${valid}%` }} />
        <span className="viz__seg viz__seg--cloud" style={{ width: `${c}%` }} />
        <span className="viz__seg viz__seg--nodata" style={{ width: `${n}%` }} />
      </div>
      <ul className="viz__key">
        <li><i className="viz__dot viz__dot--valid" />Observed both periods <b>{valid.toFixed(1)}%</b></li>
        <li><i className="viz__dot viz__dot--cloud" />Cloud <b>{c.toFixed(1)}%</b></li>
        <li><i className="viz__dot viz__dot--nodata" />No data <b>{n.toFixed(1)}%</b></li>
      </ul>
      <p className="viz__note">
        The grey portion is <em>unknown</em>, not unchanged. Read the change value
        against how much of the district it actually covers.
      </p>
    </div>
  );
}

/** Baseline vs comparison, drawn to scale. */
function ChangeBars({ detail }: { detail: DetailView }) {
  const b = detail.metric.baselineRaw;
  const c = detail.metric.comparisonRaw;
  if (b === null || c === null) return null;
  const max = Math.max(Math.abs(b), Math.abs(c)) || 1;
  const accent = styleFor(detail.indicatorId).accent;

  return (
    <div className="viz">
      <p className="viz__title">Baseline against comparison</p>
      <div className="viz__pair">
        <span className="viz__ptag">was</span>
        <span className="viz__ptrack">
          <span className="viz__pfill viz__pfill--base" style={{ width: `${(Math.abs(b) / max) * 100}%` }} />
        </span>
        <span className="viz__pval">{b}</span>
      </div>
      <div className="viz__pair">
        <span className="viz__ptag">now</span>
        <span className="viz__ptrack">
          <span className="viz__pfill" style={{ width: `${(Math.abs(c) / max) * 100}%`, background: accent }} />
        </span>
        <span className="viz__pval">{c}</span>
      </div>
    </div>
  );
}

/** How far the answer moves when the threshold moves. */
function SensitivityBand({ detail }: { detail: DetailView }) {
  const row = detail.quality.rows.find((r) => r.label === 'Threshold sensitivity');
  if (!row || row.value.kind !== 'value') return null;
  const pct = parseFloat(row.value.text);
  const width = Math.min(100, Math.max(2, pct * 2));
  const heavy = pct > 15;

  return (
    <div className="viz">
      <p className="viz__title">How stable is this?</p>
      <div className="viz__sens" role="img"
        aria-label={`Result moves by ${pct.toFixed(1)} percent across the documented threshold range`}>
        <span className="viz__sensfill" style={{ width: `${width}%`, background: heavy ? '#ff8a8a' : '#7ee2b8' }} />
        <span className="viz__sensmark" />
      </div>
      <p className="viz__note">
        Moving the classification threshold across its documented range changes
        the result by <b>{pct.toFixed(1)}%</b>.{' '}
        {heavy
          ? 'That is a wide band — treat the direction as the finding, not the figure.'
          : 'The direction of change is stable across that range.'}
      </p>
    </div>
  );
}

export function EvidenceViz({ detail }: { detail: DetailView }) {
  return (
    <section className="panel viz-panel" aria-label="Evidence at a glance">
      <div className="viz-grid">
        <ChangeBars detail={detail} />
        <CoverageBar detail={detail} />
        <SensitivityBand detail={detail} />
      </div>
    </section>
  );
}

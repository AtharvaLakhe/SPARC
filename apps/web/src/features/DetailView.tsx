/* One indicator in full: metric, plain-language reading, quality evidence,
 * provenance, and the spatial layer.
 *
 * Order is deliberate. The interpretation comes before the evidence because a
 * non-specialist needs to know what the number means before they can judge it,
 * and the caveats sit *inside* the interpretation block rather than in a
 * footnote — a reading and its limits should not be separable by scrolling. */

import { useId, type CSSProperties } from 'react';
import { sdgLinksFor } from '../sdg';
import type { DetailView as DetailVM } from '../viewmodel/mapper';
import { QualityPanel, ProvenancePanel } from './Disclosure';
import { BoundaryProvenancePanel } from './BoundaryProvenance';
import { LayerView } from './LayerView';
import { EvidenceViz } from './EvidenceViz';
import { Choropleth } from './Choropleth';
import { styleFor } from '../indicators';
import { SignalObservatory } from './SignalObservatory';
import { Value } from './Primitives';

/* Which SDG target this proxy speaks to — and, just as prominently, the official
   indicator it is not. Stating the relevance without stating the limit is how a
   screening tool gets quoted as national reporting. */
function SdgPanel({ indicatorId }: { indicatorId: string }) {
  const id = useId();
  const links = sdgLinksFor(indicatorId);
  if (!links.length) return null;

  return (
    <section className="panel" aria-labelledby={id}>
      <h3 id={id}>SDG relevance</h3>
      {links.map((link) => (
        <article key={`${link.goal}-${link.target}`} className="sdg">
          <h4 className="sdg__head">
            <span className="pill pill--sdg">SDG {link.target}</span>
            {link.goalName} — {link.targetName}
          </h4>
          <p className="sdg__supports"><strong>Can support:</strong> {link.supports}</p>
          <p className="sdg__not"><strong>Is not:</strong> {link.notOfficial}</p>
        </article>
      ))}
    </section>
  );
}

export function DetailScreen({
  detail,
  onBack,
}: {
  detail: DetailVM;
  onBack: () => void;
}) {
  const indicatorLabel = detail.indicatorName.replace(/ — .*$/, '');
  const indicatorStyle = styleFor(detail.indicatorId);
  const signalSubject = indicatorStyle.short === 'Water'
    ? 'Surface-water signal'
    : `${indicatorStyle.short} signal`;
  const relativeMagnitude = detail.metric.percentChange.kind === 'value'
    ? detail.metric.percentChange.text.replace(/^[+\-−]/, '')
    : null;
  const finding = detail.metric.changeUnavailable
    ? `A defensible change estimate is not available for ${indicatorLabel}.`
    : detail.metric.direction === 'no measured change'
      ? `${signalSubject} shows no measured change from baseline.`
      : relativeMagnitude
        ? `${signalSubject} is ${relativeMagnitude} ${detail.metric.direction} than baseline.`
        : `${signalSubject} moved from ${detail.metric.baseline.text} to ${detail.metric.comparison.text}.`;
  const findingStyle = {
    '--finding-accent': indicatorStyle.accent,
  } as CSSProperties;

  return (
    <>
      {/* Sticky: the detail view is long, and a back control that scrolls away
          leaves the reader stranded at the bottom of a provenance table. */}
      <nav aria-label="Breadcrumb" className="crumb crumb--sticky">
        <button type="button" className="btn btn--back" onClick={onBack}>
          <span aria-hidden="true">←</span> Back to {detail.region.name.replace(/ — .*$/, '')}
        </button>
        <span className="crumb__here">{detail.indicatorName.replace(/ — .*$/, '')}</span>
      </nav>

      <section id="detail-signal" className="detail-finding" style={findingStyle} aria-labelledby="detail-finding-heading">
        <p className="detail-section__kicker">01 / principal finding</p>
        <div className="detail-finding__composition">
          <h1 id="detail-finding-heading">
            {finding}
          </h1>
          <dl className="detail-finding__telemetry">
            <div>
              <dt>Estimated change</dt>
              <dd><Value value={detail.metric.absoluteChange} /></dd>
            </div>
            <div>
              <dt>Relative movement</dt>
              <dd><Value value={detail.metric.percentChange} /></dd>
            </div>
          </dl>
        </div>
      </section>

      <SignalObservatory detail={detail} />

      <section id="detail-reading" className="panel detail-reading" aria-labelledby="detail-reading-heading">
        <p className="detail-section__kicker">02 / interpretation</p>
        <h3 id="detail-reading-heading">What this shows</h3>
        <p className="interp">{detail.interpretation.summary}</p>

        <h4>What it does not show</h4>
        <ul className="list list--warn">
          {detail.interpretation.caveats.map((c) => <li key={c}>{c}</li>)}
        </ul>

        {detail.interpretation.suggestedActions.length ? (
          <>
            <h4>Reasonable next steps</h4>
            <ul className="list">
              {detail.interpretation.suggestedActions.map((a) => <li key={a}>{a}</li>)}
            </ul>
          </>
        ) : null}

        <p className="rule">
          Interpretation rule <code>{detail.interpretation.ruleId}</code> —
          generated from the result, not written per district.
        </p>
      </section>

      <EvidenceViz detail={detail} id="detail-evidence" />
      <QualityPanel quality={detail.quality} id="detail-quality" />
      <SdgPanel indicatorId={detail.indicatorId} />
      <LayerView
        id="detail-spatial"
        detail={detail}
        syntheticLayers={detail.badge.grade === 'synthetic'}
        accent={styleFor(detail.indicatorId).accent}
      />
      {detail.badge.grade === 'published' ? (
        <Choropleth
          indicatorId={detail.indicatorId}
          centroid={detail.region.centroid}
          regionName={detail.region.name.replace(/ — .*$/, '')}
        />
      ) : null}
      <ProvenancePanel provenance={detail.provenance} />
      <BoundaryProvenancePanel />
    </>
  );
}

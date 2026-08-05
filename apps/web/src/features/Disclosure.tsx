/* Quality, provenance and limitation disclosure.
 *
 * The requirement is that data mode, mock/pre-publication state, coverage,
 * method, sources, attribution, warnings and the boundary disclaimer are all
 * "visible without opening developer tools". So none of this is behind a
 * console log or a tooltip, and the parts that qualify the result — the badge,
 * the proxy disclaimer, the boundary disclaimer — are not inside a collapsed
 * <details>. Only the long source inventory collapses, and it defaults open on
 * the detail screen where provenance is the point. */

import { useId } from 'react';
import type { Provenance } from '../contract/types';
import {
  BOUNDARY_DISCLAIMER,
  PROXY_DISCLAIMER,
  type ModeBadge,
  type QualityView,
} from '../viewmodel/mapper';
import { BoundaryAttributionLine } from './BoundaryProvenance';
import { Callout, QualityPill, Row, Value } from './Primitives';

/* Primary-screen estimate strip. Detailed source, method and quality fields
 * remain in the methodology/provenance panels rather than competing with the
 * headline estimate. */
export function ModeBanner({ badge }: { badge: ModeBadge; warnings: string[] }) {
  return (
    <div className={`prov prov--${badge.grade}`}>
      <span className="prov__dot" aria-hidden="true" />
      <span className="prov__grade">Satellite-derived estimate</span>
      <span className="prov__sep" aria-hidden="true">·</span>
      <span className="prov__src">Data source: {badge.transportLabel}</span>
      <span className="sr-only">{badge.detail}</span>
    </div>
  );
}

export function LimitationsPanel() {
  const id = useId();
  return (
    <section className="panel panel--limits" aria-labelledby={id}>
      <h3 id={id}>Limitations you must read before using these numbers</h3>
      <ul className="limits">
        <li>{PROXY_DISCLAIMER}</li>
        <li>{BOUNDARY_DISCLAIMER}</li>
        <li>
          A change in a proxy is not a cause. Vegetation indices move with crops,
          rainfall, irrigation and harvest timing; a built-up signal is confused
          by bare soil and construction; open water excludes volume, quality and
          groundwater.
        </li>
        <li>
          Pixels that were cloudy or invalid are <em>unknown</em>, not unchanged.
          Read common-valid coverage before reading the change value.
        </li>
        <li>
          Scope is district-only. No subdistrict boundary has passed its approval
          gate, so no child-region result is offered.
        </li>
      </ul>
      {/* Attribution sits inside the limitations block so it travels with any
          screenshot of the caveats — the two are needed together. */}
      <BoundaryAttributionLine />
    </section>
  );
}

export function QualityPanel({ quality }: { quality: QualityView }) {
  const id = useId();
  return (
    <section className="panel" aria-labelledby={id}>
      <h3 id={id}>Quality evidence</h3>

      <p className="panel__lede">
        <QualityPill level={quality.level} />
        <span className="panel__basis">
          Basis: {quality.basis} · Method {quality.methodVersion}
        </span>
      </p>

      {!quality.independentValidationComplete ? (
        <Callout tone="warn" title="No independent validation">
          <p>
            No independent reference labels have been applied to this result, so
            no accuracy figure can be quoted. A quality grade above “unknown”
            here reflects internal gates only — coverage, scene count and
            threshold behaviour — not measured correctness.
          </p>
        </Callout>
      ) : null}

      {quality.reasons.length ? (
        <>
          <h4>Why this grade</h4>
          <ul className="list">{quality.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
        </>
      ) : null}

      {quality.warnings.length ? (
        <>
          <h4>Warnings</h4>
          <ul className="list list--warn">{quality.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </>
      ) : null}

      <h4>Evidence</h4>
      <dl className="rows">
        {quality.rows.map((row) => (
          <Row key={row.label} label={row.label} note={row.note}>
            <Value value={row.value} />
          </Row>
        ))}
      </dl>
    </section>
  );
}

/* A long evidence list, kept complete but bounded.
 *
 * A real Sentinel-2 composite names every contributing granule — for a summer
 * window over a district straddling two tiles this runs to hundreds of ids, and
 * rendering them raw pushes citation, licence and catalogue link so far down
 * the page that the provenance block stops functioning as provenance.
 *
 * Dropping them is not an option: which scenes went in *is* the provenance. So
 * the count leads (that is the number a reader actually wants), a few are shown
 * for shape, and the remainder sit behind a disclosure that scrolls in its own
 * box rather than growing the page. */
function ScrollList({ items, noun, mono = false }: {
  items: string[]; noun: string; mono?: boolean;
}) {
  const PREVIEW = 4;
  const rest = items.length - PREVIEW;
  const Item = ({ v }: { v: string }) => (
    <li>{mono ? <code className="wrap">{v}</code> : v}</li>
  );

  return (
    <div className="scenes">
      <p className="scenes__count">
        {items.length.toLocaleString()} {noun}{items.length === 1 ? '' : 's'}
      </p>
      <ul className="list list--tight scenes__preview">
        {items.slice(0, PREVIEW).map((v) => <Item key={v} v={v} />)}
      </ul>
      {rest > 0 ? (
        <details className="scenes__more">
          <summary>Show the remaining {rest.toLocaleString()}</summary>
          <ul className="list list--tight scenes__all">
            {items.slice(PREVIEW).map((v) => <Item key={v} v={v} />)}
          </ul>
        </details>
      ) : null}
    </div>
  );
}

export function ProvenancePanel({ provenance }: { provenance: Provenance }) {
  const id = useId();
  return (
    <section className="panel" aria-labelledby={id}>
      <h3 id={id}>Provenance</h3>

      <dl className="rows">
        <Row label="Algorithm"><code>{provenance.algorithmId}</code> v{provenance.algorithmVersion}</Row>
        <Row label="Parameters hash"><code className="wrap">{provenance.parametersHash}</code></Row>
        <Row label="Analysis CRS">{provenance.analysisCrs}</Row>
        <Row
          label="Effective resolution"
          note="The thermal or spectral support can be coarser than the published grid."
        >
          {provenance.effectiveResolutionMeters === null
            ? 'Unavailable'
            : `${provenance.effectiveResolutionMeters} m`}
        </Row>
        <Row label="Generated">{provenance.generatedAt}</Row>
      </dl>

      <h4>Source observations</h4>
      {provenance.sources.map((source) => (
        <details key={source.datasetId} className="source" open>
          <summary>
            {source.provider}
            {source.mission ? ` · ${source.mission}` : ''}
          </summary>
          <dl className="rows">
            <Row label="Dataset"><code>{source.datasetId}</code></Row>
            {source.collection ? <Row label="Collection">{source.collection}</Row> : null}
            {source.processingBaseline ? (
              <Row label="Processing baseline">{source.processingBaseline}</Row>
            ) : null}
            <Row label="Scene items">
              <ScrollList items={source.itemIds} noun="scene" mono />
            </Row>
            {source.acquiredAt.length ? (
              <Row label="Acquired">
                <ScrollList items={source.acquiredAt} noun="acquisition" />
              </Row>
            ) : null}
            {source.assetKeys.length ? (
              <Row label="Bands / assets">{source.assetKeys.join(', ')}</Row>
            ) : null}
            <Row label="Citation">{source.citation}</Row>
            <Row label="Licence">{source.license}</Row>
            {source.sourceUrl ? (
              <Row label="Catalogue">
                <a href={source.sourceUrl} target="_blank" rel="noreferrer noopener" className="wrap">
                  {source.sourceUrl}
                </a>
              </Row>
            ) : null}
          </dl>
        </details>
      ))}
    </section>
  );
}

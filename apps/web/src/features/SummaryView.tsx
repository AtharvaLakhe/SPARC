/* District summary as an editorial observation report.
 *
 * The change is the finding, so it receives the strongest typographic weight.
 * Baseline and comparison remain adjacent as the audit trail, while status,
 * unavailable reasons, and caveats stay in the reading flow. Nothing in this
 * view derives a value that is not already present in the view model. */

import { useEffect, useId, useRef } from 'react';
import { styleFor } from '../indicators';
import { SDG_SCOPE_NOTE } from '../sdg';
import type { IndicatorCardView, PeriodView, SummaryView as SummaryVM } from '../viewmodel/mapper';
import { Value } from './Primitives';

const STATUS_LABELS: Record<IndicatorCardView['status'], string> = {
  complete: 'Complete',
  partial: 'Partial',
  unavailable: 'Unavailable',
  failed: 'Failed',
};

function PeriodBlock({ title, period }: { title: string; period: PeriodView }) {
  return (
    <article className="period" aria-label={`${title} observation period`}>
      <span className="period__node" aria-hidden="true" />
      <h3 className="period__title">{title}</h3>
      <p className="period__range">{period.range}</p>
      <dl className="period__meta">
        {period.seasonLabel ? (<><dt>Season</dt><dd>{period.seasonLabel}</dd></>) : null}
        {period.compositeMethod ? (<><dt>Composite</dt><dd>{period.compositeMethod}</dd></>) : null}
        <dt>Scenes</dt>
        <dd>{period.sceneCount === null ? 'Unavailable' : period.sceneCount}</dd>
      </dl>
    </article>
  );
}

function SignalReadout({
  card,
  index,
  onOpen,
  onPreview,
}: {
  card: IndicatorCardView;
  index: number;
  onOpen: (indicatorId: string) => void;
  onPreview: (indicatorId: string | null) => void;
}) {
  const headingId = useId();
  const style = styleFor(card.id);
  const sequence = String(index + 1).padStart(2, '0');

  return (
    <li className="readout" data-indicator-id={card.id} style={{ ['--accent' as string]: style.accent }}>
      <article aria-labelledby={headingId}>
        <header className="readout__header">
          <p className="readout__channel">Signal {sequence} / {style.short}</p>
          <span className={`readout__status readout__status--${card.status}`}>
            {STATUS_LABELS[card.status]}
          </span>
        </header>

        <div className="readout__main">
          <div className="readout__finding">
            <h3 id={headingId} className="readout__title">{card.name}</h3>
            <p className="readout__proxy">{card.proxyLabel}</p>

            {card.metric.changeUnavailable ? (
              <div className="readout__change readout__change--unavailable">
                <p className="readout__change-label">Reported change</p>
                <p className="readout__value"><Value value={card.metric.absoluteChange} /></p>
                <p className="readout__direction">No change value was produced.</p>
              </div>
            ) : (
              <div className="readout__change">
                <p className="readout__change-label">Reported change</p>
                <p className="readout__value"><Value value={card.metric.absoluteChange} /></p>
                <p className="readout__direction">
                  <Value value={card.metric.percentChange} />
                  <span> · {card.metric.direction} than baseline</span>
                </p>
              </div>
            )}
          </div>

          <dl className="readout__telemetry" aria-label={`${card.name} period comparison`}>
            <div>
              <dt>Baseline</dt>
              <dd><Value value={card.metric.baseline} /></dd>
            </div>
            <div>
              <dt>Comparison</dt>
              <dd><Value value={card.metric.comparison} /></dd>
            </div>
          </dl>
        </div>

        {card.metric.changeUnavailable && card.metric.unavailableReason ? (
          <p className="readout__note readout__note--reason">
            <span>Why unavailable</span>
            {card.metric.unavailableReason}
          </p>
        ) : null}
        {card.caveat ? (
          <p className="readout__note">
            <span>Interpret with care</span>
            {card.caveat}
          </p>
        ) : null}

        <span className="readout__action" aria-hidden="true">
          <span>Inspect evidence</span>
          <span className="readout__arrow" aria-hidden="true">↗</span>
        </span>
        <button
          type="button"
          className="readout__open"
          onClick={() => onOpen(card.id)}
          onPointerEnter={() => onPreview(card.id)}
          onPointerLeave={(event) => {
            if (event.currentTarget.ownerDocument.activeElement !== event.currentTarget) onPreview(null);
          }}
          onFocus={() => onPreview(card.id)}
          onBlur={() => onPreview(null)}
          aria-label={`Inspect evidence for ${card.name}`}
        >
          <span className="sr-only">Inspect evidence for {card.name}</span>
        </button>
      </article>
    </li>
  );
}

export function SummaryScreen({
  summary,
  onOpenIndicator,
  onPreviewIndicator,
  onReport,
}: {
  summary: SummaryVM;
  onOpenIndicator: (indicatorId: string) => void;
  onPreviewIndicator: (indicatorId: string | null) => void;
  onReport: () => void;
}) {
  const periodsId = useId();
  const indicatorsId = useId();
  const reportId = useId();
  const signalsRef = useRef<HTMLOListElement | null>(null);

  useEffect(() => {
    const list = signalsRef.current;
    const view = list?.ownerDocument.defaultView;
    if (!list || !view) return;

    const root = list.closest<HTMLElement>('.sparc-panel');
    let frame = 0;
    const update = () => {
      frame = 0;
      const rootRect = root?.getBoundingClientRect();
      const readingLine = (rootRect?.top ?? 0) + (rootRect?.height ?? view.innerHeight) * 0.44;
      const listRect = list.getBoundingClientRect();
      if (readingLine < listRect.top || readingLine > listRect.bottom) {
        onPreviewIndicator(null);
        return;
      }

      const rows = Array.from(list.querySelectorAll<HTMLElement>('[data-indicator-id]'));
      const active = rows.find((row) => {
        const rect = row.getBoundingClientRect();
        return rect.top <= readingLine && rect.bottom >= readingLine;
      });
      onPreviewIndicator(active?.dataset.indicatorId ?? null);
    };
    const schedule = () => {
      if (frame) return;
      frame = view.requestAnimationFrame(update);
    };

    update();
    (root ?? view).addEventListener('scroll', schedule, { passive: true });
    view.addEventListener('resize', schedule, { passive: true });
    return () => {
      (root ?? view).removeEventListener('scroll', schedule);
      view.removeEventListener('resize', schedule);
      if (frame) view.cancelAnimationFrame(frame);
      onPreviewIndicator(null);
    };
  }, [onPreviewIndicator, summary.indicators]);

  return (
    <>
      <section id="summary-overview" className="panel panel--mission-summary" aria-labelledby={periodsId}>
        <header className="panel__heading">
          <div>
            <p className="panel__kicker">Observation window</p>
            <h2 id={periodsId}>
              {summary.regionName}
              <span className="panel__sub"> · {summary.regionType}</span>
            </h2>
          </div>
          <span className="panel__index" aria-hidden="true">01</span>
        </header>
        <p className="panel__lede">
          Analysis period: same-season comparison between two fixed composite windows. Both
          windows use the same method, so the difference is not an artefact of
          changing how the measurement was made.
        </p>
        <div className="periods" aria-label="Connected baseline and comparison capture timeline">
          <PeriodBlock title="Baseline" period={summary.baseline} />
          <PeriodBlock title="Comparison" period={summary.comparison} />
        </div>
      </section>

      <section id="summary-signals" className="panel panel--signals" aria-labelledby={indicatorsId}>
        <header className="panel__heading">
          <div>
            <p className="panel__kicker">Earth surface signals</p>
            <h2 id={indicatorsId}>Observed change</h2>
          </div>
          <span className="panel__count">{summary.indicators.length} signals</span>
        </header>
        <p className="panel__lede">{SDG_SCOPE_NOTE}</p>
        <ol ref={signalsRef} className="cards">
          {summary.indicators.map((card, index) => (
            <SignalReadout
              key={card.id}
              card={card}
              index={index}
              onOpen={onOpenIndicator}
              onPreview={onPreviewIndicator}
            />
          ))}
        </ol>
      </section>

      <section id="summary-report" className="panel report-launch panel--report" aria-labelledby={reportId}>
        <div className="report-launch__copy">
          <p className="panel__kicker">Ground response</p>
          <h2 id={reportId}>Turn observation into action</h2>
          <p className="panel__lede">
            Create a neutral request for inspection using this analysis and your own observation.
          </p>
        </div>
        <button type="button" className="btn btn--primary" onClick={onReport}>
          <span>Start a report</span><span aria-hidden="true">↗</span>
        </button>
      </section>
    </>
  );
}

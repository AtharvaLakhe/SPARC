/* District summary and the three indicator cards.
 *
 * Each card is a button that opens the detail view. Cards state their own
 * status and quality in words, and a card whose change value is unavailable
 * says so where the number would have been — the one thing it must never do is
 * render a plausible zero. */

import { useId } from 'react';
import { sdgChips, SDG_SCOPE_NOTE } from '../sdg';
import type { IndicatorCardView, PeriodView, SummaryView as SummaryVM } from '../viewmodel/mapper';
import { QualityPill, StatusPill, Value } from './Primitives';

function PeriodBlock({ title, period }: { title: string; period: PeriodView }) {
  return (
    <div className="period">
      <h4 className="period__title">{title}</h4>
      <p className="period__range">{period.range}</p>
      <dl className="period__meta">
        {period.seasonLabel ? (
          <><dt>Season</dt><dd>{period.seasonLabel}</dd></>
        ) : null}
        {period.compositeMethod ? (
          <><dt>Composite</dt><dd>{period.compositeMethod}</dd></>
        ) : null}
        <dt>Scenes</dt>
        <dd>{period.sceneCount === null ? 'Unavailable' : period.sceneCount}</dd>
      </dl>
    </div>
  );
}

function IndicatorCard({
  card,
  onOpen,
}: {
  card: IndicatorCardView;
  onOpen: (indicatorId: string) => void;
}) {
  const headingId = useId();
  return (
    <li className="card">
      <article aria-labelledby={headingId}>
        <header className="card__head">
          <h3 id={headingId} className="card__title">{card.name}</h3>
          <p className="card__proxy">{card.proxyLabel}</p>
          <p className="card__pills">
            {sdgChips(card.id).map((chip) => (
              <span key={chip} className="pill pill--sdg">{chip}</span>
            ))}
            <StatusPill status={card.status} />
            <QualityPill level={card.qualityLevel} />
          </p>
        </header>

        <dl className="card__metrics">
          <div>
            <dt>Baseline</dt>
            <dd><Value value={card.metric.baseline} /></dd>
          </div>
          <div>
            <dt>Comparison</dt>
            <dd><Value value={card.metric.comparison} /></dd>
          </div>
          <div className="card__change">
            <dt>Change</dt>
            <dd>
              <Value value={card.metric.absoluteChange} />
              {!card.metric.changeUnavailable ? (
                <span className="card__pct"><Value value={card.metric.percentChange} /></span>
              ) : null}
            </dd>
          </div>
        </dl>

        {card.metric.changeUnavailable && card.metric.unavailableReason ? (
          <p className="card__reason">{card.metric.unavailableReason}</p>
        ) : null}

        {card.caveat ? <p className="card__caveat">{card.caveat}</p> : null}

        <button type="button" className="btn btn--card" onClick={() => onOpen(card.id)}>
          Open evidence
          {/* Names the target so a screen-reader user hitting several identical
              buttons in a row knows which is which. */}
          <span className="sr-only"> for {card.name}</span>
        </button>
      </article>
    </li>
  );
}

export function SummaryScreen({
  summary,
  onOpenIndicator,
}: {
  summary: SummaryVM;
  onOpenIndicator: (indicatorId: string) => void;
}) {
  const periodsId = useId();
  const indicatorsId = useId();

  return (
    <>
      <section className="panel" aria-labelledby={periodsId}>
        <h2 id={periodsId}>
          {summary.regionName}
          <span className="panel__sub"> · {summary.regionType}</span>
        </h2>
        <p className="panel__lede">
          Same-season comparison between two fixed composite windows. Both
          windows use the same method, so the difference is not an artefact of
          changing how the measurement was made.
        </p>
        <div className="periods">
          <PeriodBlock title="Baseline" period={summary.baseline} />
          <PeriodBlock title="Comparison" period={summary.comparison} />
        </div>
      </section>

      <section className="panel" aria-labelledby={indicatorsId}>
        <h2 id={indicatorsId}>Indicators</h2>
        <p className="panel__lede">{SDG_SCOPE_NOTE}</p>
        <ul className="cards">
          {summary.indicators.map((card) => (
            <IndicatorCard key={card.id} card={card} onOpen={onOpenIndicator} />
          ))}
        </ul>
      </section>
    </>
  );
}

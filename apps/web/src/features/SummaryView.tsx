/* District summary and the three indicator cards.
 *
 * The card leads with the *change*, because that is the question the product
 * exists to answer — "is this district's water shrinking" is answered by the
 * delta, not by two absolute numbers the reader has to subtract themselves.
 * Baseline and comparison sit underneath as the working.
 *
 * The two bars are scaled against each other rather than a global range, and
 * they are decoration on top of numbers that are already printed: they make the
 * magnitude readable at a glance, they are not the only way to read it. When a
 * value is missing there is no bar at all — a bar drawn from a null is a
 * fabricated measurement. */

import { useId } from 'react';
import { barFractions, styleFor } from '../indicators';
import { sdgChips, SDG_SCOPE_NOTE } from '../sdg';
import type { IndicatorCardView, PeriodView, SummaryView as SummaryVM } from '../viewmodel/mapper';
import { QualityPill, StatusPill, Value } from './Primitives';

function PeriodBlock({ title, period }: { title: string; period: PeriodView }) {
  return (
    <div className="period">
      <h4 className="period__title">{title}</h4>
      <p className="period__range">{period.range}</p>
      <dl className="period__meta">
        {period.seasonLabel ? (<><dt>Season</dt><dd>{period.seasonLabel}</dd></>) : null}
        {period.compositeMethod ? (<><dt>Composite</dt><dd>{period.compositeMethod}</dd></>) : null}
        <dt>Scenes</dt>
        <dd>{period.sceneCount === null ? 'Unavailable' : period.sceneCount}</dd>
      </dl>
    </div>
  );
}

function CompareBars({ card, accent }: { card: IndicatorCardView; accent: string }) {
  const f = barFractions(card.metric.baselineRaw, card.metric.comparisonRaw);
  if (!f) return null;
  return (
    <div className="bars" aria-hidden="true">
      <div className="bars__row">
        <span className="bars__tag">was</span>
        <span className="bars__track">
          <span className="bars__fill bars__fill--base" style={{ width: `${f.baseline * 100}%` }} />
        </span>
      </div>
      <div className="bars__row">
        <span className="bars__tag">now</span>
        <span className="bars__track">
          <span
            className="bars__fill"
            style={{ width: `${f.comparison * 100}%`, background: accent }}
          />
        </span>
      </div>
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
  const style = styleFor(card.id);
  const rising = (card.metric.percentRaw ?? 0) > 0;

  return (
    <li className="card card2" style={{ ['--accent' as string]: style.accent }}>
      <article aria-labelledby={headingId}>
        <header className="card2__head">
          <span className="card2__glyph" aria-hidden="true">{style.glyph}</span>
          <div>
            <h3 id={headingId} className="card2__title">{card.name}</h3>
            <p className="card2__proxy">{card.proxyLabel}</p>
          </div>
        </header>

        <p className="card2__pills">
          {sdgChips(card.id).map((chip) => (
            <span key={chip} className="pill pill--sdg">{chip}</span>
          ))}
          <StatusPill status={card.status} />
          <QualityPill level={card.qualityLevel} />
        </p>

        {/* The headline. Direction is written in words as well as shown by the
            arrow, so it survives without colour and without the glyph. */}
        <div className="card2__hero">
          {card.metric.changeUnavailable ? (
            <p className="card2__nochange">
              <Value value={card.metric.absoluteChange} />
              <span className="card2__nochange-word">no change value</span>
            </p>
          ) : (
            <>
              <p className="card2__delta">
                <span className="card2__arrow" aria-hidden="true">{rising ? '▲' : '▼'}</span>
                <Value value={card.metric.absoluteChange} />
              </p>
              <p className="card2__pct">
                <Value value={card.metric.percentChange} />
                <span className="card2__word"> · {card.metric.direction} than baseline</span>
              </p>
            </>
          )}
        </div>

        <CompareBars card={card} accent={style.accent} />

        <dl className="card2__figures">
          <div>
            <dt>Baseline</dt>
            <dd><Value value={card.metric.baseline} /></dd>
          </div>
          <div>
            <dt>Comparison</dt>
            <dd><Value value={card.metric.comparison} /></dd>
          </div>
        </dl>

        {card.metric.changeUnavailable && card.metric.unavailableReason ? (
          <p className="card__reason">{card.metric.unavailableReason}</p>
        ) : null}
        {card.caveat ? <p className="card__caveat">{card.caveat}</p> : null}

        <button type="button" className="btn btn--card" onClick={() => onOpen(card.id)}>
          Open evidence
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

/* The two questions asked between the globe and the dashboard: where, and when.
 *
 * The honest bit is what happens when the answer is "nowhere we have data".
 * SPARC serves immutable precomputed packs, so most of the planet has nothing
 * behind it. Typing Paris must say so plainly and offer what does exist, rather
 * than silently snapping to the nearest district and presenting its numbers as
 * if they were the answer to the question asked. */

import { useEffect, useMemo, useRef, useState } from 'react';
import { findPlaces } from '@globe/places.js';
import { parseQuery } from '@globe/geo.js';
import type { RegionRef } from '../contract/types';
import { FROZEN_PERIODS, type FrozenPeriod } from '../config';
import { catalogRegions, cityForCoordinate } from '../catalog/cities';
import { CityPicker } from './CityPicker';

/** Great-circle distance in km. */
function haversineKm(aLat: number, aLon: number, bLat: number, bLon: number): number {
  const R = 6371;
  const dLat = ((bLat - aLat) * Math.PI) / 180;
  const dLon = ((bLon - aLon) * Math.PI) / 180;
  const s = Math.sin(dLat / 2) ** 2
    + Math.cos((aLat * Math.PI) / 180) * Math.cos((bLat * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

/** A district covers a point if the point falls inside its bounding box. */
function coveringRegion(regions: RegionRef[], lat: number, lon: number): RegionRef | null {
  return regions.find((r) => {
    const [w, s, e, n] = r.bbox;
    return lon >= w && lon <= e && lat >= s && lat <= n;
  }) ?? null;
}

export function LocationConsole({
  regions,
  regionsLoading,
  onResolved,
  onCancel,
  handoff,
  showDemoCities = false,
}: {
  regions: RegionRef[];
  regionsLoading: boolean;
  onResolved: (regionId: string) => void;
  onCancel: () => void;
  /** Coordinates the globe already collected, if the user arrived that way. */
  handoff?: { lat: number; lon: number; name: string } | null;
  /** Kept for compatibility; catalog quick targets are available in both modes. */
  showDemoCities?: boolean;
}) {
  const [query, setQuery] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [onCancel]);

  const catalog = catalogRegions();

  /* Arriving from the globe, the location question has already been answered —
     so answer it rather than asking again. The city catalogue is intentionally
     separate from published analytical districts: a catalog envelope can open
     report/export workflow, but it never upgrades itself to an analysis pack. */
  const consumed = useRef(false);
  useEffect(() => {
    if (!handoff || consumed.current) return;
    /* A catalog envelope can be resolved without the API list. A processed
       district cannot: wait for listRegions instead of consuming the handoff
       against an empty list and incorrectly reporting that nothing covers it. */
    if (regionsLoading && !cityForCoordinate(handoff.lat, handoff.lon)) return;
    consumed.current = true;
    setQuery(handoff.name);
    resolve(handoff.lat, handoff.lon, handoff.name);
    // resolve() is stable for this purpose; re-running on every render would
    // fight the user's own typing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handoff, regions, regionsLoading]);

  const suggestions = useMemo(
    () => (query.trim().length >= 2 ? findPlaces(query, 5) : []),
    [query],
  );

  function resolve(lat: number, lon: number, label: string) {
    const covering = coveringRegion(regions, lat, lon);
    if (covering) { onResolved(covering.id); return; }

    const city = cityForCoordinate(lat, lon);
    if (city) { onResolved(city.regionId); return; }

    const nearest = [...regions, ...catalog]
      .map((r) => ({ r, km: haversineKm(lat, lon, r.centroid[1], r.centroid[0]) }))
      .sort((a, b) => a.km - b.km)[0];

    setMessage(
      nearest
        ? `No published scope covers ${label}. The nearest catalog target is ${nearest.r.name}, about `
          + `${Math.round(nearest.km).toLocaleString()} km away. Pick a district below to continue.`
        : `No packaged result covers ${label}.`,
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const raw = query.trim();
    if (!raw) return;
    setMessage(null);

    const parsed = parseQuery(raw);
    if (parsed) { resolve(parsed.lat, parsed.lon, parsed.name); return; }
    setMessage(`Could not read "${raw}" as a place or a coordinate pair.`);
  }

  return (
    <div className="console-wrap" role="dialog" aria-modal="true" aria-labelledby="loc-h" aria-describedby="loc-desc">
      <div className="console console--location">
        <button type="button" className="console__close" onClick={onCancel} aria-label="Close">×</button>
        <header className="console__header">
          <div className="console__mission">
            <p className="console__step">01 / Locate</p>
            <div className="console__sequence" aria-hidden="true">
              <span className="is-active">Position</span>
              <span>Window</span>
            </div>
          </div>
          <h2 id="loc-h">Set an observation point</h2>
          <p className="console__lede" id="loc-desc">
            Search by place or enter latitude and longitude. The instrument only
            opens an analysis where a processed district or catalog scope exists.
          </p>
        </header>

        <form className="console__search" onSubmit={submit}>
          <span className="console__search-label" aria-hidden="true">Spatial query</span>
          <div className="console__field">
            <label htmlFor="place" className="sr-only">Place or coordinates</label>
            <span className="console__reticle" aria-hidden="true" />
            <input
              id="place"
              ref={inputRef}
              value={query}
              onChange={(e) => { setQuery(e.target.value); setMessage(null); }}
              placeholder="Nagpur  /  21.15, 79.08"
              autoComplete="off"
              spellCheck={false}
            />
            <button type="submit" className="console__submit">Resolve point <span aria-hidden="true">↗</span></button>
          </div>
        </form>

        {suggestions.length ? (
          <div className="console__suggestions">
            <p className="console__suggest-label">Matching coordinates</p>
            <ul className="console__suggest">
            {suggestions.map((p) => (
              <li key={`${p.name}-${p.lat}`}>
                <button type="button" onClick={() => resolve(p.lat, p.lon, p.name)}>
                  <span className="console__suggest-place">{p.name}, {p.country}</span>
                  <code>{p.lat.toFixed(2)}, {p.lon.toFixed(2)}</code>
                  <span className="console__suggest-go" aria-hidden="true">↗</span>
                </button>
              </li>
            ))}
            </ul>
          </div>
        ) : null}

        {message ? <p className="console__msg" role="status">{message}</p> : null}

        <div className="console__foot">
          {regionsLoading ? (
            <p className="console__note">Loading districts…</p>
          ) : regions.length === 0 ? (
            <p className="console__note" role="status">
              The processed-district index is unavailable. Catalog report/export targets remain below.
            </p>
          ) : null}
          <CityPicker
            onPick={onResolved}
            regions={regions}
            showDemoCities={showDemoCities}
          />
        </div>
      </div>
    </div>
  );
}

export function PeriodConsole({
  regionName,
  periods = FROZEN_PERIODS,
  onChosen,
  onBack,
}: {
  regionName: string;
  periods?: readonly FrozenPeriod[];
  onChosen: (period: FrozenPeriod) => void;
  onBack: () => void;
}) {
  const firstPeriodRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => { firstPeriodRef.current?.focus(); }, []);

  useEffect(() => {
    const backOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onBack();
    };
    window.addEventListener('keydown', backOnEscape);
    return () => window.removeEventListener('keydown', backOnEscape);
  }, [onBack]);

  return (
    <div className="console-wrap" role="dialog" aria-modal="true" aria-labelledby="per-h" aria-describedby="per-desc">
      <div className="console console--period">
        <button type="button" className="console__close" onClick={onBack} aria-label="Back">×</button>
        <header className="console__header">
          <div className="console__mission">
            <p className="console__step">02 / Observation window</p>
            <div className="console__sequence" aria-hidden="true">
              <span>Position</span>
              <span className="is-active">Window</span>
            </div>
          </div>
          <h2 id="per-h">Align two seasonal captures</h2>
          <p className="console__lede" id="per-desc">
            Choose a processed comparison for {regionName}. Each pair holds the
            season constant so the signal describes the ground, not the calendar.
          </p>
        </header>

        <ul className="period-list">
          {periods.map((p, index) => (
            <li key={p.id}>
              <button
                ref={index === 0 ? firstPeriodRef : undefined}
                type="button"
                className="period-card"
                onClick={() => onChosen(p)}
              >
                <span className="period-card__heading">
                  <span className="period-card__season">{p.seasonLabel}</span>
                  <span className="period-card__label">{p.label}</span>
                </span>
                <span className="period-card__track" aria-hidden="true">
                  <span className="period-card__node">{p.baselineStart.slice(0, 4)}</span>
                  <span className="period-card__line"><i /></span>
                  <span className="period-card__node period-card__node--comparison">{p.comparisonStart.slice(0, 4)}</span>
                </span>
                <span className="period-card__dates">
                  <span className="period-card__capture">
                    <span>Baseline capture</span>
                    <time dateTime={p.baselineStart}>{p.baselineStart}</time>
                    <span aria-hidden="true">—</span>
                    <time dateTime={p.baselineEnd}>{p.baselineEnd}</time>
                  </span>
                  <span className="period-card__capture period-card__capture--comparison">
                    <span>Comparison capture</span>
                    <time dateTime={p.comparisonStart}>{p.comparisonStart}</time>
                    <span aria-hidden="true">—</span>
                    <time dateTime={p.comparisonEnd}>{p.comparisonEnd}</time>
                  </span>
                </span>
                <span className="period-card__go">Open aligned analysis <span aria-hidden="true">→</span></span>
              </button>
            </li>
          ))}
        </ul>

        <details className="console__disclosure">
          <summary>Why are the windows fixed?</summary>
          <p>
            Other date ranges are not offered because nothing has been computed
            for them. SPARC resolves immutable precomputed results; it does not
            process imagery on request.
          </p>
        </details>
      </div>
    </div>
  );
}

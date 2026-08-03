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
  onResolved,
  onCancel,
  handoff,
}: {
  regions: RegionRef[];
  onResolved: (regionId: string) => void;
  onCancel: () => void;
  /** Coordinates the globe already collected, if the user arrived that way. */
  handoff?: { lat: number; lon: number; name: string } | null;
}) {
  const [query, setQuery] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  /* Arriving from the globe, the location question has already been answered —
     so answer it rather than asking again. If the target it picked has no
     packaged district, this falls through to the same honest refusal a typed
     query gets, with the console already open to fix it. */
  const consumed = useRef(false);
  useEffect(() => {
    if (!handoff || consumed.current || !regions.length) return;
    consumed.current = true;
    setQuery(handoff.name);
    resolve(handoff.lat, handoff.lon, handoff.name);
    // resolve() is stable for this purpose; re-running on every render would
    // fight the user's own typing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handoff, regions]);

  const suggestions = useMemo(
    () => (query.trim().length >= 2 ? findPlaces(query, 5) : []),
    [query],
  );

  function resolve(lat: number, lon: number, label: string) {
    const covering = coveringRegion(regions, lat, lon);
    if (covering) { onResolved(covering.id); return; }

    const nearest = regions
      .map((r) => ({ r, km: haversineKm(lat, lon, r.centroid[1], r.centroid[0]) }))
      .sort((a, b) => a.km - b.km)[0];

    setMessage(
      nearest
        ? `No packaged result covers ${label}. SPARC only serves districts that have been `
          + `processed and gated — the nearest is ${nearest.r.name}, about `
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
    <div className="console-wrap" role="dialog" aria-modal="true" aria-labelledby="loc-h">
      <div className="console">
        <button type="button" className="console__close" onClick={onCancel} aria-label="Close">×</button>
        <p className="console__step">Step 1 of 2</p>
        <h2 id="loc-h">Where do you want to look?</h2>
        <p className="console__lede">
          Type a place or a coordinate pair. SPARC will tell you whether a
          processed district covers it.
        </p>

        <form onSubmit={submit}>
          <div className="console__field">
            <label htmlFor="place" className="sr-only">Place or coordinates</label>
            <input
              id="place"
              ref={inputRef}
              value={query}
              onChange={(e) => { setQuery(e.target.value); setMessage(null); }}
              placeholder="Nagpur    ·    21.15, 79.08"
              autoComplete="off"
              spellCheck={false}
            />
            <button type="submit" className="cta cta--sm">Locate</button>
          </div>
        </form>

        {suggestions.length ? (
          <ul className="console__suggest">
            {suggestions.map((p) => (
              <li key={`${p.name}-${p.lat}`}>
                <button type="button" onClick={() => resolve(p.lat, p.lon, p.name)}>
                  <span>{p.name}, {p.country}</span>
                  <code>{p.lat.toFixed(2)}, {p.lon.toFixed(2)}</code>
                </button>
              </li>
            ))}
          </ul>
        ) : null}

        {message ? <p className="console__msg" role="status">{message}</p> : null}

        <div className="console__foot">
          <CityPicker
            onPick={onResolved}
            realRegion={regions.find((r) => r.id.includes('nagpur')) ?? regions[0] ?? null}
          />
        </div>
      </div>
    </div>
  );
}

export function PeriodConsole({
  regionName,
  onChosen,
  onBack,
}: {
  regionName: string;
  onChosen: (period: FrozenPeriod) => void;
  onBack: () => void;
}) {
  return (
    <div className="console-wrap" role="dialog" aria-modal="true" aria-labelledby="per-h">
      <div className="console">
        <button type="button" className="console__close" onClick={onBack} aria-label="Back">×</button>
        <p className="console__step">Step 2 of 2</p>
        <h2 id="per-h">Which two periods should we compare?</h2>
        <p className="console__lede">
          Both windows must cover the same season, or the difference measures the
          calendar rather than the ground. These are the windows with a processed
          composite behind them.
        </p>

        <ul className="period-list">
          {FROZEN_PERIODS.map((p) => (
            <li key={p.id}>
              <button type="button" className="period-card" onClick={() => onChosen(p)}>
                <span className="period-card__season">{p.seasonLabel}</span>
                <span className="period-card__label">{p.label}</span>
                <span className="period-card__dates">
                  <span>{p.baselineStart} → {p.baselineEnd}</span>
                  <span className="period-card__vs">compared with</span>
                  <span>{p.comparisonStart} → {p.comparisonEnd}</span>
                </span>
                <span className="period-card__go">Analyse {regionName} →</span>
              </button>
            </li>
          ))}
        </ul>

        <p className="console__note">
          Other date ranges are not offered because nothing has been computed for
          them. SPARC resolves immutable precomputed results; it does not process
          imagery on request.
        </p>
      </div>
    </div>
  );
}

/* National screening choropleth.
 *
 * ── EVERY VALUE HERE IS GENERATED ───────────────────────────────────────────
 * This is the "many districts at once" view — the thematic map that makes a
 * screening indicator useful, because the question it answers is comparative:
 * which regions moved, and which moved most.
 *
 * No region on this map has been processed. The values are deterministic
 * synthetic figures seeded from the region name, exactly like the demo cities,
 * and the panel says so above the map. When the real 735-district extraction
 * lands (region-scale-out.md Phase 0) this component swaps its data source and
 * nothing else changes.
 * ────────────────────────────────────────────────────────────────────────────
 *
 * Colour is a diverging ramp about zero, because the reader's first question is
 * direction, not magnitude — a sequential ramp would make "small increase" and
 * "small decrease" look like neighbours on a scale rather than opposites.
 */

import { useEffect, useId, useRef, useState } from 'react';
import { styleFor } from '../indicators';

const SRC = `${import.meta.env.BASE_URL}basemap/india-admin1.geojson`;

/** Deterministic per-region change, seeded from the name. */
function seeded(name: string, indicatorId: string): number {
  let h = 2166136261;
  for (const ch of `${name}|${indicatorId}`) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 16777619);
  }
  const u = ((h >>> 0) % 10000) / 10000;
  // Built-up trends up, vegetation and water drift both ways.
  const bias = indicatorId === 'built-up' ? 0.62 : 0.46;
  return Number(((u - bias) * 34).toFixed(1));
}

export function Choropleth({ indicatorId }: { indicatorId: string }) {
  const headingId = useId();
  const ref = useRef<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState(false);
  const accent = styleFor(indicatorId).accent;

  useEffect(() => {
    let disposed = false;
    let map: { remove: () => void } | null = null;

    (async () => {
      try {
        const maplibre = await import('maplibre-gl');
        const geo = await fetch(SRC).then((r) => r.json());
        if (disposed || !ref.current) return;

        for (const f of geo.features) {
          f.properties.change = seeded(f.properties.name, indicatorId);
        }

        const instance = new maplibre.Map({
          container: ref.current,
          style: { version: 8, sources: {}, layers: [
            { id: 'bg', type: 'background', paint: { 'background-color': '#0a1420' } },
          ] },
          bounds: [67.5, 6.5, 97.5, 36.5],
          fitBoundsOptions: { padding: 12 },
          attributionControl: false,
          keyboard: false,
        });
        map = instance;

        instance.on('load', () => {
          if (disposed) return;
          instance.addSource('regions', { type: 'geojson', data: geo });
          instance.addLayer({
            id: 'regions-fill', type: 'fill', source: 'regions',
            paint: {
              // Diverging about zero: loss red, gain in the indicator's colour.
              'fill-color': [
                'interpolate', ['linear'], ['get', 'change'],
                -18, '#c2402f', -6, '#7a3a3a', 0, '#243244', 6, accent, 18, '#eaf6ff',
              ],
              'fill-opacity': 0.88,
            },
          });
          instance.addLayer({
            id: 'regions-line', type: 'line', source: 'regions',
            paint: { 'line-color': '#0a1420', 'line-width': 0.6 },
          });
        });
        instance.on('error', () => setFailed(true));
      } catch {
        if (!disposed) setFailed(true);
      }
    })();

    return () => { disposed = true; map?.remove(); };
  }, [indicatorId, accent]);

  return (
    <section className="panel" aria-labelledby={headingId}>
      <h3 id={headingId}>Regional screening view</h3>
      <p className="choro__warn">
        <strong>Generated values.</strong> No region on this map has been
        processed. This shows how a screening indicator reads at scale — the
        comparison between regions is the point, and every figure behind it is
        synthetic.
      </p>
      {failed ? (
        <p className="hint">The regional view could not be drawn. The district result above is unaffected.</p>
      ) : (
        <div ref={ref} className="choro__map" role="img"
          aria-label={`Generated ${indicatorId} change across Indian regions, shown as a coloured map. Values are synthetic.`} />
      )}
      <div className="choro__legend" aria-hidden="true">
        <span>loss</span>
        <span className="choro__ramp" style={{
          background: `linear-gradient(90deg,#c2402f,#7a3a3a,#243244,${accent},#eaf6ff)`,
        }} />
        <span>gain</span>
      </div>
      <p className="hint">
        Boundaries: Natural Earth admin-1 (public domain), bundled offline. They
        are context for the demo, not the district geometry the indicators use.
      </p>
    </section>
  );
}

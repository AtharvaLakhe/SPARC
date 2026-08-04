/* Regional screening field.
 *
 * ── EVERY VALUE HERE IS GENERATED ───────────────────────────────────────────
 * No region on this map has been processed. Values are deterministic synthetic
 * figures seeded from the region name, and the panel says so above the map.
 * ────────────────────────────────────────────────────────────────────────────
 *
 * A continuous intensity field over 4,596 admin-1 regions worldwide, rather
 * than flat polygon fills. Two reasons, one a correctness fix and one a
 * modelling argument:
 *
 *  · The previous version drew a map of India for *every* district, including
 *    London and Tokyo. That was simply wrong. A world field centred on the
 *    selection cannot be wrong about which country you are looking at.
 *  · A screening indicator is a field. The useful signal is where change
 *    concentrates, not the precise value of one administrative unit — and
 *    hard-edged choropleth polygons imply each boundary is meaningful to the
 *    measurement, which at screening tier it is not.
 */

import { useEffect, useId, useRef, useState } from 'react';

const LAND = `${import.meta.env.BASE_URL}basemap/ne_110m_land.geojson`;
const CENTROIDS = `${import.meta.env.BASE_URL}basemap/world-admin1-centroids.geojson`;

/** Deterministic per-region magnitude, seeded from the region name. */
function seeded(name: string, indicatorId: string): number {
  let h = 2166136261;
  for (const ch of `${name}|${indicatorId}`) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}

export function Choropleth({
  indicatorId,
  centroid,
  regionName,
}: {
  indicatorId: string;
  centroid?: [number, number];
  regionName?: string;
}) {
  const headingId = useId();
  const ref = useRef<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let disposed = false;
    let map: { remove: () => void } | null = null;

    (async () => {
      try {
        const maplibre = await import('maplibre-gl');
        const points = await fetch(CENTROIDS).then((r) => r.json());
        if (disposed || !ref.current) return;

        for (const f of points.features) {
          f.properties.w = seeded(f.properties.name || f.properties.iso, indicatorId);
        }

        const instance = new maplibre.Map({
          container: ref.current,
          style: {
            version: 8,
            sources: {},
            layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#04070d' } }],
          },
          center: centroid ?? [79.08, 21.15],
          zoom: 2.4,
          attributionControl: false,
          keyboard: false,
        });
        map = instance;

        instance.on('load', () => {
          if (disposed) return;

          instance.addSource('land', { type: 'geojson', data: LAND });
          instance.addLayer({
            id: 'land',
            type: 'fill',
            source: 'land',
            paint: { 'fill-color': '#0d1b2c', 'fill-outline-color': '#22405e' },
          });

          instance.addSource('field', { type: 'geojson', data: points });
          instance.addLayer({
            id: 'field',
            type: 'heatmap',
            source: 'field',
            paint: {
              'heatmap-weight': ['get', 'w'],
              /* Low intensity and a tight radius on purpose. At the first
                 settings every centroid bloomed into its neighbours and the
                 whole map saturated to white — which looks dramatic and carries
                 no information, because a field that is everywhere maximal says
                 nothing about where change concentrates. */
              'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 0.28, 6, 0.75],
              'heatmap-color': [
                'interpolate', ['linear'], ['heatmap-density'],
                0, 'rgba(4,7,13,0)',
                0.22, 'rgba(20,50,110,0.45)',
                0.45, 'rgba(20,110,150,0.62)',
                0.66, 'rgba(34,180,175,0.74)',
                0.85, 'rgba(110,232,214,0.85)',
                1, 'rgba(226,252,248,0.95)',
              ],
              'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 6, 3, 16, 6, 34],
              // Land must stay legible through the field, or the reader loses
              // the geography the values are attached to.
              'heatmap-opacity': 0.78,
            },
          });

          // The selected district, so the field has an anchor you can find.
          if (centroid) {
            instance.addSource('here', {
              type: 'geojson',
              data: {
                type: 'Feature',
                properties: {},
                geometry: { type: 'Point', coordinates: centroid },
              },
            });
            instance.addLayer({
              id: 'here-halo',
              type: 'circle',
              source: 'here',
              paint: {
                'circle-radius': 13,
                'circle-color': 'rgba(0,0,0,0)',
                'circle-stroke-color': '#ffb454',
                'circle-stroke-width': 1.4,
              },
            });
            instance.addLayer({
              id: 'here-dot',
              type: 'circle',
              source: 'here',
              paint: { 'circle-radius': 3.2, 'circle-color': '#ffb454' },
            });
          }
        });
        instance.on('error', () => setFailed(true));
      } catch {
        if (!disposed) setFailed(true);
      }
    })();

    return () => { disposed = true; map?.remove(); };
  }, [indicatorId, centroid]);

  return (
    <section className="panel" aria-labelledby={headingId}>
      <h3 id={headingId}>Regional screening field</h3>
      <p className="choro__warn">
        <strong>Generated values.</strong> No region on this map has been
        processed. This shows how a screening indicator reads at scale — where
        change concentrates is the point, and every figure behind it is synthetic.
      </p>
      {failed ? (
        <p className="hint">
          The regional view could not be drawn. The district result above is unaffected.
        </p>
      ) : (
        <div
          ref={ref}
          className="choro__map"
          role="img"
          aria-label={
            `Generated ${indicatorId} intensity across world administrative regions`
            + `${regionName ? `, centred on ${regionName}` : ''}. Values are synthetic.`
          }
        />
      )}
      <div className="choro__legend" aria-hidden="true">
        <span>low</span>
        <span className="choro__ramp choro__ramp--aurora" />
        <span>high</span>
      </div>
      <p className="hint">
        {regionName ? (
          <>
            <span className="choro__pin" aria-hidden="true" /> marks {regionName}.{' '}
          </>
        ) : null}
        Regions: Natural Earth admin-1 (public domain, 4,596 units), bundled
        offline. Context for the demo, not the district geometry the indicators use.
      </p>
    </section>
  );
}

/* Spatial layer with a mandatory non-WebGL path.
 *
 * The fallback is not a degraded afterthought — docs/project-status.md requires
 * the layer to be inspectable "with a non-WebGL table/image fallback" and the
 * offline release gate tests the journey with WebGL unavailable. So the
 * accessible representation (bounds, legend, attribution, checksum) is rendered
 * *always*, and the map is an enhancement layered on top when the platform can
 * support it. Doing it the other way round produces a fallback nobody has
 * looked at since the day it was written.
 *
 * MapLibre is loaded lazily: it is the single largest dependency in the bundle
 * and the dashboard must be usable before it arrives, or on a device where it
 * never will. ADR-005 pins it below v6. */

import { useEffect, useId, useRef, useState } from 'react';
import type { LayerDescriptor } from '../contract/types';
import { shapeForRegion } from '../globe/overlay';
import { Callout } from './Primitives';

function webglAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(
      canvas.getContext('webgl2') ??
      canvas.getContext('webgl') ??
      canvas.getContext('experimental-webgl'),
    );
  } catch {
    return false;
  }
}

/** Only relative, application-controlled hrefs are ever resolved. The contract
 *  promises the API never returns an upstream or signed URL; this is the
 *  browser-side half of that promise, because a descriptor is still data and
 *  data is not trusted just because it validated. */
function isSafeAppHref(href: string): boolean {
  return href.startsWith('/') && !href.startsWith('//');
}

function BoundsTable({ layer }: { layer: LayerDescriptor }) {
  const [west, south, east, north] = layer.bounds;
  return (
    <table className="table table--compact">
      <caption className="sr-only">Layer extent and identity</caption>
      <tbody>
        <tr><th scope="row">Representation</th><td>{layer.representation}</td></tr>
        <tr><th scope="row">West</th><td>{west}°</td></tr>
        <tr><th scope="row">South</th><td>{south}°</td></tr>
        <tr><th scope="row">East</th><td>{east}°</td></tr>
        <tr><th scope="row">North</th><td>{north}°</td></tr>
        <tr>
          <th scope="row">Available offline</th>
          <td>{layer.availableOffline ? 'Yes' : 'No'}</td>
        </tr>
        {layer.checksum ? (
          <tr><th scope="row">Checksum</th><td><code className="wrap">{layer.checksum}</code></td></tr>
        ) : null}
      </tbody>
    </table>
  );
}

function Legend({ layer }: { layer: LayerDescriptor }) {
  if (!layer.legend.length) return null;
  return (
    <div className="legend">
      <h4 className="legend__title">Legend</h4>
      <ul className="legend__list">
        {layer.legend.map((entry) => (
          <li key={`${entry.label}-${String(entry.value)}`} className="legend__item">
            {/* The swatch is decorative; the label carries the meaning, so the
                legend still reads correctly without colour. */}
            <span
              className="legend__swatch"
              style={{ background: entry.color }}
              aria-hidden="true"
            />
            <span>{entry.label}</span>
            {entry.value !== null ? (
              <code className="legend__value">{String(entry.value)}</code>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** A descriptor carrying only what the map needs to frame a boundary. */
function syntheticBoundaryLayer(regionId: string, rings: [number, number][][]): LayerDescriptor {
  let w = 180, s = 90, e = -180, n = -90;
  for (const ring of rings) {
    for (const [lon, lat] of ring) {
      w = Math.min(w, lon); e = Math.max(e, lon);
      s = Math.min(s, lat); n = Math.max(n, lat);
    }
  }
  return {
    id: `${regionId}:extent`, kind: 'district extent', representation: 'geojson',
    href: '', tileJsonHref: null, bounds: [w, s, e, n],
    minZoom: null, maxZoom: null, opacity: 1, legend: [], attributions: [],
    checksum: null, contentVersion: null, availableOffline: true,
  };
}

function MapCanvas({ layer, regionId, syntheticLayers, accent }: {
  layer: LayerDescriptor; regionId: string; syntheticLayers: boolean; accent?: string;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const [rasterMissing, setRasterMissing] = useState(false);

  useEffect(() => {
    let disposed = false;
    let map: { remove: () => void } | null = null;

    (async () => {
      try {
        const maplibre = await import('maplibre-gl');
        if (disposed || !ref.current) return;

        // No remote basemap by design: the offline gate forbids one, and a
        // missing tile server would otherwise leave a blank frame with the
        // analytical layer invisible on top of it.
        const instance = new maplibre.Map({
          container: ref.current,
          style: { version: 8, sources: {}, layers: [
            { id: 'bg', type: 'background', paint: { 'background-color': '#0a1420' } },
          ] },
          bounds: layer.bounds,
          fitBoundsOptions: { padding: 26 },
          attributionControl: false,
          // The accessible table below is the keyboard path; leaving the canvas
          // in the tab order would trap users in a control with no equivalent.
          keyboard: false,
        });
        map = instance;

        instance.on('load', () => {
          if (disposed) return;

          /* Land and coastline context. Without it the district floats on a flat
             background and reads as a broken map rather than a located one.
             Natural Earth is public domain and is bundled into the build, so
             this costs no runtime network access — the offline gate holds.
             Provenance: data/metadata/basemap/natural-earth.provenance.json */
          instance.addSource('ne-land', { type: 'geojson', data: `${import.meta.env.BASE_URL}basemap/ne_110m_land.geojson` });
          instance.addLayer({
            id: 'ne-land-fill', type: 'fill', source: 'ne-land',
            paint: { 'fill-color': '#16202c', 'fill-outline-color': '#243244' },
          });
          instance.addSource('ne-coast', { type: 'geojson', data: `${import.meta.env.BASE_URL}basemap/ne_50m_coastline.geojson` });
          instance.addLayer({
            id: 'ne-coast-line', type: 'line', source: 'ne-coast',
            paint: { 'line-color': '#3d5a7a', 'line-width': 0.9 },
          });

          /* The district boundary, drawn from the validated geometry we already
             hold. This is the part that is always real — the raster below is a
             demo asset that may not be packaged, and a map showing nothing at
             all because one image 404'd was worse than useless. */
          // A one-degree graticule: at district scale the coastline may be off
          // screen entirely, and a grid gives the extent a sense of size.
          const [gw, gs, ge, gn] = layer.bounds;
          const lines: { type: 'Feature'; properties: Record<string, never>;
            geometry: { type: 'LineString'; coordinates: number[][] } }[] = [];
          for (let lon = Math.floor(gw) - 1; lon <= Math.ceil(ge) + 1; lon += 1) {
            lines.push({ type: 'Feature', properties: {}, geometry: {
              type: 'LineString', coordinates: [[lon, gs - 2], [lon, gn + 2]] } } as never);
          }
          for (let lat = Math.floor(gs) - 1; lat <= Math.ceil(gn) + 1; lat += 1) {
            lines.push({ type: 'Feature', properties: {}, geometry: {
              type: 'LineString', coordinates: [[gw - 2, lat], [ge + 2, lat]] } } as never);
          }
          instance.addSource('graticule', {
            type: 'geojson', data: { type: 'FeatureCollection', features: lines },
          });
          instance.addLayer({
            id: 'graticule-line', type: 'line', source: 'graticule',
            paint: { 'line-color': '#2b3a4d', 'line-width': 0.6 },
          });

          const shape = shapeForRegion(regionId, layer.bounds);
          if (shape) {
            instance.addSource('sparc-district', {
              type: 'geojson',
              data: {
                type: 'Feature',
                properties: {},
                geometry: { type: 'Polygon', coordinates: shape.rings },
              },
            });
            instance.addLayer({
              id: 'sparc-district-fill',
              type: 'fill',
              source: 'sparc-district',
              paint: { 'fill-color': accent ?? '#58b7ff', 'fill-opacity': 0.22 },
            });
            instance.addLayer({
              id: 'sparc-district-line',
              type: 'line',
              source: 'sparc-district',
              paint: {
                'line-color': accent ?? '#7fd0ff',
                'line-width': 1.6,
                // Dashed when the outline is a bounding box rather than a
                // surveyed boundary, so the two never look alike.
                ...(shape.approximate ? { 'line-dasharray': [2, 2] } : {}),
              },
            });
          }

          /* Synthetic descriptors point at demo assets that were never
             committed. Probing for one produces a guaranteed 404 in the console
             of every demo — an error that looks like a defect, caused by us
             asking for something we already know is not there. So when the
             payload is synthetic we state the absence instead of discovering
             it. */
          if (syntheticLayers) { setRasterMissing(true); return; }

          // The analytical raster is optional and often absent in a demo build.
          if (isSafeAppHref(layer.href) && layer.representation === 'image') {
            const [w, s, e, n] = layer.bounds;
            fetch(layer.href, { method: 'HEAD' })
              .then((r) => {
                if (disposed || !r.ok) {
                  if (!r.ok) setRasterMissing(true);
                  return;
                }
                instance.addSource('sparc-layer', {
                  type: 'image',
                  url: layer.href,
                  coordinates: [[w, n], [e, n], [e, s], [w, s]],
                });
                instance.addLayer({
                  id: 'sparc-layer',
                  type: 'raster',
                  source: 'sparc-layer',
                  paint: { 'raster-opacity': layer.opacity ?? 1 },
                });
              })
              .catch(() => setRasterMissing(true));
          }
        });

        instance.on('error', (event: { error?: { message?: string } }) => {
          const msg = event?.error?.message ?? '';
          // A missing raster is expected and already reported separately; do not
          // escalate it into "the map is broken", because the map is fine and
          // the boundary on it is real.
          if (/404|Not Found/i.test(msg)) { setRasterMissing(true); return; }
          setFailed(msg || 'The map could not be drawn.');
        });
      } catch (err) {
        setFailed(`The map renderer failed to load: ${String((err as Error)?.message ?? err)}`);
      }
    })();

    return () => {
      disposed = true;
      map?.remove();
    };
  }, [layer, regionId, syntheticLayers, accent]);

  return (
    <>
      <div ref={ref} className="map" role="img" aria-label={`Map preview of ${layer.id}. The table below carries the same information.`} />
      {rasterMissing ? (
        <Callout tone="info" title="Analytical raster not packaged in this build">
          <p>
            The district boundary above is the validated geometry. The
            change-detection image it would be draped with is a demo asset that
            is not committed, so only the boundary is drawn — the extent, legend
            and attribution below remain authoritative.
          </p>
        </Callout>
      ) : null}
      {failed ? (
        <Callout tone="warn" title="Map preview unavailable">
          <p>{failed}</p>
          <p>The layer's extent, legend and attribution are listed below and remain authoritative.</p>
        </Callout>
      ) : null}
    </>
  );
}

export function LayerView({ layers, regionId, syntheticLayers = false, accent }: {
  layers: LayerDescriptor[]; regionId: string; syntheticLayers?: boolean; accent?: string;
}) {
  const headingId = useId();
  const [webgl] = useState(webglAvailable);

  /* No analytical raster does not mean nothing to show. The district boundary
     always exists, so the map renders regardless — previously an empty `layers`
     array produced a text callout and no visual at all, which is what every
     generated district got. */
  if (!layers.length) {
    const shape = shapeForRegion(regionId);
    return (
      <section className="panel" aria-labelledby={headingId}>
        <h3 id={headingId}>Spatial extent</h3>
        {webgl && shape ? (
          <div className="layer__map">
            <MapCanvas
              layer={syntheticBoundaryLayer(regionId, shape.rings)}
              regionId={regionId}
              syntheticLayers
              accent={accent}
            />
          </div>
        ) : null}
        <Callout tone="info" title="No analytical layer is packaged for this result">
          <p>
            {shape?.approximate
              ? 'The outline is this district’s bounding box, drawn dashed because it is an approximation rather than a surveyed boundary.'
              : 'The outline is the validated district boundary.'}{' '}
            No change-detection raster exists for it, so there is nothing to drape
            over the shape. The metric, quality evidence and provenance are
            unaffected.
          </p>
        </Callout>
      </section>
    );
  }

  return (
    <section className="panel" aria-labelledby={headingId}>
      <h3 id={headingId}>Spatial layer</h3>

      {layers.map((layer) => (
        <article key={layer.id} className="layer">
          <header className="layer__head">
            <h4 className="layer__title">{layer.kind}</h4>
            <code className="layer__id">{layer.id}</code>
          </header>

          {webgl ? (
            <div className="layer__map">
              <MapCanvas
                layer={layer}
                regionId={regionId}
                syntheticLayers={syntheticLayers}
                accent={accent}
              />
              <p className="hint">
                The map is an optional preview. Everything it shows is also in the
                table below, which is the accessible and offline path.
              </p>
            </div>
          ) : (
            <Callout tone="info" title="WebGL is unavailable — using the accessible layer view">
              <p>
                The map preview needs WebGL. The extent, legend and attribution
                below carry the same information and are the supported path for
                the offline release.
              </p>
            </Callout>
          )}

          <BoundsTable layer={layer} />
          <Legend layer={layer} />

          <div className="layer__attrib">
            <h4 className="legend__title">Attribution</h4>
            <ul>
              {layer.attributions.map((a) => (
                <li key={a.label}>
                  {a.url ? (
                    <a href={a.url} rel="noreferrer noopener" target="_blank">{a.label}</a>
                  ) : (
                    a.label
                  )}
                </li>
              ))}
            </ul>
          </div>
        </article>
      ))}
    </section>
  );
}

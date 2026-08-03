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

function MapCanvas({ layer }: { layer: LayerDescriptor }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState<string | null>(null);

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
            { id: 'bg', type: 'background', paint: { 'background-color': '#0d1117' } },
          ] },
          bounds: layer.bounds,
          fitBoundsOptions: { padding: 16 },
          attributionControl: false,
          // The accessible table below is the keyboard path; leaving the canvas
          // in the tab order would trap users in a control with no equivalent.
          keyboard: false,
        });
        map = instance;

        instance.on('load', () => {
          if (disposed || !isSafeAppHref(layer.href)) return;
          if (layer.representation === 'image') {
            const [w, s, e, n] = layer.bounds;
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
          }
        });

        instance.on('error', (event: { error?: { message?: string } }) => {
          // A missing image is expected in the mock pack — the fixture points at
          // a demo asset that is not committed. Say so instead of looking broken.
          setFailed(event?.error?.message ?? 'The layer asset could not be loaded.');
        });
      } catch (err) {
        setFailed(`The map renderer failed to load: ${String((err as Error)?.message ?? err)}`);
      }
    })();

    return () => {
      disposed = true;
      map?.remove();
    };
  }, [layer]);

  return (
    <>
      <div ref={ref} className="map" role="img" aria-label={`Map preview of ${layer.id}. The table below carries the same information.`} />
      {failed ? (
        <Callout tone="warn" title="Map preview unavailable">
          <p>{failed}</p>
          <p>The layer's extent, legend and attribution are listed below and remain authoritative.</p>
        </Callout>
      ) : null}
    </>
  );
}

export function LayerView({ layers }: { layers: LayerDescriptor[] }) {
  const headingId = useId();
  const [webgl] = useState(webglAvailable);
  const [showMap, setShowMap] = useState(false);

  if (!layers.length) {
    return (
      <section className="panel" aria-labelledby={headingId}>
        <h3 id={headingId}>Spatial layer</h3>
        <Callout tone="info" title="No layer is packaged for this result">
          <p>
            A result without a layer is still a valid result — the metric,
            quality evidence and provenance below are unaffected. Layers are
            omitted when a period fails its coverage gate.
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
              {showMap ? (
                <MapCanvas layer={layer} />
              ) : (
                <button type="button" className="btn" onClick={() => setShowMap(true)}>
                  Load map preview
                </button>
              )}
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

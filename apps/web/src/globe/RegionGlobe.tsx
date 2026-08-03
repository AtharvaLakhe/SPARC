/* The globe panel.
 *
 * Three rules this component exists to keep, from
 * docs/architecture/3d-asset-integration.md and docs/project-status.md:
 *
 *  1. Zero 3D bytes until the user asks. three.js, the shaders and 3.3 MB of
 *     textures all sit behind a dynamic import that only runs on click, so the
 *     analytical route never pays for them.
 *  2. It is never the only way to select a district. The same districts are
 *     listed as ordinary buttons underneath, and the <select> in the header
 *     stays authoritative. A keyboard user never has to touch the canvas.
 *  3. Failure degrades to the buttons, not to a blank frame. WebGL missing,
 *     chunk failed, textures 404 — all land on the same accessible list. */

import { useEffect, useRef, useState } from 'react';
import type { GlobeHandle, GlobeMarker } from './scene';

function webglAvailable(): boolean {
  try {
    const c = document.createElement('canvas');
    return Boolean(c.getContext('webgl2') ?? c.getContext('webgl'));
  } catch {
    return false;
  }
}

export function RegionGlobe({
  markers,
  selectedId,
  onSelect,
}: {
  markers: GlobeMarker[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const handleRef = useRef<GlobeHandle | null>(null);
  /* `active` is the user's intent; `status` is what the loader is doing. They
     are separate state because the mount effect must depend on the *intent*
     only. Keying it on status too meant setStatus('ready') re-ran the effect,
     whose cleanup disposed the renderer it had just created — the globe mounted
     and tore itself down in the same tick, and the repeated WebGL context churn
     eventually took the renderer process with it. */
  const [active, setActive] = useState(false);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'failed'>('idle');
  const [failure, setFailure] = useState<string>('');
  const [hovered, setHovered] = useState<string | null>(null);
  const reduced = typeof matchMedia === 'function'
    && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Held in a ref so a selection change never re-runs the mount effect.
  const selectedRef = useRef(selectedId);
  selectedRef.current = selectedId;

  useEffect(() => {
    if (!active || !hostRef.current) return;
    let disposed = false;
    setStatus('loading');

    (async () => {
      try {
        const mod = await import('./scene');
        if (disposed || !hostRef.current) return;
        const handle = mod.mount(hostRef.current, markers, {
          onSelect,
          onHover: setHovered,
          reducedMotion: reduced,
        });
        handleRef.current = handle;
        handle.setSelected(selectedRef.current);
        if (selectedRef.current) handle.focus(selectedRef.current);
        setStatus('ready');
      } catch (err) {
        if (disposed) return;
        setFailure(String((err as Error)?.message ?? err));
        setStatus('failed');
      }
    })();

    return () => {
      disposed = true;
      handleRef.current?.dispose();
      handleRef.current = null;
    };
  }, [active, markers, onSelect, reduced]);

  useEffect(() => {
    handleRef.current?.setSelected(selectedId);
    if (selectedId) handleRef.current?.focus(selectedId);
  }, [selectedId]);

  const supported = webglAvailable();

  return (
    <section className="panel globe" aria-labelledby="globe-h">
      <div className="globe__head">
        <h2 id="globe-h">Choose a district</h2>
        {supported && !active ? (
          <button type="button" className="btn" onClick={() => setActive(true)}>
            Show the globe
            <span className="btn__note"> · loads ~3 MB</span>
          </button>
        ) : null}
        {active ? (
          <button type="button" className="btn" onClick={() => { setActive(false); setStatus('idle'); }}>
            Hide the globe
          </button>
        ) : null}
      </div>

      <p className="globe__lede">
        The globe is an optional way in. Every district on it is also a button
        below, and the dropdown above stays the primary control — nothing here is
        needed to read the data.
      </p>

      {!supported ? (
        <p className="hint">
          WebGL is unavailable in this browser, so the globe is disabled. The
          district buttons below do the same job.
        </p>
      ) : null}

      {status === 'loading' ? (
        <div className="state state--loading" aria-busy="true" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          <p>Loading the globe…</p>
        </div>
      ) : null}

      {status === 'failed' ? (
        <div className="callout callout--warn">
          <p className="callout__title">The globe could not load</p>
          <div className="callout__body">
            <p>{failure}</p>
            <p>District selection is unaffected — use the buttons below.</p>
          </div>
        </div>
      ) : null}

      {/* Present for the whole active window, so the ref exists when the mount
          effect runs and dispose() runs when the user hides it again. */}
      {active ? (
        <div
          ref={hostRef}
          className="globe__canvas"
          role="img"
          aria-label={
            'Rotating globe with a marker on each available district. '
            + 'This is decorative; use the district buttons below to select one.'
          }
        />
      ) : null}

      {hovered ? (
        <p className="globe__hover" aria-hidden="true">
          {markers.find((m) => m.id === hovered)?.name}
        </p>
      ) : null}

      <ul className="globe__list">
        {markers.map((m) => (
          <li key={m.id}>
            <button
              type="button"
              className={`btn ${m.id === selectedId ? 'btn--primary' : ''}`}
              aria-pressed={m.id === selectedId}
              onClick={() => onSelect(m.id)}
            >
              {m.name}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

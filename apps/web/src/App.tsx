/* SPARC — one application, four stages.
 *
 *   orbit → locate → period → dashboard
 *
 * The globe is the front door, not the building. Every stage past it is plain
 * HTML, so the whole analytical journey stays reachable with no WebGL: the
 * landing offers "Open the terminal" as a real control, and `#/dashboard`
 * bypasses the scene entirely.
 *
 * Routing is hash-based so a deep link survives a reload on a static file
 * server with no rewrite rules — which is what the offline demo runs on. */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { config, FROZEN_PERIODS, type DataMode, type FrozenPeriod } from './config';
import type { ComparisonSelection, RegionRef } from './contract/types';
import { DataError } from './data/errors';
import { createTransport, Repository } from './data/repository';
import { DetailScreen } from './features/DetailView';
import { LimitationsPanel, ModeBanner } from './features/Disclosure';
import { ErrorView, LoadingView } from './features/StateViews';
import { SummaryScreen } from './features/SummaryView';
import { intensityFor, shapeForRegion } from './globe/overlay';
import { styleFor } from './indicators';
import { LocationConsole, PeriodConsole } from './shell/Consoles';
import {
  mapDetail, mapSummary,
  type DetailView as DetailVM, type SummaryView as SummaryVM,
} from './viewmodel/mapper';

type Stage = 'locate' | 'period' | 'dashboard';
type Route = { name: 'summary' } | { name: 'indicator'; indicatorId: string };

type Async<T> =
  | { status: 'idle' } | { status: 'loading' }
  | { status: 'ready'; value: T } | { status: 'error'; error: DataError };

const DEFAULT_REGION = 'mock:district:nagpur';

/* The globe lives at /, this client at /app/. Leaving the dashboard means
   going back up a level, not to a route in here. */
const ORBIT_URL = '../';

function parseHash(hash: string): { stage: Stage; route: Route } {
  const ind = /^#\/dashboard\/([a-z0-9-]{1,64})/.exec(hash);
  if (ind?.[1]) return { stage: 'dashboard', route: { name: 'indicator', indicatorId: ind[1] } };
  if (hash.startsWith('#/dashboard')) return { stage: 'dashboard', route: { name: 'summary' } };
  return { stage: 'locate', route: { name: 'summary' } };
}

/* Coordinates handed over by the globe: #/locate?lat=..&lon=..&name=.. */
function handoffFromHash(hash: string): { lat: number; lon: number; name: string } | null {
  const q = hash.indexOf('?');
  if (q < 0) return null;
  const params = new URLSearchParams(hash.slice(q + 1));
  const lat = Number(params.get('lat'));
  const lon = Number(params.get('lon'));
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  return { lat, lon, name: params.get('name') ?? 'the selected point' };
}

export interface PanelMode {
  target: { lat: number; lon: number; name: string };
  onClose: () => void;
}

export default function App({ panel }: { panel?: PanelMode } = {}) {
  /* In panel mode the globe already answered "where", and routing must not
     touch location.hash — the globe owns the URL. So navigation is local
     state. Standalone keeps the hash router for shareable deep links. */
  const [panelNav, setPanelNav] = useState<{ stage: Stage; route: Route }>(
    { stage: 'locate', route: { name: 'summary' } },
  );
  const [hashNav, setNav] = useState(() => parseHash(location.hash));
  const { stage, route } = panel ? panelNav : hashNav;
  const [dataMode, setDataMode] = useState<DataMode>(config.dataMode);
  const [regionId, setRegionId] = useState<string>(DEFAULT_REGION);
  const [period, setPeriod] = useState<FrozenPeriod>(FROZEN_PERIODS[0]);
  const [regions, setRegions] = useState<RegionRef[]>([]);
  const [summary, setSummary] = useState<Async<SummaryVM>>({ status: 'idle' });
  const [detail, setDetail] = useState<Async<DetailVM>>({ status: 'idle' });
  const [reloadToken, setReloadToken] = useState(0);
  const mainRef = useRef<HTMLElement | null>(null);

  const repository = useMemo(() => new Repository(createTransport(dataMode)), [dataMode]);

  const selection: ComparisonSelection = useMemo(() => ({
    regionId,
    baselineStart: period.baselineStart,
    baselineEnd: period.baselineEnd,
    comparisonStart: period.comparisonStart,
    comparisonEnd: period.comparisonEnd,
  }), [regionId, period]);

  useEffect(() => {
    if (panel) return;
    const onHash = () => setNav(parseHash(location.hash));
    addEventListener('hashchange', onHash);
    return () => removeEventListener('hashchange', onHash);
  }, [panel]);

  useEffect(() => {
    const ac = new AbortController();
    repository.listRegions(ac.signal)
      .then((list) => setRegions(list.filter((r) => r.type === 'district')))
      .catch(() => setRegions([]));
    return () => ac.abort();
  }, [repository]);

  // Only fetch once the user has actually reached the dashboard.
  useEffect(() => {
    if (stage !== 'dashboard') return;
    const ac = new AbortController();
    setSummary({ status: 'loading' });
    repository.getRegionSummary(selection, ac.signal)
      .then((r) => setSummary({ status: 'ready', value: mapSummary(r, repository.label) }))
      .catch((e: unknown) => { if (!ac.signal.aborted) setSummary({ status: 'error', error: toDataError(e) }); });
    return () => ac.abort();
  }, [repository, selection, stage, reloadToken]);

  useEffect(() => {
    if (stage !== 'dashboard' || route.name !== 'indicator') { setDetail({ status: 'idle' }); return; }
    const ac = new AbortController();
    setDetail({ status: 'loading' });
    repository.getIndicatorComparison(selection, route.indicatorId, ac.signal)
      .then((r) => setDetail({ status: 'ready', value: mapDetail(r, repository.label) }))
      .catch((e: unknown) => { if (!ac.signal.aborted) setDetail({ status: 'error', error: toDataError(e) }); });
    return () => ac.abort();
  }, [repository, selection, stage, route, reloadToken]);

  useEffect(() => { if (stage === 'dashboard') mainRef.current?.focus(); }, [stage, route.name]);

  /* The globe owns its own scene, so the panel does not reach into it — it
     announces which indicator is in focus and the globe recolours its marker
     if it feels like it. One-way, so neither side can break the other. */
  useEffect(() => {
    const id = route.name === 'indicator' ? route.indicatorId : null;
    dispatchEvent(new CustomEvent('sparc:indicator', { detail: { indicatorId: id } }));
  }, [route]);

  /* Choropleth patch for the district in view. Sent whenever the district or
     the focused indicator changes; cleared when the panel leaves the results,
     because a patch left behind on the globe would keep asserting a selection
     that is no longer current. */
  useEffect(() => {
    if (stage !== 'dashboard') {
      dispatchEvent(new CustomEvent('sparc:district', { detail: null }));
      return;
    }
    const shape = shapeForRegion(regionId);
    if (!shape) return;

    /* Point the globe at it. Picking a district from the list previously left
       the planet wherever it happened to be, so the patch was often drawn on
       the far side and the user saw nothing happen. */
    const centre = summary.status === 'ready' ? summary.value : null;
    const globe = (window as unknown as { __orbital?: { goTo?: (lat: number, lon: number, name: string) => void } }).__orbital;
    if (centre && globe?.goTo) {
      const [w, s2, e, n] = centre.bbox;
      globe.goTo((s2 + n) / 2, (w + e) / 2, centre.regionName);
    }

    const focused = route.name === 'indicator' ? route.indicatorId : null;
    const card = summary.status === 'ready'
      ? summary.value.indicators.find((i) => (focused ? i.id === focused : true))
      : undefined;

    dispatchEvent(new CustomEvent('sparc:district', {
      detail: {
        rings: shape.rings,
        approximate: shape.approximate,
        colour: Number(styleFor(focused ?? 'surface-water').accent.replace('#', '0x')),
        intensity: intensityFor(card?.metric.percentRaw ?? null),
      },
    }));
  }, [stage, regionId, route, summary]);

  const go = useCallback((hash: string) => { location.hash = hash; }, []);
  const openIndicator = useCallback((id: string) => {
    if (panel) setPanelNav({ stage: 'dashboard', route: { name: 'indicator', indicatorId: id } });
    else go(`#/dashboard/${id}`);
  }, [panel, go]);
  const backToSummary = useCallback(() => {
    if (panel) setPanelNav({ stage: 'dashboard', route: { name: 'summary' } });
    else go('#/dashboard');
  }, [panel, go]);
  const retry = useCallback(() => setReloadToken((n) => n + 1), []);

  /* Resolution lives in LocationConsole and nowhere else. It previously also
     happened here, and the two disagreed: this one silently switched to the
     location step while the console — which owns the explanation — never
     learned a target had been rejected. Targeting Mumbai therefore re-asked
     "where?" with no reason given. */
  const regionName = regions.find((r) => r.id === regionId)?.name ?? 'this district';

  /* ── stages before the dashboard ───────────────────────────────────────── */
  if (stage === 'locate' || stage === 'period') {
    return (
      <div className="handoff">
        {stage === 'locate' ? (
          <LocationConsole
            /* The real list, never a stand-in. A one-element fallback here made
               "still loading" indistinguishable from "only Nagpur exists", so the
               console auto-resolved an incoming target against an incomplete list
               and refused London — which it does have. The console waits instead. */
            regions={regions}
            onResolved={(id) => {
              setRegionId(id);
              /* Straight to the numbers. There is exactly one processed
                 comparison window, so asking which one to use is a question
                 with a single possible answer — pure friction between the user
                 and the thing they asked for. "Change period" in the header
                 reopens it for when there is more than one. */
              const next = FROZEN_PERIODS.length > 1
                ? { stage: 'period' as Stage, route: { name: 'summary' as const } }
                : { stage: 'dashboard' as Stage, route: { name: 'summary' as const } };
              if (panel) setPanelNav(next); else setNav(next);
            }}
            handoff={panel ? panel.target : handoffFromHash(location.hash)}
            showDemoCities={dataMode === 'demo'}
            onCancel={() => { location.href = ORBIT_URL; }}
          />
        ) : (
          <PeriodConsole
            regionName={regionName}
            onChosen={(p) => {
              setPeriod(p);
              if (panel) setPanelNav({ stage: 'dashboard', route: { name: 'summary' } });
              else go('#/dashboard');
            }}
            onBack={() => setNav({ stage: 'locate', route: { name: 'summary' } })}
          />
        )}
      </div>
    );
  }

  /* ── dashboard ─────────────────────────────────────────────────────────── */
  const badge = summary.status === 'ready' ? summary.value.badge
    : detail.status === 'ready' ? detail.value.badge : null;
  const warnings = summary.status === 'ready' ? summary.value.warnings : [];

  return (
    <div className="app">
      <a className="skip" href="#main">Skip to results</a>

      <header className="topbar">
        <div className="brand">
          <span className="brand__name">SPARC</span>
          <span className="brand__sub">{regionName} · {period.label}</span>
        </div>
        <div className="topbar__actions">
          {badge ? <ModeBanner badge={badge} warnings={warnings} /> : null}
          <button
            type="button" className="btn"
            onClick={() => (panel
              ? setPanelNav({ stage: 'locate', route: { name: 'summary' } })
              : go('#/locate'))}
          >
            Change period
          </button>
          <button
            type="button" className="btn btn--ghost" data-autofocus
            onClick={() => (panel ? panel.onClose() : (location.href = ORBIT_URL))}
          >
            {panel ? 'Close' : 'Back to orbit'}
          </button>
        </div>
      </header>

      <main id="main" ref={mainRef} tabIndex={-1} className="main">
        {route.name === 'summary' ? (
          summary.status === 'loading' || summary.status === 'idle' ? (
            <LoadingView what="the district summary" />
          ) : summary.status === 'error' ? (
            <ErrorView
              error={summary.error} onRetry={retry}
              onResetPeriods={() => setPeriod(FROZEN_PERIODS[0])}
              canUseOffline={dataMode === 'api'}
              onUseOffline={() => setDataMode('demo')}
            />
          ) : (
            <SummaryScreen summary={summary.value} onOpenIndicator={openIndicator} />
          )
        ) : detail.status === 'loading' || detail.status === 'idle' ? (
          <LoadingView what="the indicator result" />
        ) : detail.status === 'error' ? (
          <>
            <nav aria-label="Breadcrumb" className="crumb">
              <button type="button" className="btn btn--link" onClick={backToSummary}>
                ← Back to district summary
              </button>
            </nav>
            <ErrorView
              error={detail.error} onRetry={retry}
              onResetPeriods={() => setPeriod(FROZEN_PERIODS[0])}
              canUseOffline={dataMode === 'api'}
              onUseOffline={() => setDataMode('demo')}
            />
          </>
        ) : (
          <DetailScreen detail={detail.value} onBack={backToSummary} />
        )}

        <LimitationsPanel />
      </main>

      <footer className="foot">
        <p>Contract {config.contractVersion} · No official SDG claim, no causal claim.</p>
      </footer>
    </div>
  );
}

function toDataError(err: unknown): DataError {
  if (err instanceof DataError) return err;
  return new DataError('server', String((err as Error)?.message ?? err));
}

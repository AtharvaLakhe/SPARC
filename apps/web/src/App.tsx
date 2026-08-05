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
import { config, FROZEN_PERIODS, frozenPeriodsForRegion, type DataMode, type FrozenPeriod } from './config';
import type { ComparisonSelection, RegionRef } from './contract/types';
import { DataError } from './data/errors';
import { createTransport, Repository } from './data/repository';
import { DetailScreen } from './features/DetailView';
import { LimitationsPanel, ModeBanner } from './features/Disclosure';
import { ErrorView, LoadingView } from './features/StateViews';
import { SummaryScreen } from './features/SummaryView';
import { FallbackCityView } from './features/FallbackCityView';
import { ChapterRail, type ChapterRailChapter } from './features/ChapterRail';
import { intensityFor, shapeForRegion } from './globe/overlay';
import { styleFor } from './indicators';
import { LocationConsole, PeriodConsole } from './shell/Consoles';
import { ReportConcern } from './reporting/ReportConcern';
import {
  mapDetail, mapSummary,
  userFacingLabel,
  type DetailView as DetailVM, type SummaryView as SummaryVM,
} from './viewmodel/mapper';
import { cityForRegionId, isValidatedCity, type CityCatalogEntry } from './catalog/cities';

type Stage = 'locate' | 'period' | 'dashboard';
type Route = { name: 'summary' } | { name: 'indicator'; indicatorId: string };

type Async<T> =
  | { status: 'idle' } | { status: 'loading' }
  | { status: 'ready'; value: T } | { status: 'error'; error: DataError };

const DEFAULT_REGION = 'district:nagpur';
const DEFAULT_PERIOD = FROZEN_PERIODS[0]!;

/* The globe-led experience is the canonical public entry. */
const ORBIT_URL = '/';

const SUMMARY_CHAPTERS: readonly ChapterRailChapter[] = [
  { id: 'summary-overview', label: 'Window' },
  { id: 'summary-signals', label: 'Signals' },
  { id: 'summary-report', label: 'Respond' },
];

const DETAIL_CHAPTERS: readonly ChapterRailChapter[] = [
  { id: 'detail-signal', label: 'Finding' },
  { id: 'detail-reading', label: 'Reading' },
  { id: 'detail-evidence', label: 'Evidence' },
  { id: 'detail-quality', label: 'Quality' },
  { id: 'detail-spatial', label: 'Spatial' },
];

function coordinate(value: number, positive: string, negative: string) {
  return `${Math.abs(value).toFixed(2)}°${value >= 0 ? positive : negative}`;
}

function parseHash(hash: string): { stage: Stage; route: Route } {
  const ind = /^#\/dashboard\/([a-z0-9-]{1,64})/.exec(hash);
  if (ind?.[1]) return { stage: 'dashboard', route: { name: 'indicator', indicatorId: ind[1] } };
  if (hash.startsWith('#/dashboard')) return { stage: 'dashboard', route: { name: 'summary' } };
  if (hash.startsWith('#/period')) return { stage: 'period', route: { name: 'summary' } };
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
  const [regionsLoading, setRegionsLoading] = useState(true);
  const [summary, setSummary] = useState<Async<SummaryVM>>({ status: 'idle' });
  const [detail, setDetail] = useState<Async<DetailVM>>({ status: 'idle' });
  const [reloadToken, setReloadToken] = useState(0);
  // CODEX PROTOTYPE HANDOFF: Claude should replace this local shell with the
  // reviewed reporting transport once the browser contract is consumed.
  const [reportOpen, setReportOpen] = useState(false);
  const [previewIndicatorId, setPreviewIndicatorId] = useState<string | null>(null);
  const mainRef = useRef<HTMLElement | null>(null);

  const repository = useMemo(() => new Repository(createTransport(dataMode)), [dataMode]);
  const catalogCity: CityCatalogEntry | null = cityForRegionId(regionId);
  const cityHasValidatedPack = isValidatedCity(catalogCity);
  const availablePeriods = useMemo(() => frozenPeriodsForRegion(regionId), [regionId]);

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
    setRegionsLoading(true);
    setRegions([]);
    repository.listRegions(ac.signal)
      .then((list) => {
        if (ac.signal.aborted) return;
        setRegions(list.filter((r) => r.type === 'district'));
        setRegionsLoading(false);
      })
      .catch(() => {
        if (ac.signal.aborted) return;
        setRegions([]);
        setRegionsLoading(false);
      });
    return () => ac.abort();
  }, [repository]);

  // Only fetch once the user has actually reached the dashboard.
  useEffect(() => {
    if (stage !== 'dashboard' || (catalogCity && !cityHasValidatedPack)) {
      if (catalogCity && !cityHasValidatedPack) setSummary({ status: 'idle' });
      return;
    }
    const ac = new AbortController();
    setSummary({ status: 'loading' });
    repository.getRegionSummary(selection, ac.signal)
      .then((r) => setSummary({ status: 'ready', value: mapSummary(r, repository.label) }))
      .catch((e: unknown) => { if (!ac.signal.aborted) setSummary({ status: 'error', error: toDataError(e) }); });
    return () => ac.abort();
  }, [repository, selection, stage, reloadToken, catalogCity, cityHasValidatedPack]);

  useEffect(() => {
    if (stage !== 'dashboard' || route.name !== 'indicator' || (catalogCity && !cityHasValidatedPack)) { setDetail({ status: 'idle' }); return; }
    const ac = new AbortController();
    setDetail({ status: 'loading' });
    repository.getIndicatorComparison(selection, route.indicatorId, ac.signal)
      .then((r) => setDetail({ status: 'ready', value: mapDetail(r, repository.label) }))
      .catch((e: unknown) => { if (!ac.signal.aborted) setDetail({ status: 'error', error: toDataError(e) }); });
    return () => ac.abort();
  }, [repository, selection, stage, route, reloadToken, catalogCity, cityHasValidatedPack]);

  useEffect(() => {
    if (stage !== 'dashboard' || !mainRef.current) return;
    const drawer = mainRef.current.closest<HTMLElement>('.sparc-panel');
    if (drawer) drawer.scrollTop = 0;
    else mainRef.current.scrollIntoView({ block: 'start' });
    /* Focus announces the new result to keyboard and assistive-tech users, but
       its default scroll would tuck the first heading under the sticky mission
       header on a narrow viewport. The container is already positioned above. */
    mainRef.current.focus({ preventScroll: true });
  }, [stage, route.name]);

  /* The globe owns its own scene, so the panel does not reach into it — it
     announces which indicator is in focus and the globe recolours its marker
     if it feels like it. One-way, so neither side can break the other. */
  useEffect(() => {
    const id = stage === 'dashboard'
      ? route.name === 'indicator' ? route.indicatorId : previewIndicatorId
      : null;
    dispatchEvent(new CustomEvent('sparc:indicator', { detail: { indicatorId: id } }));
  }, [stage, route, previewIndicatorId]);

  /* Camera movement belongs to target selection, not signal preview. Keeping
     it separate prevents each scroll-linked colour change from restarting the
     globe's flight animation. */
  useEffect(() => {
    if (stage !== 'dashboard' || summary.status !== 'ready') return;
    const globe = (window as unknown as { __orbital?: { goTo?: (lat: number, lon: number, name: string) => void } }).__orbital;
    if (!globe?.goTo) return;
    const [w, s2, e, n] = summary.value.bbox;
    globe.goTo((s2 + n) / 2, (w + e) / 2, summary.value.regionName);
  }, [stage, summary]);

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

    const focused = route.name === 'indicator' ? route.indicatorId : previewIndicatorId;
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
  }, [stage, regionId, route, summary, previewIndicatorId]);

  const go = useCallback((hash: string) => { location.hash = hash; }, []);
  const openIndicator = useCallback((id: string) => {
    setPreviewIndicatorId(null);
    if (panel) setPanelNav({ stage: 'dashboard', route: { name: 'indicator', indicatorId: id } });
    else go(`#/dashboard/${id}`);
  }, [panel, go]);
  const backToSummary = useCallback(() => {
    setPreviewIndicatorId(null);
    if (panel) setPanelNav({ stage: 'dashboard', route: { name: 'summary' } });
    else go('#/dashboard');
  }, [panel, go]);
  const previewIndicator = useCallback((id: string | null) => {
    setPreviewIndicatorId((current) => current === id ? current : id);
  }, []);
  const retry = useCallback(() => setReloadToken((n) => n + 1), []);

  /* Resolution lives in LocationConsole and nowhere else. It previously also
     happened here, and the two disagreed: this one silently switched to the
     location step while the console — which owns the explanation — never
     learned a target had been rejected. Targeting Mumbai therefore re-asked
     "where?" with no reason given. */
  const regionName = userFacingLabel(catalogCity?.name ?? regions.find((r) => r.id === regionId)?.name ?? 'this district');

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
            regionsLoading={regionsLoading}
            onResolved={(id) => {
              setRegionId(id);
              setPeriod(frozenPeriodsForRegion(id)[0] ?? DEFAULT_PERIOD);
              setSummary({ status: 'idle' });
              setDetail({ status: 'idle' });
              const pickedCity = cityForRegionId(id);
              if (pickedCity && !isValidatedCity(pickedCity)) {
                const next = { stage: 'dashboard' as Stage, route: { name: 'summary' as const } };
                if (panel) setPanelNav(next); else setNav(next);
                return;
              }
              /* Each accepted district has a frozen comparison window. Keep
                 the period step explicit so a district cannot accidentally be
                 queried with another district's dates. */
              const next = FROZEN_PERIODS.length > 1
                ? { stage: 'period' as Stage, route: { name: 'summary' as const } }
                : { stage: 'dashboard' as Stage, route: { name: 'summary' as const } };
              if (panel) setPanelNav(next); else setNav(next);
            }}
            handoff={panel ? panel.target : handoffFromHash(location.hash)}
            /* Only stable packaged regions appear as processed districts.
               Catalog targets remain available for their explicitly labelled
               report/export scope; they never receive invented metrics. */
            showDemoCities={false}
            onCancel={() => {
              if (panel) panel.onClose(); else location.href = ORBIT_URL;
            }}
          />
        ) : (
          <PeriodConsole
            regionName={regionName}
            periods={availablePeriods}
            onChosen={(p) => {
              setPeriod(p);
              setSummary({ status: 'idle' });
              setDetail({ status: 'idle' });
              if (panel) setPanelNav({ stage: 'dashboard', route: { name: 'summary' } });
              else go('#/dashboard');
            }}
            onBack={() => {
              const next = { stage: 'locate' as Stage, route: { name: 'summary' as const } };
              if (panel) setPanelNav(next); else setNav(next);
            }}
          />
        )}
      </div>
    );
  }

  /* ── dashboard ─────────────────────────────────────────────────────────── */
  const badge = summary.status === 'ready' ? summary.value.badge
    : detail.status === 'ready' ? detail.value.badge : null;
  const warnings = summary.status === 'ready' ? summary.value.warnings : [];
  const fallbackCity = catalogCity && !cityHasValidatedPack ? catalogCity : null;
  const chapters = fallbackCity
    ? []
    : route.name === 'summary' && summary.status === 'ready'
      ? SUMMARY_CHAPTERS
      : route.name === 'indicator' && detail.status === 'ready'
        ? DETAIL_CHAPTERS
        : [];

  return (
    <div className={`app${chapters.length ? ' app--chapters' : ''}`}>
      <a className="skip" href="#main">Skip to results</a>

      <header className="topbar">
        <div className="brand">
          {panel ? <span className="brand__beacon" aria-hidden="true"><i /></span> : null}
          <span className="brand__copy">
            {panel ? <span className="brand__eyebrow">Orbital analysis / district scan</span> : null}
            <span className="brand__name">SPARC</span>
            <span className="brand__sub">{regionName} · {fallbackCity ? 'Report/export scope' : period.label}</span>
          </span>
        </div>
        <div className="topbar__actions">
          {!panel && badge ? <ModeBanner badge={badge} warnings={warnings} /> : null}
          <button
            type="button" className="btn"
            onClick={() => {
              if (fallbackCity) {
                if (panel) setPanelNav({ stage: 'locate', route: { name: 'summary' } });
                else go('#/locate');
                return;
              }
              if (panel) setPanelNav({ stage: 'period', route: { name: 'summary' } });
              else go('#/period');
            }}
          >
            {fallbackCity ? 'Change target' : panel ? 'Window' : 'Change period'}
          </button>
          <button
            type="button" className="btn btn--ghost" data-autofocus
            aria-label={panel ? 'Close analysis panel' : undefined}
            title={panel ? 'Close analysis panel' : undefined}
            onClick={() => (panel ? panel.onClose() : (location.href = ORBIT_URL))}
          >
            {panel ? <span className="topbar__close" aria-hidden="true">×</span> : 'Back to orbit'}
          </button>
        </div>

        {panel ? (
          <div className="mission-strip" aria-label="Selected target details">
            <span className="mission-strip__state"><span aria-hidden="true" /> Target acquired</span>
            <dl className="mission-strip__telemetry">
              <div><dt>Lat</dt><dd>{coordinate(panel.target.lat, 'N', 'S')}</dd></div>
              <div><dt>Lon</dt><dd>{coordinate(panel.target.lon, 'E', 'W')}</dd></div>
              <div><dt>Signals</dt><dd>{summary.status === 'ready' ? summary.value.indicators.length : '—'}</dd></div>
            </dl>
            {badge ? <ModeBanner badge={badge} warnings={warnings} /> : null}
          </div>
        ) : null}
      </header>

      <div className="analysis-frame">
        {chapters.length ? <ChapterRail chapters={chapters} /> : null}
        <main
          id="main"
          ref={mainRef}
          tabIndex={-1}
          className={`main${route.name === 'indicator' ? ' main--detail' : ''}`}
        >
        {fallbackCity ? (
          <FallbackCityView city={fallbackCity} onReport={() => setReportOpen(true)} />
        ) : route.name === 'summary' ? (
          summary.status === 'loading' || summary.status === 'idle' ? (
            <LoadingView what="the district summary" />
          ) : summary.status === 'error' ? (
            <ErrorView
              error={summary.error} onRetry={retry}
              onResetPeriods={() => setPeriod(availablePeriods[0] ?? DEFAULT_PERIOD)}
              canUseOffline={dataMode === 'api'}
              onUseOffline={() => setDataMode('demo')}
            />
          ) : (
            <SummaryScreen
              summary={summary.value}
              onOpenIndicator={openIndicator}
              onPreviewIndicator={previewIndicator}
              onReport={() => setReportOpen(true)}
            />
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
              onResetPeriods={() => setPeriod(availablePeriods[0] ?? DEFAULT_PERIOD)}
              canUseOffline={dataMode === 'api'}
              onUseOffline={() => setDataMode('demo')}
            />
          </>
        ) : (
          <DetailScreen detail={detail.value} onBack={backToSummary} />
        )}

          <LimitationsPanel />
        </main>
      </div>

      <footer className="foot">
        <p>Contract {config.contractVersion} · No official SDG claim, no causal claim.</p>
      </footer>

      <ReportConcern
        open={reportOpen}
        onClose={() => setReportOpen(false)}
        regionName={regionName}
        regionId={regionId}
        analysisSnapshot={summary.status === 'ready' ? summary.value : undefined}
        coordinates={regions.find((region) => region.id === regionId)?.centroid}
        catalogEntry={catalogCity ?? undefined}
      />
    </div>
  );
}

function toDataError(err: unknown): DataError {
  if (err instanceof DataError) return err;
  return new DataError('server', String((err as Error)?.message ?? err));
}

/* The quick-target picker. Each catalog card identifies the country, explicit
 * boundary definition, analytical coverage, and routing coverage before the
 * user opens a location. It deliberately does not invent metric previews for
 * a city whose Earth Engine pack has not passed the processing gate. */

import { CITY_CATALOG, type CityCatalogEntry } from '../catalog/cities';

function CityCard({
  city,
  index,
  onPick,
}: {
  city: CityCatalogEntry;
  index: number;
  onPick: (regionId: string) => void;
}) {
  const supported = city.analyticsCoverage === 'FULLY_SUPPORTED';
  const boundary = city.boundary.kind === 'catalog-envelope'
    ? 'catalog WGS84 envelope · report/export scope'
    : `${city.boundary.kind.replace('validated-', '').toUpperCase()} · ${city.boundary.status.toLowerCase()}`;
  const coverage = supported ? 'Satellite pack available' : 'Report and export available';
  const routing = city.routingCoverage.replaceAll('_', ' ').toLowerCase();

  return (
    <li>
      <button
        type="button"
        className={`citycard${supported ? ' citycard--supported' : ''}`}
        onClick={() => onPick(city.regionId)}
      >
        <span className="citycard__index" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
        <span className="citycard__body">
          <span className="citycard__head">
            <span className="citycard__name">{city.name}</span>
            <span className="citycard__country">{city.countryCode} / {city.country}</span>
          </span>
          <span className="citycard__story">{city.story}</span>
          <span className="citycard__meta">
            <span><i className="citycard__status" aria-hidden="true" />{coverage}</span>
            <span>Boundary / {boundary}</span>
            <span>Routing / {routing}</span>
          </span>
        </span>
        <span className="citycard__action">
          <span className="citycard__badge">{city.analyticsCoverage.replaceAll('_', ' ')}</span>
          <span className="citycard__go">Open <span aria-hidden="true">↗</span></span>
        </span>
      </button>
    </li>
  );
}

export function CityPicker({
  onPick,
  regions = [],
  mockRegion,
  showDemoCities = false,
}: {
  onPick: (regionId: string) => void;
  /** District outputs available through either transport. */
  regions?: Array<{ id: string; name: string }>;
  /** Backward-compatible single-region input for older callers. */
  mockRegion?: { id: string; name: string } | null;
  /** Kept for compatibility with older callers; catalog cards are always shown. */
  showDemoCities?: boolean;
}) {
  const availableRegions = regions.length ? regions : (mockRegion ? [mockRegion] : []);
  return (
    <div className="picker">
      {availableRegions.length ? (
        <section className="picker__section" aria-labelledby="available-districts">
          <p className="picker__label picker__label--fixture" id="available-districts">
            <span>Processed districts</span>
            <span className="picker__count">{String(availableRegions.length).padStart(2, '0')}</span>
          </p>
          <ul className="picker__fixture">
            {availableRegions.map((region, index) => (
              <li key={region.id}>
                <button type="button" className="citycard citycard--fixture" onClick={() => onPick(region.id)}>
                  <span className="citycard__index" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
                  <span className="citycard__body">
                    <span className="citycard__head">
                      <span className="citycard__name">{region.name.replace(/\s+—\s+MOCK(?: REGION)?\b/gi, '')}</span>
                      <span className="citycard__country">Validated analysis scope</span>
                    </span>
                    <span className="citycard__story">
                      Open the district analysis and review the source, processing
                      method, analysis period, and known limitations.
                    </span>
                    <span className="citycard__meta">
                      <span><i className="citycard__status" aria-hidden="true" />Processed result available</span>
                    </span>
                  </span>
                  <span className="citycard__action"><span className="citycard__go">Open <span aria-hidden="true">↗</span></span></span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="picker__section" aria-labelledby="quick-targets">
        <p className="picker__label" id="quick-targets">
          <span>Catalog targets</span>
          <span className="picker__warn">coverage / boundary / routing disclosed</span>
        </p>
        <ul className="picker__grid">
          {CITY_CATALOG.map((city, index) => (
            <CityCard key={city.slug} city={city} index={index} onPick={onPick} />
          ))}
        </ul>
      </section>
    </div>
  );
}

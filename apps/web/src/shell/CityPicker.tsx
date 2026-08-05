/* The quick-target picker. Each catalog card identifies the country, explicit
 * boundary definition, analytical coverage, and routing coverage before the
 * user opens a location. It deliberately does not invent metric previews for
 * a city whose Earth Engine pack has not passed the processing gate. */

import { CITY_CATALOG, type CityCatalogEntry } from '../catalog/cities';

function CityCard({ city, onPick }: { city: CityCatalogEntry; onPick: (regionId: string) => void }) {
  const supported = city.analyticsCoverage === 'FULLY_SUPPORTED';

  return (
    <li>
      <button type="button" className="citycard" onClick={() => onPick(city.regionId)}>
        <span className="citycard__head">
          <span className="citycard__name">{city.name}</span>
          <span className="citycard__country">{city.countryCode} · {city.country}</span>
          <span className="citycard__badge">{city.analyticsCoverage.replaceAll('_', ' ')}</span>
        </span>
        <span className="citycard__story">{city.story}</span>

        <span className="citycard__story">
          Boundary: {city.boundary.kind === 'validated-adm2' ? 'geoBoundaries ADM2 (validated)' : 'catalog WGS84 envelope (report/export scope)'}
        </span>

        <span className="citycard__foot">
          <span className="citycard__cov">{supported ? 'Satellite pack available' : 'Report and export available'} · routing {city.routingCoverage.replaceAll('_', ' ').toLowerCase()}</span>
          <span className="citycard__go">Open →</span>
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
        <>
          <p className="picker__label picker__label--fixture">Available districts</p>
          <ul className="picker__fixture">
            {availableRegions.map((region) => (
              <li key={region.id}>
                <button type="button" className="citycard citycard--fixture" onClick={() => onPick(region.id)}>
                  <span className="citycard__head">
                    <span className="citycard__name">{region.name.replace(/\s+—\s+MOCK(?: REGION)?\b/gi, '')}</span>
                  </span>
                  <span className="citycard__story">
                    Open the district analysis and review the source, processing
                    method, analysis period, and known limitations.
                  </span>
                  <span className="citycard__go">Open →</span>
                </button>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      <p className="picker__label">
        Quick targets
        <span className="picker__warn">country code · boundary and coverage state shown</span>
      </p>
      <ul className="picker__grid">
        {CITY_CATALOG.map((city) => <CityCard key={city.slug} city={city} onPick={onPick} />)}
      </ul>
    </div>
  );
}

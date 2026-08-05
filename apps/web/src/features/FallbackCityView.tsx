import type { CityCatalogEntry } from '../catalog/cities';

export function FallbackCityView({ city, onReport }: { city: CityCatalogEntry; onReport: () => void }) {
  return (
    <section className="fallback-city" aria-labelledby="fallback-city-title">
      <p className="summary__eyebrow">CITY SCOPE · {city.countryCode}</p>
      <h1 id="fallback-city-title">{city.name}</h1>
      <p className="summary__lede">{city.story}</p>

      <div className="fallback-city__grid">
        <article className="card fallback-city__card">
          <h2>Analysis availability</h2>
          <p className="fallback-city__status">No validated Earth Engine pack is published for this city.</p>
          <p>SPARC keeps the dashboard contract safe: no satellite-derived value is invented or presented as a measurement. You can still create a neutral inspection request and export its evidence package.</p>
        </article>
        <article className="card fallback-city__card">
          <h2>Boundary definition</h2>
          <p>{city.boundary.definition}</p>
          <dl className="fallback-city__facts">
            <div><dt>Administrative area</dt><dd>{city.administrativeAreas.join(' · ')}</dd></div>
            <div><dt>Coordinates</dt><dd>{city.centroid[1].toFixed(4)}, {city.centroid[0].toFixed(4)}</dd></div>
            <div><dt>CRS</dt><dd>{city.boundary.crs}</dd></div>
            <div><dt>Boundary checksum</dt><dd><code>{city.boundary.sha256}</code></dd></div>
          </dl>
        </article>
      </div>

      <div className="fallback-city__actions">
        <button type="button" className="btn btn--primary" onClick={onReport}>Report environmental concern</button>
        <p className="fallback-city__note">Authority routing: {city.routingCoverage.replaceAll('_', ' ').toLowerCase()}. SPARC will not guess an official authority where its registry is not verified.</p>
      </div>
    </section>
  );
}


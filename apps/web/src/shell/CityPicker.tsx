/* The district picker.
 *
 * It used to be a row of grey pills that said nothing about what you were about
 * to open. Now each card carries the district's own headline: three indicator
 * dials showing the direction and magnitude of change, and a coverage read.
 * The point is that the choice is informed before you make it — you can see
 * which places actually moved without opening any of them.
 *
 * The dials are SVG, drawn inline. No chart library: three arcs and a needle do
 * not justify 40 kB of dependency on the critical path of an offline bundle.
 *
 * Colour matches the globe marker and the indicator card, so water is the same
 * blue in all three places. Every dial also prints its signed percentage, so
 * the card reads without colour and without the arc. */

import { styleFor } from '../indicators';
import { DEMO_CITIES, previewFor, regionIdFor, type DemoCity } from '../demo/cities';

/* An arc from 12 o'clock, clockwise for growth and anticlockwise for loss, so
   direction is legible as a shape and not only as a sign. Magnitude is
   compressed: district-scale change is usually small, and a linear map would
   make every dial look identical. */
function Dial({ pct, accent, label, glyph }: {
  pct: number; accent: string; label: string; glyph: string;
}) {
  const R = 15.5;
  const C = 2 * Math.PI * R;
  const mag = Math.min(1, Math.log10(1 + Math.abs(pct)) / Math.log10(31)); // 0..1 over 0..30%
  const sweep = Math.max(0.02, mag) * C * 0.75;
  const grew = pct >= 0;

  return (
    <div className="dial" title={`${label}: ${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`}>
      <svg viewBox="0 0 40 40" className="dial__svg" aria-hidden="true">
        <circle cx="20" cy="20" r={R} className="dial__track" />
        <circle
          cx="20" cy="20" r={R}
          className="dial__arc"
          stroke={accent}
          strokeDasharray={`${sweep} ${C}`}
          transform={grew ? 'rotate(-90 20 20)' : 'rotate(-90 20 20) scale(1 -1) translate(0 -40)'}
        />
        <text x="20" y="24" className="dial__glyph" fill={accent}>{glyph}</text>
      </svg>
      <span className="dial__pct">{pct >= 0 ? '+' : ''}{pct.toFixed(1)}%</span>
      <span className="dial__label">{label}</span>
    </div>
  );
}

function CityCard({ city, onPick }: { city: DemoCity; onPick: (regionId: string) => void }) {
  const p = previewFor(city);
  const water = styleFor('surface-water');
  const veg = styleFor('vegetation');
  const built = styleFor('built-up');

  return (
    <li>
      <button type="button" className="citycard" onClick={() => onPick(regionIdFor(city))}>
        <span className="citycard__head">
          <span className="citycard__name">{city.name}</span>
          <span className="citycard__country">{city.country}</span>
        </span>
        <span className="citycard__story">{city.story}</span>

        <span className="citycard__dials">
          <Dial pct={p.water} accent={water.accent} label="Water" glyph={water.glyph} />
          <Dial pct={p.vegetation} accent={veg.accent} label="Green" glyph={veg.glyph} />
          <Dial pct={p.built} accent={built.accent} label="Built" glyph={built.glyph} />
        </span>

        <span className="citycard__foot">
          <span className="citycard__cov">
            <span className="citycard__covbar">
              <span className="citycard__covfill" style={{ width: `${p.coverage}%` }} />
            </span>
            {p.coverage.toFixed(0)}% coverage
          </span>
          <span className="citycard__go">Open →</span>
        </span>
      </button>
    </li>
  );
}

export function CityPicker({
  onPick,
  mockRegion,
  showDemoCities = false,
}: {
  onPick: (regionId: string) => void;
  /** The committed mock fixture available through either transport. */
  mockRegion?: { id: string; name: string } | null;
  /** Generated cities are only available from DemoTransport, never ApiTransport. */
  showDemoCities?: boolean;
}) {
  return (
    <div className="picker">
      {mockRegion ? (
        <>
          <p className="picker__label picker__label--fixture">Bundled synthetic fixture</p>
          <ul className="picker__fixture">
            <li>
              <button type="button" className="citycard citycard--fixture" onClick={() => onPick(mockRegion.id)}>
                <span className="citycard__head">
                  <span className="citycard__name">{mockRegion.name}</span>
                  <span className="citycard__badge">mock fixture</span>
                </span>
                <span className="citycard__story">
                  Bundled synthetic values used to exercise the pilot interface.
                  This does not render an accepted or deployable real-data pack.
                </span>
                <span className="citycard__go">Open →</span>
              </button>
            </li>
          </ul>
        </>
      ) : null}

      {showDemoCities ? (
        <>
          <p className="picker__label">
            Demonstration districts
            <span className="picker__warn">generated values · not observations</span>
          </p>
          <ul className="picker__grid">
            {DEMO_CITIES.map((c) => <CityCard key={c.slug} city={c} onPick={onPick} />)}
          </ul>
        </>
      ) : null}
    </div>
  );
}

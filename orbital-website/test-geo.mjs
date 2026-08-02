/* Node smoke test for the coordinate + query logic.  node test-geo.mjs  */

import { latLonToVec3, vec3ToLatLon, parseQuery, fmtLat, fmtLon } from './geo.js';
import { PLACES, findPlaces, nearestPlace } from './places.js';

let pass = 0, fail = 0;
const ok = (name, cond, extra = '') => {
  if (cond) { pass++; }
  else { fail++; console.log(`  FAIL  ${name} ${extra}`); }
};
const near = (a, b, eps = 1e-6) => Math.abs(a - b) < eps;

console.log('\ncoordinate round-trip');
for (const p of PLACES) {
  const v = latLonToVec3(p.lat, p.lon, 1);
  const back = vec3ToLatLon(v);
  ok(`${p.name} lat`, near(back.lat, p.lat, 1e-9), `got ${back.lat} want ${p.lat}`);
  // longitude is degenerate at the poles, skip the wrap check there
  if (Math.abs(p.lat) < 89.9) {
    ok(`${p.name} lon`, near(((back.lon - p.lon + 540) % 360) - 180, 0, 1e-9),
       `got ${back.lon} want ${p.lon}`);
  }
}

console.log('cardinal directions');
ok('north pole', near(latLonToVec3(90, 0, 1).y, 1, 1e-12));
ok('south pole', near(latLonToVec3(-90, 0, 1).y, -1, 1e-12));
ok('equator radius', near(Math.hypot(...Object.values(latLonToVec3(0, 45, 1))), 1, 1e-12));
ok('lon wraps', near(latLonToVec3(0, 180, 1).x, latLonToVec3(0, -180, 1).x, 1e-9));

console.log('unit vectors stay unit');
for (const [lat, lon] of [[0, 0], [45, 90], [-33.9, 18.4], [78.2, 15.6], [-77.8, 166.7]]) {
  const v = latLonToVec3(lat, lon, 1);
  ok(`|v| at ${lat},${lon}`, near(Math.hypot(v.x, v.y, v.z), 1, 1e-12));
}

console.log('decimal coordinate parsing');
ok('comma pair', (() => { const r = parseQuery('35.68, 139.69'); return r && near(r.lat, 35.68) && near(r.lon, 139.69); })());
ok('space pair', (() => { const r = parseQuery('-33.87 151.21'); return r && near(r.lat, -33.87) && near(r.lon, 151.21); })());
ok('negative both', (() => { const r = parseQuery('-22.9068, -43.1729'); return r && near(r.lat, -22.9068); })());
ok('lat out of range', parseQuery('120, 30') === null);
ok('lon out of range', parseQuery('30, 200') === null);
ok('names custom target', (() => { const r = parseQuery('0, 0'); return r && r.name === 'Custom target'; })());
ok('names nearby city', (() => { const r = parseQuery('35.68, 139.70'); return r && r.name === 'Tokyo'; })(),
   JSON.stringify(parseQuery('35.68, 139.70')));

console.log('DMS parsing');
ok('london dms', (() => {
  const r = parseQuery("51°30'N 0°7'W");
  return r && near(r.lat, 51.5, 1e-9) && near(r.lon, -7 / 60, 1e-9);
})(), JSON.stringify(parseQuery("51°30'N 0°7'W")));
ok('lon first', (() => {
  const r = parseQuery("139°41'E 35°41'N");
  return r && near(r.lat, 35 + 41 / 60, 1e-9) && near(r.lon, 139 + 41 / 60, 1e-9);
})(), JSON.stringify(parseQuery("139°41'E 35°41'N")));
ok('with seconds', (() => {
  const r = parseQuery(`40°42'46"N 74°0'22"W`);
  return r && near(r.lat, 40 + 42 / 60 + 46 / 3600, 1e-9);
})());
ok('south/west negative', (() => {
  const r = parseQuery("33°52'S 151°12'E");
  return r && r.lat < 0 && r.lon > 0;
})());

console.log('place name lookup');
ok('exact', parseQuery('Tokyo')?.name === 'Tokyo');
ok('case insensitive', parseQuery('tOkYo')?.name === 'Tokyo');
ok('prefix', parseQuery('San Fran')?.name === 'San Francisco');
ok('multiword', parseQuery('New York')?.name === 'New York');
ok('unknown -> null', parseQuery('Zzzzqqq') === null);
ok('empty -> null', parseQuery('') === null);
ok('whitespace -> null', parseQuery('   ') === null);
ok('null-safe', parseQuery(null) === null);

console.log('suggestion ranking');
ok('exact ranks first', findPlaces('Delhi', 5)[0].name === 'Delhi');
ok('prefix beats contains', findPlaces('Man', 5)[0].name === 'Manila',
   findPlaces('Man', 5).map((p) => p.name).join(','));
ok('limit respected', findPlaces('a', 4).length <= 4);
ok('no query -> empty', findPlaces('', 5).length === 0);

console.log('reverse lookup');
ok('on a city', nearestPlace(35.68, 139.70) === 'Tokyo');
ok('mid-ocean is null', nearestPlace(-30, -140) === null, String(nearestPlace(-30, -140)));
ok('antimeridian safe', typeof nearestPlace(0, 179.9) !== 'undefined');

console.log('formatting');
ok('north', fmtLat(51.5074) === '51.51°N');
ok('south', fmtLat(-33.8688) === '33.87°S');
ok('east', fmtLon(139.6503) === '139.65°E');
ok('west', fmtLon(-0.1278) === '0.13°W');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);

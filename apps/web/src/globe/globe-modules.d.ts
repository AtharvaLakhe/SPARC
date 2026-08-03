/* Types for the assets the globe borrows from orbital-website/.
 *
 * `shaders.js` is deliberately plain JavaScript — it is shared with a
 * build-free ES-module page, so it cannot become TypeScript without breaking
 * that. Declaring its surface here is cheaper than turning on allowJs for one
 * file, and it keeps the shared shader source in exactly one place. */

declare module '@globe/places.js' {
  export interface Place { name: string; country: string; lat: number; lon: number }
  export const PLACES: Place[];
  export function findPlaces(query: string, limit?: number): Place[];
  export function nearestPlace(lat: number, lon: number): string | null;
}

declare module '@globe/geo.js' {
  export function latLonToVec3(lat: number, lon: number, radius?: number): { x: number; y: number; z: number };
  export function vec3ToLatLon(v: { x: number; y: number; z: number }): { lat: number; lon: number };
  export function parseQuery(raw: string): { lat: number; lon: number; name: string } | null;
  export function fmtLat(lat: number): string;
  export function fmtLon(lon: number): string;
}

declare module '@globe/shaders.js' {
  /** Rayleigh + Mie + ozone single-scattering integrator, raymarched. */
  export const ATMOSPHERE_GLSL: string;
  /** Value noise and fbm. */
  export const NOISE_GLSL: string;
  /** sRGB decode helper. */
  export const SRGB_GLSL: string;
}

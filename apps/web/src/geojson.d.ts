declare module '*.geojson' {
  const value: { type: string; coordinates?: unknown; [key: string]: unknown };
  export default value;
}
declare module '*.geojson?raw' {
  const value: string;
  export default value;
}

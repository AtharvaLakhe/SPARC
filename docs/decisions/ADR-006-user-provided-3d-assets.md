# ADR-006: Gate and isolate user-provided 3D assets

- **Status:** Accepted; runtime selection deferred
- **Date:** 2026-08-02
- **Decision owners:** Shared; user owns source assets
- **Applies to:** User-provided Earth and satellite models and any future 3D showcase

## Context

The user will later supply an Earth model and a satellite model. Neither file exists in the current repository, so format, licensing, texture references, animation, coordinate system, size, performance and runtime compatibility cannot be confirmed.

The core innovation is the conversion of satellite observations into understandable local proxy indicators. Making unknown 3D files a dependency of region selection or analytics would create a high-risk critical path and misplace the product's value.

## Decision drivers

- Respect user asset ownership and restrictions.
- Do not invent compatibility or licensing facts.
- Preserve P0 analytics under asset, WebGL, performance or accessibility failure.
- Avoid selecting a heavy runtime before evidence exists.
- Support progressive enhancement and reduced motion.
- Keep the offline bundle self-contained.

## Decision

1. Represent the assets only by neutral placeholders until they are supplied:

   ```text
   assets/models/earth/[USER_PROVIDED_EARTH_MODEL]
   assets/models/satellite/[USER_PROVIDED_SATELLITE_MODEL]
   ```

2. Do not search for, download, purchase, generate or recommend replacement Earth/satellite models.
3. Do not assume GLB, glTF, FBX, OBJ or another format. Those are inspection candidates only.
4. Do not select or install CesiumJS, Three.js, React Three Fiber, Babylon.js or another 3D runtime until the actual formats, extensions, coordinate expectations and performance are inspected in a bounded spike.
5. Classify 3D as an optional showcase/landing experience or region-selection transition, never as an analytical dependency.
6. Lazy-load the selected runtime and model only after the user enters/requests the showcase. The core dashboard must require zero model/runtime bytes.
7. Provide a non-animated/static 3D path for reduced motion and a complete 2D poster/dashboard path for unsupported WebGL, context loss, load error, timeout or device budget failure.
8. Any conversion/optimization modifies a user asset. Preserve the original, obtain explicit approval, record tool/version/settings, and hash both source and derivative.
9. Do not upload assets to third-party conversion/hosting services without explicit user permission.

## Inspection gate

No implementation branch may enable 3D in the release until it records:

- asset ownership and public redistribution permission;
- actual format/version and all external references;
- byte size and SHA-256;
- mesh/vertex/material/draw-call counts;
- texture formats, dimensions, color space, compression and memory estimate;
- axes, handedness, units, pivot/origin, bounds and any georeferencing;
- animation clips, rigs, morph targets and intended behavior;
- tested runtime/loader and browser/device matrix;
- transfer, parse, render and frame performance;
- reduced-motion, keyboard, screen-reader, error and 2D fallback results; and
- offline packaging/manifest entries.

## Options considered

| Option | Advantages | Limitations | Decision |
|---|---|---|---|
| Select CesiumJS now | Strong geospatial globe/3D Tiles engine | Asset may be decorative/non-georeferenced/unsupported; large premature dependency | Deferred pending evidence |
| Select Three.js/React Three Fiber now | Broad general-purpose 3D ecosystem | Asset extensions/materials/performance unknown; runtime choice could be wrong | Deferred pending evidence |
| Convert every file to GLB immediately | Often simplifies browser packaging | Conversion may lose materials/animation, change user work and needs tool/license approval | Rejected until inspected/approved |
| Find a replacement asset | Removes compatibility delay | Explicitly violates user restriction and adds licensing risk | Rejected |
| Isolate, inspect, then select or omit | Evidence-based, protects dashboard and ownership | 3D may be absent from P0 | **Selected** |

## Consequences

### Positive

- Unknown assets cannot block the core prototype.
- Runtime and conversion decisions are based on real file evidence.
- Offline, WebGL and accessibility fallbacks are designed before visual polish.
- User ownership and model integrity are preserved.

### Negative and trade-offs

- A 3D showcase may not be ready until Day 4 or a later phase.
- The frontend cannot finalize scene/camera/material work before files arrive.
- Multiple loader spikes may be required if the supplied format is inefficient or unusual.
- A 2D fallback/poster must be prepared even if 3D succeeds.

## Performance and accessibility constraints

- No model or 3D runtime in the critical dashboard route/chunk.
- Numeric asset/frame budgets are set only after measurement on the presentation laptop and agreed low-end mobile device.
- If the model cannot meet the approved budget without an unauthorized modification, release uses the 2D fallback.
- Provide a visible skip/reset/pause path, keyboard-operable equivalent controls and text description.
- Honor `prefers-reduced-motion`; no forced orbit, parallax, camera travel or autoplay for users requesting reduction.
- Model load/error status is announced accessibly without trapping focus.

## Security and integrity

- Treat binaries and referenced resources as untrusted until validated/scanned.
- Reject traversal and unexpected remote/data URI references unless reviewed.
- Bound geometry, texture and animation complexity to avoid memory/resource exhaustion.
- Do not render asset metadata as unsanitized HTML.
- Serve accepted assets from the same local/approved origin and list them in the offline manifest.

## Reversal conditions

This decision becomes implementation-ready only when both files pass the inspection gate. A runtime selection is a new reviewed decision/addendum. If either file is incompatible, unlicensed for public use, too large or inaccessible, omit it and retain the 2D experience; do not source a substitute.

## Sources

Official standards were accessed on 2026-08-02.

- [glTF 2.0 Specification — Khronos Group](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html). Candidate glTF structure, coordinate conventions, materials, buffers and animation.
- [WebGL Specification — Khronos Group](https://registry.khronos.org/webgl/specs/latest/1.0/). Graphics-context behavior and context loss.
- [Media Queries Level 5: `prefers-reduced-motion` — W3C](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion). Standard user motion preference.
- [WCAG 2.2 — W3C, 2023-10-05](https://www.w3.org/TR/WCAG22/). Keyboard, animation, focus, text alternative and status requirements.


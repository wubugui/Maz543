# Fitted barrel-axis motion review, not vehicle acceptance

Use `?asset-review=cab-va180-axis-v1` in the development ordinary viewport. This
uses the exact existing cab-va180-v1 GLB and changes only the four copied door
pivot translations under their existing rotations. `cab-va180-v1` keeps the old
motion for comparison. No native .blend, GLB geometry, production selector or
render-worker default is replaced. All16 vehicle gates remain OPEN.

## Actual checks

- `node scripts/verify-barrel-axis-pose-binding.mjs`: actual source model.update,
  actual binding-loop statement, delivered GLB transforms and decoded geometry
- `node scripts/verify-va180-pose-binding.mjs`: existing721-state steering check
- `node scripts/verify-left-driver-pose-binding.mjs`: existing480-state check
- `MAZ_REVIEW_REPORT_DIR=work/cloud-barrel-axis-web-20261001 node scripts/verify-review-asset-selection.mjs`
- focused oxlint of all3changed code files, TypeScript and production build

Existing legacy tests write their historical result paths. Their fresh results
were copied here and those older paths restored byte-for-byte from HEAD. The
first VA180 run could not write because its sparse-recovery output directory did
not exist; it was created before the successful unchanged test rerun.

## Retained failed metric

Attempt01 required both native barrel box center and dimension agreement within
20um and found0components. Attempts02–05 inspected the real encoded components,
quantization metadata and unique-position centroid without accepting that failed
box/size test. The final replay explicitly still asserts0matches for the old box
filter. Draco POSITION metadata is14bit over1.2699999809265137m, a77.519um grid.
The inherited box-size error reaches54.479um and is not declared transport-pass.

The native evaluated barrel has192vertices/380triangles. Decoded normal seams
split it into368indices but exactly192unique positions/380triangles. Thus their
192-position mean is the comparable geometric centroid, not the AABB midpoint
and not a physical mass centroid. Native-to-decoded centroid differences reach
8.207um; the unchanged measured native axis gives12.509um maximum sampled center
drift. The original20um motion gate is unchanged. No native interval or factory
acceptance is inferred from this distinction.

No browser or renderer was used for these checks. Component poses/matrices are
not screenshots, UI/loader tests, a full-vehicle assembly audit or clearance.

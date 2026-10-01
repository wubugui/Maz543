# Cab-panel installation trials: not accepted

These two independent native trials place the source-traced panel study in the
left-driver-side Master candidate. Neither trial is suitable for promotion.
All 16 whole-vehicle gates remain OPEN. The original production files and the
prior left-driver candidate are unchanged.

## What was replaced and retained

The earlier cab prototype had seven generic gauges in each cab. The study has
14 left instrument positions and a distinct right auxiliary panel, following
1977 Fig101/102 with the documented caption conflicts and fitted dimensions.

The old 14 gauge-face, bezel and pointer proxies are retained as three hidden
editable objects. The two old solid dashboard blocks were separated from the
merged green mesh using Blender's native Separate operation. Their 1,800
vertices are retained in a fourth hidden object. The seat bases sharing that
mesh remain visible and unchanged. Original face-corner coordinates, authored
UVs and material indices remain accounted for across the separated objects.
The builder checks 7,708 other original meshes for unchanged authored geometry,
UVs, transforms, parents and object render flags. It does not claim a complete
shader or mechanical audit from that comparison.

No part was shrunk, and no wall, seat, steering wheel or column was moved to
force a fit. The original standalone study is also unchanged. The candidate
adds `review_vehicle_fit` metadata; original standalone-study properties remain
as source metadata. This is inclusion in an unaccepted review vehicle only.

## Retained failed trials

- `iteration-01`: panel plane at the centre of the old 0.25 m deep dashboard
  block, preserving the old block's nominal tilt. Fresh readback passes 247
  finite closed positive-volume solids and 57 plate openings, but finds the
  left sheet and one lower control intersecting the inner wall: 2 object pairs
  and 733 triangle pairs. The first reader returned 0 for its structure checks
  while explicitly reporting the rest interference as OPEN. Its exact reader
  is retained. That exit status did not accept the installation
- `iteration-02`: panel plane moved to the old block's driver-facing +X face,
  using its existing 0.125 m half-depth and the same tilt. This is a correction
  to the inherited proxy anchor, not a new factory datum. The same 247 solids
  and 57 openings pass structure checks. The inner-wall intersections remain,
  and parts of the left sheet and A4/A5 instruments intersect the steering
  wheel. There are 15 new-part-to-existing-part surface-intersection pairs.
  The stricter reader records this failure and exits 2

The tests only compare actual rest-pose triangle surfaces. No-hit pairs are not
a complete containment, clearance, swept-volume, mounting or operation proof.
The legacy steering-column/seat interference is separate and was not fixed.
The preliminary ten-control diagnostic is in
`../cloud-left-driver-rest-audit-20261001/`.

## Why fitting is still open

The flat study reproduces an undimensioned projected drawing, including an
unresolved lower return and unknown mounting attitude. The original cab
interior, steering and seat positions also lack completed factory calibration.
Neither arbitrary shrinking nor further coordinate adjustments establish the
correct installation. The next geometry change needs a defensible panel/cab
datum or a source-supported correction to the interior structure.

The two `.build.json` and `.readback.json` files identify exact source and output
hashes. `iteration-02/render-provenance.json` identifies two actual Cycles cabin
images of the failed second trial. Both images were inspected. They retain all
current candidate geometry; no further wall or steering parts were hidden. The earlier left-driver image is a valid
same-camera baseline; a plausible picture cannot override the collision result.

## Reproduction

Run `build-cab-panel-fit-candidate.py` with the earlier left-driver Master as
`--input` and a fresh output path. `--anchor body-centre` reproduces the first
placement; `--anchor rear-face` reproduces the second. Then run
`readback-cab-panel-fit-candidate.py --input` on the saved file in a new verified
Blender 4.5.13 process. Keep failed outputs. Neither command writes a production
path, exports a browser asset or publishes a website.

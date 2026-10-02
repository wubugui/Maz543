# Existing lower-step datum: rejected

The existing +Y lower step cannot be adopted as a verified installation baseline.
At the saved closed frame0 state, its native curve and last tread bar have strict
noncoplanar triangle crossings with the actual first tyre geometry. No model was
changed or saved, and no replacement dimensions or factory hardpoints were made.
All 16 whole-vehicle gates remain OPEN. The saved door-control candidate remains
LOCAL_ONLY_LFS_BLOCKED.

## Positive evidence

`attempt-01/native/crossing-witnesses.json` retains six selected witnesses. Each
contains both triangles' world coordinates and evaluated vertex indices, shared
segment endpoints and midpoint, barycentric coordinates, plane residuals, strict
straddling margins and distances to triangle edges. They establish intersecting
surfaces without assuming that a wheel component is a watertight physical solid.

| Step object | Wheel object | Triangle indices (step/wheel) | Shared segment | Minimum midpoint-to-edge margin |
|---|---|---:|---:|---:|
| BL_Cab_-1_step | BL_Tyre_0_VI203_profile | 62 / 873 | 22.589869 mm | 5.804031 mm |
| BL_Cab_-1_step | BL_Tyre_0_vent_-1_16 | 54 / 0 | 1.306645 mm | 0.653006 mm |
| BL_Cab_-1_step | BL_Tyre_0_vent_-1_17 | 57 / 4 | 0.714391 mm | 0.352568 mm |
| BL_Cab_-1_step | BL_Tyre_0_vent_-1_18 | 61 / 9 | 2.125419 mm | 0.666506 mm |
| BL_Step_-1_19 | BL_Tyre_0_VI203_profile | 177 / 1141 | 10.784259 mm | 5.205114 mm |
| BL_Step_-1_19 | BL_Tyre_0_mould_ring_-1_0.635 | 185 / 933 | 1.615632 mm | 0.803327 mm |

The floating check found 188 positive triangle pairs across these six object
pairs. This count is not an intrusion volume or penetration depth. Four remaining
object pairs produced no strict positive witness; they are explicitly **not
clearance passes**. The predicate excludes coplanar, edge-only, nearly degenerate
and containment cases. The largest residual among the six retained witnesses is
6.542e-15 m; minimum barycentric coordinate is 0.0188773, and minimum normal-cross
sine is 0.686319. Method thresholds are printed in the native report; they were
not loosened to obtain results.

An additional lightweight check, `verify-exact-witnesses.py`, uses exact rational
arithmetic on each triangle's recorded binary64 coordinates. It independently
constructs the two plane-section segments and verifies identical exact endpoints,
positive interval length, strictly positive barycentric coordinates, and exactly
zero plane/reconstruction residuals. All six passed in
`exact-witness-verification.json`. This arithmetic check is not another native
model read; native identity is covered by the evaluated signatures below.

## Scope and reused inventory

Broadphase reuses the already-published full inventory:

- Repository: `testcar/work/cloud-step-installation-fit-20261001/publication`
- Restored record: `attempt-05/native/all-geometry-inventory.json`
- SHA-256: `7929cddd99fbdeb4a38acbd69ea98133bf14a4a8fdf0db56ecc8a6161d9f2221`
- 10,353 original/instance entries, including 1,009 previously established exact
  duplicate source placements; none of that inventory is republished here

The wheel selection is precisely the inventory entries whose **recorded direct
parent is `wheels_pivot_002`**. All selected source names match `BL_Tyre_0_`,
`BL_Rim_0_`, `BL_Hub_0_` or `BL_Wheel_0_`. This is an existing scene grouping of
186 distinct source objects plus 89 evaluated instance entries, **not an assertion
that it is a complete factory wheel assembly**. Different source objects are
never merged, even if their geometry coincides. The preserved all-scene overlap
name list provides a check against silently losing other broadphase candidates;
body, fender and Boolean-tool checks are outside this wheel-datum item.

The published snapshot identifies all 89 wheel instances as exact duplicates of
their same source placements. That is reused historical evidence, not a fresh
89-instance geometry check. This run freshly evaluated 33 sources plus six
relevant instances (the step curve, two mould rings and three vents). Each of the
39 evaluations exactly matched the published float64 world-position/int32
triangle-index signature, counts and bounds. Instance descriptors, matrices,
persistent IDs and duplicate mappings are retained in the selected-geometry
report. All six fresh instances also matched their distinct named source. The
other 84 wheel instances were not freshly evaluated.

The 21 step sources versus 186 wheel sources produce 3,906 possible pairs; 10
have overlapping AABBs in the reused inventory. Only those 10 underwent triangle
checks. The native run also freshly verifies tread-block, rim and hub geometry
for datum comparison; it does not claim a new full-scene geometry inventory.

## Datums and conclusion

The native curve is an uncapped five-point POLY path with 23 mm bevel depth.
Its centerline runs through (-4.80,1.48,1.12), (-4.80,1.48,0.95),
(-4.70,1.52,0.90), (-3.63,1.52,0.90), (-3.55,1.48,1.13) metres
(rounded here; exact stored values in `existing-datums.json`). It is an inherited
authoring curve, not a certified physical support structure.

The 20 bars span X -4.692500 to -3.679500 m, Y 1.460000 to 1.580000 m,
Z 0.923500 to 0.932500 m. The profile's forward X bound is -3.809000 m;
the tread-block bound is -3.833979 m. The curve's rear bound reaches 280.627 mm
behind the profile's forward bound, and the last bar reaches 129.500 mm behind
it. These are longitudinal overlaps, **not penetration depths**. The strict
triangle witnesses, not these bounding values, reject the installation baseline.

The old shorter step remains useful only as a record of inherited model
coordinates. Its length, height, path and bar spacing must not be promoted to
validated installation dimensions. The previous 2.2 m layout also remains
installation FAIL. A later refit needs independently justified lower-step
placement against the actual tyre and source references. This item did not
choose replacement dimensions, certify attachments, move a wheel or remove an
original part.

## Native execution and preservation

One official Blender 4.5.13 run used background/factory-startup/disable-autoexec,
CPU1 with a 120-second hard subprocess deadline. Exit0 in 28.610721 seconds,
peak child RSS 2,010,632 KiB. This is recorded elapsed time, not a performance
benchmark. No render or special view was needed; no failed native run occurred.

The 10,434 original object identities and listed parent/data/matrix/visibility/
selection/collection/modifier-state fields compared exactly before/after. All
33 selected source geometry signatures were rechecked at the end. No original
objects were hidden, deleted, moved or saved. No whole-scene mesh preservation
claim is made beyond the listed state fields and selected evaluated geometry.
Source, candidate, inventory and frozen executed scripts have unchanged hashes.

- Immutable source: `8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70`
- Saved candidate: `3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f`
- Executed native script: `1118b30ba5d90ffa3793aa530b6356c7344643accc40824143f2db9168f3af79`
- Frozen runner: `6c860b9d6367d9b62c43a2c372659444e44fe3cecc592abbdf8d5d5332a37355`

## Explicit-path recovery and replay

The native runner takes all inputs explicitly. The inventory can be restored
with the published `testcar/scripts/pack-step-installation-evidence.py` restore
mode; verify its restored SHA before passing it. The candidate must be the exact
local saved candidate above. If it is lost while still LFS-blocked, reconstruction
and fresh verification are necessary; do not call a rebuild the same saved bytes.

```bash
python run-existing-step-datum.py \
  --blender /absolute/path/to/blender-4.5.13-linux-x64/blender \
  --script /absolute/path/to/check-existing-step-datum.py \
  --candidate /absolute/path/to/MAZ543A_Native_Barrel_Axis_Controls.blend \
  --original /absolute/path/to/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend \
  --inventory /absolute/path/to/attempt-05/native/all-geometry-inventory.json \
  --out /absolute/path/to/new-unique-run-directory

python verify-exact-witnesses.py \
  --witnesses /absolute/path/to/attempt-01/native/crossing-witnesses.json \
  --out /absolute/path/to/new-exact-check.json
```

Every native run writes frozen script/runner copies, a process terminal record,
input start/end hashes and a log. Failure/timeout emits a FAILURE record. The
native report is preserved as produced; later exact arithmetic and scope notes
are separate evidence.

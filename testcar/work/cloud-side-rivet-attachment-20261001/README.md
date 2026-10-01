# Retained side-head native attachment trial

This is a reproducible, **in-memory fitted installation correction**, not a
published `.blend`, a new browser GLB, factory-dimension acceptance or a vehicle
collision pass. The original 8e962d6… Master remains byte-identical.

## Actual change

Each original side rivet mesh contains75 retained head components. Complete
8-corner base footprints were projected onto the actual outer-plane triangles
of the named monocoque. Seventy per side pass numerical coverage; each original
24-vertex/38-triangle head is translated inward11.999964714mm using Blender's
native edit-mode Translate operator. No head shape, X/Z spacing, topology, UV,
material assignment, object transform or parent is rebuilt. All1120 base-ring
vertices read back exactly on the measured original skin plane. This fixes the
visible stand-off for this limited140-head set, not manufacturer fastener design.

The remaining10 heads are untouched: four footprints cross original bevels and
six project through rear-door openings. The latter retain their existing closed
surface contacts. Four original column-like components are also unchanged.

## Verification

- Source, four input reports/reference and coverage helper SHA256 are pinned
- Coverage uses binary64 convex polygon subtraction, retaining uncovered regions;
  summed triangle area alone cannot pass. Duplicate/overlapping support rejects
- Area tolerance1e-14m², at most64 local triangles/4096 uncovered fragments per
  call. Actual worst local triangle count27. Passed footprint areas are about
  0.000181m²; maximum reported uncovered residual6.613e-20m². These numerical
  residuals are not an interval/exact arithmetic or manufacturing proof
- Both sides are assessed and written before any edit. All diagnosed70 per side
  must qualify; no silent partial edit. Current excluded five per side each fail
  actual full-area coverage, independently of the prior finite-sample category
- 3360 moved vertices read back with zero translation error. All240 untouched
  head vertices remain exact. Both target topology/UV/material signatures match
-7468 other native mesh position/topology/material/UV signatures remain exact;
 10434 object transforms, parents, data identities and visibility states match
-44 closed-door evaluated vertex arrays and triangle indices remain exact
-88 door-versus-target object comparisons preserve104 contact triangle pairs;
 all6 prior closed object pairs and190 prior contact triangle pairs remain exact
- No new native asset save, production/runtime change or LFS entity publication

Native mesh signatures intentionally do not claim every custom attribute,
computed-normal field, modifier configuration or scene RNA field was compared.
The transform operation's geometric result and listed preservation fields are
verified. No whole-angle motion or all-body clearance is inferred.

Final pinned/old-PASS-invalidation replay: Blender4.5.13, one thread,23.333s,
exit0, peak1921356KiB; not an isolated performance benchmark. The process record
binds the exact script SHA and report SHA. First exploratory successful output is
retained separately; it is not a second model asset.

## Coverage controls

`test-convex-coverage.py`:20 test methods, including300 deterministic random
checks. `audit-convex-coverage-oracle.py`:55 independent cases,42 compared with an
exact rational vertical-slab union oracle. Tests reject holes/notches which pass
all nine point probes, duplicate support masking holes, malformed ordering,
subnormal arithmetic and aggregate overflow. The initial helper audit found and
fixed subnormal, cyclic-duplicate and aggregate-overflow weaknesses before this
native replay. Regression tests retain them; no earlier helper was used to edit.

## Reproduce

From `testcar`, after materializing and verifying the published native source:

    python scripts/test-convex-coverage.py
    python scripts/audit-convex-coverage-oracle.py
    blender --background --factory-startup --disable-autoexec --threads 1 \
      --python-exit-code 1 --python /absolute/path/testcar/scripts/trial-side-rivet-native-attachment.py

Each invocation replaces any old PASS with IN_PROGRESS before validation; a failure cannot leave a current PASS. Accept only a final report and matching successful process evidence.

This leaves the trial only in the running Blender process. It never saves over
any source or claims an unuploaded output. The qualitative primary photo sources
and batch/metric limits remain in
`reference/cab-sill-step-rivet-source-20261001.json`. Photos show surface-mounted
heads around fixed skin/sill areas; they do not establish this count, geometry,
12mm correction or1977/543A batch. The correction distance is derived from the
existing model's own measured support plane. Shanks, holes and fastening strength
remain unmodeled/unverified. All16 whole-vehicle gates remain OPEN.

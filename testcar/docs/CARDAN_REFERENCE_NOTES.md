# Fan-drive Cardan reconstruction

This is an independent inspection component, not an accepted vehicle installation.
It is available under Cooling -> Inspect Cardan in the browser and as
`outputs/MAZ543A_Cardan_Master.blend`. It has 213 authored meshes and 190 moving
nodes. These counts describe this reconstruction, not the factory bill of materials.

## Sources actually inspected

- [Original 1973 technical description, cooling section](https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/007.htm)
  describes two open Cardan joints, a male splined lower fork, female upper fork,
  needle bearings, sealing rings and grease nipples. No length is provided there.
- [543-1308586-A exploded parts drawing](https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/val_kardannyj_543_1308586_a-82),
  local `work/reference-docs/543-cardan-exploded.gif`, shows the flange forks,
  cross, caps/circlips and separate sliding forks. Listed numbers include
  543-1308606, 408-2201026-02, 400-2201043, 704902-K6,
  543-1308603-B and 543-1308598-B. This catalog includes later variants;
  compatibility with a specific 1973 vehicle is not established.
- [MCB Universal Joint Catalogue, version 2.0 (2017)](https://mcbbearings.com/wp-content/uploads/2024/02/MCB-Univeral-Joint-Catalog.pdf),
  PDF pages 12 and 29 (printed pages 7 and 24), downloaded completely and
  rendered with Poppler. `MCB-grooved-cross-definition.png` shows D, O and L;
  `MCB-408-dimensions.png` identifies 400/408-2201025 as D=28, O=42.5,
  L=73 mm, with 704902K6C10 bearings. This supports the 408-family envelope,
  not an unproven identity with the original -2201026-02 cross.

No accepted individual photograph or dimensioned manufacturing drawing of the
complete 543-1308586-A shaft has been obtained. Generic part images are not
treated as measured original geometry.

### References inside Blender

All 213 mechanism meshes have individual evidence properties: referencePartNumber,
sourceSupports, dimensionStatus and individualPhotoStatus. The complete index is
embedded as CARDAN_PART_EVIDENCE.json and exported to outputs/cardan-parts-register.json.
Needles and seals explicitly retain fitted dimensions; the 408-family envelope is
not attributed to unrelated fork, spline or grease-nipple dimensions.

The native master packs the Cardan exploded drawing (lossless GIF-to-PNG copy),
the 1973 Fig.30 sheet and the two MCB catalog sheets.
Open them in an Image Editor or enable CARDAN_REFERENCE_SHEETS in the Outliner.
This collection is hidden by default, excluded from renders and outside the
mechanism/export hierarchy. Display scale is arbitrary; these are source documents,
not calibrated photo planes. READ_ME_REFERENCES.txt explains navigation. This is a
native authoring aid; the existing web GLB geometry and motion remain unchanged.

Further exact-part web/image searches on 2026-09-06 did not yield an accepted
543-1308586-A or 543-1308210 individual photo or a 543-1308010 dimension drawing.
Search results showing ZIL shafts, GAZ-34039 reducers and KAMAZ couplings were
rejected as different equipment. This is a search result, not proof such photos
do not exist.

## Native construction

Each end has a continuous fork with rounded bearing eyes, tapered arms,
drilled four-hole flange where applicable, and a separate cross. The cross
has machined trunnions and intersecting grease galleries. Each of eight cups
has a closed bottom, inner race, seal recess, external retaining groove and
open retaining ring. The two sliding forks share a fitted 12-tooth straight
spline profile with separate tooth lands, roots and flank surfaces.

The model uses a 28 mm cup outside diameter, 73 mm cap-to-cap span and
42.5 mm groove reference span. The 16 mm trunnions, 2.5 x 14 mm needles,
22 rollers per cup, fork profiles, 74 mm flange PCD, 100 mm flange OD,
clearances, fits, machining radii, grease holes and surface finish are fitted.
Needle count and internal bearing dimensions have not been catalog-confirmed.
No manufacturing tolerance or load rating is asserted.

The fitted cross-centre spacing is 230-270 mm. Male splines end 170 mm from
the first cross; the female socket reaches 125 mm back from the second.
The commanded range retains 25-65 mm overlap and at least 16 mm clearance
to the female fork bridge. This range belongs to this inspection mechanism,
not to a verified MAZ stroke specification.

## Kinematic constraints

`lib/cardan.ts` solves the two cross constraints as orthogonal unit vectors.
The intermediate trunnion is perpendicular to both the input trunnion and
the intermediate shaft. The second cross derives the output trunnion from
that same intermediate trunnion. The sliding spline permits translation
while preserving the phase of the two intermediate forks.

The inspection configuration has parallel end axes and equal joint angles.
Its intermediate angular-speed ratio varies from cos(beta) to 1/cos(beta).
At 30 degrees this is 0.8660-1.1547; the correctly phased second joint restores
equal input/output rotation. The browser allows 0-30 degrees and 0-40 mm
extension. Its input follows the current fitted lower-drive ratio, 32:20,
using the accumulated crank angle from the starting solver.

For each needle set, the cross-to-yoke twist drives the virtual roller carrier
and each needle's own rotation. With outer race stationary relative to the
fork, inner race radius R-r and outer radius R+r, the two contact surface
velocities match. The carrier is only a coordinate frame: this full-complement
reconstruction does not invent a physical cage.

This model has geometric rolling constraints. It does not yet solve bearing
loads, elastic contact, lubrication flow, spline friction, shaft bending,
wear or a measured Cardan inertia. It is not inserted into the vehicle's
torque path. Current vehicle fan/clutch dynamics retain their documented
fitted net ratio and lumped loads.

## Checks and known installation conflict

`prepare-cardan.mjs` exports the existing 601-frame guided start/coast sequence.
`blender-cardan.py` constructs the native module and exports its independent GLB.
`verify-cardan.mjs` checks 776 angle/stroke states, phase closure, rolling
velocities, all 190 GLB node bindings and glTF validation.
`verify-cardan-native.py` checks the actual native pose tracks, all four
cap-pair envelopes and 200 moving configurations for opposing-fork,
fork/cross and male/female-spline surface interference. The first version
failed on spline end-cap triangulation; corrected annular topology passes.
The verifier renders assembled and internal inspection images.

`audit-cooling-installation.py` initially found each fan shroud intersecting its
adjacent cab inner wall, with 32 triangle pairs per side. The subsequent
photo-guided lower cab relief removes those surface crossings at frame zero;
see CAB_PHOTO_FIT_NOTES.md for its fitted dimensions and remaining limits.
The installed placeholders still do not connect
the rebuilt gearbox flange centres. The current gearbox/fan placement cannot
be accepted, and it has not been silently changed to fit this independent rig.
Factory fan-pack dimensions and installed shaft axes remain needed to resolve
that conflict. All full-vehicle acceptance gates remain OPEN.

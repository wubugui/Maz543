# MAZ-543A cooling reconstruction — 2026-09-06

2026-09-08: return springs now use circular-wire, constant-centreline-length
morph geometry synchronized with the native masters and browser. A dedicated
left-spring view exposes the whole coil. See [continuation and evidence](CONTINUATION_20260908.md).
The installed Cardan conflict remains OPEN.

This is an incomplete source-guided reconstruction, not factory CAD or a
validated cooling performance model. No complete-vehicle acceptance gate closes.

## Sources actually inspected

- [1973 original cooling chapter, figures 27–31](https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/007.htm).
  Forced closed water circuit; two twelve-blade aluminium fans; three-pass
  radiator; manual shutters and electromagnetic fan clutches. The pump feeds
  the two block jackets, then heads, cooled exhaust manifolds and hot header.
  Radiator, cabin heaters and compressor return to the inlet circuit.
- Original figure 30 scan: `work/reference-docs/MAZ1973-0575.jpg`, visually
  inspected. Lower bevel gearbox has eight mounting bolts, crank torsion input,
  two output shafts, ball bearings, oil pump, strainer and supply/return lines.
  Lower gearbox now has separate fitted casting, shafts, gears and bearings.
  Upper local gears and bearing cups have also been rebuilt; Cardan geometry
  and installed transmission closure remain incomplete.
- Original figure 31 scan: `work/reference-docs/MAZ1973-0582.jpg`, visually
  inspected. Upper gearbox and electromagnetic fan-clutch section.
- [1977 technical description, printed pp.79–80](https://djvu.online/file/zjMdLY3MFjmTL).
  Fan and magnetic yoke ride on two needle bearings. Splined flange and armature
  follow the output shaft. A textolite washer insulates the slip ring; two
  brushes feed it and an end brush returns through the shaft. The coil pulls
  the fan assembly into a cast-iron friction ring; a spring separates it on
  deenergization. The stated energized magnetic gap is 0.1–1.0 mm. Manual
  mechanical locking is described but is not yet operable in this model.
- [1973 vehicle layout chapter](https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/002.htm).
  Engine is between the two cabs; common water/oil radiator block is ahead of it.
  Engine holder moved from x=-2.05 to x=-4.05 m to correct that relationship.
  These installation coordinates remain fitted; complete cab/engine clearance,
  mounts and rear drivetrain connection have not been accepted.

- [543-1308509 actual part photograph](https://detal-potok.ru/product/reduktor-privoda-ventilyatora-543-1308509-nizhnij-na-maz-543/).
  Inspected the linked 1440 px product image, archived locally as
  `work/reference-docs/543-1308509-lower-photo.png`. It shows the forked casting,
  inclined output cups, flange fasteners and external oil pump. Seller identity
  is not a measured serial-number verification. Black storage enamel appearance
  was reconstructed; it is not evidence of original factory paint. Contradictory
  seller dimensions and masses were **not** used.
- [Lower gearbox original parts diagram, catalog mirror](https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/reduktor_nizhnij__privod_543_1308509-86).
  Inspected `work/reference-docs/543-lower-exploded.gif` and the actual part rows.
  Input 310A bearings, output 307A bearings, 44×65 seal, hollow leading shaft,
  torsion and separate bearing cups are identified. This is a later MAZ-543
  (7310) catalog: revision compatibility with 1973 remains to be checked.
- [GPZ-1 bearing dimension table](https://gpz1.ru/kupit-podshipniki-gpz-1/podshipniki-sharikovye-radialnye-odnoriadnye/).
  Nominal 307 series envelope: 35×80×21 mm; 310 series: 50×110×27 mm.
  Ball count, race grooves, cage and fits are **not** established by that table.
- [543-1308714 oil pump exploded parts diagram](https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/nasos_543_1308714-87).
  Inspected `work/reference-docs/543-oil-pump-exploded.gif`: separate body/cover,
  two gears, bushings, coupling and ball/spring relief valve. Relief-valve
  geometry and hydraulic operation still need implementation.

An individual verified photograph is still missing for many cooling parts.
Exploded diagrams establish assembly topology, not complete measured geometry.

The native cooling master now packs nine supporting image sheets and indexes
all 1,237 authored mesh/curve objects in `COOLING_PART_EVIDENCE.json`. The single
assembled lower-drive photograph is assigned only to 49 visible external
features; this is not 49 isolated-part photographs. The remaining references
are manual text/sections and catalog diagrams. Per-object custom properties
distinguish supporting sources, assembly-photo scope and missing exact-part
photographs. Save/reopen verification preserved the mechanism data digest.
See PART_PHOTO_WORKFLOW.md and outputs/cooling-reference-verification.json.

Upper-drive source increment:

- [Upper gearbox original catalog diagram](https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/reduktor_ventilyatora_543_1308210_a1__543_1308211_a1-83):
  inspected `543-upper-exploded.gif`. It identifies three 207K5 bearings and
  one 304K per gearbox, a separate input bearing cup, shims, 44×65 input seal,
  unequal output journals, brush housing and spring. This later catalog does not
  establish that every revision is correct for the 1973 vehicle.
- [SKF 6207 nominal envelope](https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6207)
  and [SKF 6304 dimensional sheet](https://www.tme.eu/Document/e1d0c037878b8ba23e437767aab18a9f/6304.pdf):
  35×72×17 and 20×52×15 mm respectively. These corroborate series boundary
  dimensions, not Soviet special-suffix tolerances, cage internals or interchangeability.
- Installation diagram `543-fan-install.gif` and Cardan exploded diagram
  `543-cardan-exploded.gif` were downloaded and visually inspected from the
  same catalog mirror. Cardan part numbers include 543-1308606 flange,
  408-2201026-02 cross, 704902-K6 needle bearings and two sliding spline forks.
  The Cardan drawing clearly shows four flange holes and the same flange part
  at both ends. The prior three-hole gearbox reconstruction has been replaced
  by four-hole mating interfaces. The common 74 mm PCD, 100 mm outside diameter,
  8.6 mm clearance and axial dimensions remain **fitted**, not drawing dimensions.
  The installation list identifies M8x1 bolts, nuts and 8 mm washers. Neither
  production-year compatibility nor installed Cardan closure has been verified.
  A verified individual photograph of the upper gearbox has not been found.
  Source pages: [Cardan exploded catalog](https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/val_kardannyj_543_1308586_a-82)
  and [fan-drive installation](https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/ustanovka_ventilyatora__privoda-78).
- [MCB universal-joint catalog](https://mcbbearings.com/wp-content/uploads/2024/02/MCB-Univeral-Joint-Catalog.pdf),
  PDF page 29, lists 400/408-2201025 with D=28, O=42.5, L=73 mm and
  704902K6C10 bearings. This is a dimensional lead for the 408 family;
  the original MAZ drawing lists cross 408-2201026-02. The exact suffix
  equivalence remains unverified. The complete PDF and its D/O/L diagram have
  now been visually inspected. The 408-family envelope is used in a separate
  Cardan inspection module; see CARDAN_REFERENCE_NOTES.md for its fitted details.

## Native geometry and operation

`outputs/MAZ543A_Cooling_Master.blend` contains 1237 authored mesh/curve objects,
including repeated hardware, and 254 semantic pose bindings. Counts describe
this reconstruction, not the original BOM. `cooling-parts-register.json` records
roles and source IDs. The module is appended to both editable vehicle masters;
the browser loads `maz543a-cooling.glb` separately. Old single-fan geometry is
removed; legacy air cleaners/batteries are retained as unverified auxiliaries.

Two fan impellers each have twelve twisted airfoil meshes and root hardware.
Clutches have separate driving shafts/armatures, friction rings, coil turns,
magnetic bodies, slip rings, brushes, spring and two needle bearings. The
96 rollers use ideal no-slip velocities between independently rotating races.
Spring length and brush position follow the fitted 1.5 mm engagement travel.
Twelve fitted shutter leaves rotate together and translate their common link.
Actual fan-shroud intersection checks cover 25 animation samples.

Radiator contains flattened hollow tube geometry and thin fin plates, with
separate oil-core geometry. Tank partitions, oil core, expansion vessel and hose
paths remain approximations. Geometry does not yet provide a complete watertight
three-pass tank circuit, cabin heater installation or engine water galleries.
Fan shroud stays now reach the shroud rim. Gearcase mounting and complete
installed clearances still need review.

The lower drive has a hollow, fused casting; removable bearing cups, seals and
shims; three spherical involute bevel gears; hollow input shaft with through
torsion; two output shafts and drilled four-hole flanges; six ball-bearing
assemblies; and a two-gear oil pump with its own cover. The **32:20 teeth and
3.8 mm module are fitted**, not sourced factory values. Separate ideal cage and
ball rotations follow their shaft. Forty-nine actual mesh samples found no
bevel pair, output/output, gear/casting, pump pair or pump/body surface crossings.
This is not a loaded-contact or full installation validation.

Twenty-one remaining enamelled objects use shared 2048 px baked normal/roughness maps,
packed in the Blender master and GLB. These are procedural reconstructions of
the inspected storage finish. Photo texture was not projected as fake geometry.

## Calculation and limits

`lib/cooling.ts` advances within the starting solver's fixed 1/1200 s step.
Two RL coil circuits generate fitted clutch torque capacities. Fan inertia and
quadratic aerodynamic drag feed reaction torque to the crankshaft. Switch-off
retains fan inertia and bearing drag. Pump load is also reflected at the crank.
The chosen fan drive ratio of 1:1 is **not** a sourced original ratio.

A quasi-steady pressure/flow network uses quadratic resistance, parallel bank
paths, radiator, optional heater branches and compressor branch. A conservative
14-node thermal graph transports heat through those paths, with two separate
metal masses. Pump shaft work is dissipated into the water. Fitted radiator
conductance depends on fan speed and manual shutter opening. No automatic
thermostat was invented. Initial water is 70°C and metal 75°C; values do not
describe a cold-start test. Flow, capacitance, torque, coil and heat-transfer
parameters are unmeasured reconstruction values.

Still missing: original lower/upper gearbox teeth, ratios and installed axis positions,
Cardan joint velocity constraints, fan-drive oil pump relief valve and hydraulics, pressure/vacuum
cap valves, manual fan-lock bolts, complete cooling channels and branch hoses,
fluid inertia, cavitation, boiling, calibrated fan/pump maps, real combustion
heat partition, contact loads, wear and thermal expansion. Ideal roller motion
and a small numerical energy residual do not prove physical MAZ accuracy.

## Reproducible checks

`prepare-starting.mjs` generates a shared 601-frame start/run/coast sequence.
`verify-cooling.mjs` checks independent fan control, coasting, pump affinity,
branch mass balance, shutter temperature response, conservative thermal energy,
ideal roller contacts, GLB bindings and validation.
`verify-cooling-native.py` checks actual native animation and fan-shroud meshes.
`verify-cooling-lower.py` checks lower gear/case mesh intersections, all six
bearing envelopes and ideal rolling velocities, and renders both inspection views.
`verify-cooling-install.py` compares engine, starting and cooling poses in both
vehicle masters: 430 joints across 21 sampled frames.

At fitted 1500 crank RPM: both fans settle near 1499 RPM; switching the left
off for 8 s gives roughly 394/1499 RPM. Pump flow is about 252 L/min and shaft
power 367 W. These are **model outputs, not vehicle specifications**. A 180 s
open/closed shutter comparison gives approximately 62.8/78.6°C radiator outlet
with total thermal residual below 0.000002 J. Native maximum pose angle error
was below 0.00007 radians. All quantities and limits are in the JSON reports.

## Upper native geometry increment

Both upper gearboxes now have separate conical input/output gears, eight total
ball-bearing assemblies, stepped shafts, input seals/shims, hollow cast cases,
removable bearing cups, drilled fitted flanges, pedestals and spring-loaded end
brushes. The front support bolts are outside their flange; the inlet touches the
case and the brush meets the shaft end without penetrating it. The **20:32
upper gear pair is fitted**. The fan/armature rotation sign follows the authored
upper output axis, toward the fan (-X); factory rotation and complete Cardan
velocity transmission have not been accepted. Thermal and clutch calculations
continue to use positive speed magnitudes and the fitted net ratio of 1.

Upper casting normals and roughness are baked into separate 2048 px maps.
This alloy finish has no accepted individual upper-gearbox photo and remains a
material approximation. `prepare-cooling-upper.py` prepares the tooth caps;
`update-cooling-upper.py` rebuilds only these parts while preserving the lower
bakes. `verify-cooling-upper.py` checks both local gear pairs/cases over 49
samples, all eight nominal bearing envelopes, and the end-brush contact. It
renders external/internal inspection PNGs. None of these checks validates the
installed interface conflict or turns the whole drivetrain into an accepted
physical simulation.

## Four-hole interface correction

`cooling_interfaces.py` builds the same four-hole mating pattern for both
lower outputs and upper inputs. The four flange bodies have real shaft bores,
through-drilled bolt holes and small machined edge breaks. Their steel finish
is fitted; the replacement lower flanges do not reuse an invalid casting UV atlas.
`update-cooling-interfaces.py` replaces only these meshes, preserving all 254
native joints and the casting texture bakes. `verify-cooling-interfaces.py`
checks each evaluated native mesh: 36 unobstructed bolt-hole rays, 32 solid
surrounding rays, an open central bore and zero non-manifold edges.

These local checks do not accept the current installation. The old Cardan
placeholders still miss the new interface centres, and the present fan-pack
spacing cannot accommodate the proposed complete fork/cross assemblies.
Gearbox orientation, Cardan length, fan diameter and pedestal geometry require
further source checks before the fitted vehicle installation is revised.

The independent Cardan module now has two crosses, eight bearing cups and
176 individually posed needles, with orthogonality and sliding-spline constraints.
It is deliberately identified as an inspection component in the browser and
is not represented as an accepted installed drive. A native whole-vehicle
check initially found each existing fan shroud intersecting the adjacent cab inner wall
(32 triangle pairs on each side). A later photographic lower-cab relief clears
these surfaces at frame zero, but its hidden depth and exact dimensions remain
fitted; see CAB_PHOTO_FIT_NOTES.md. Resolving the fan-pack geometry is still
part of the installation work, not merely an animation hookup.

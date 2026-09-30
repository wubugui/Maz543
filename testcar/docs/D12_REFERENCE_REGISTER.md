# D12A-525A component reference register

This is an open engineering reconstruction. It is not a complete engine, factory
CAD, or a calibrated physical digital twin. Every Blender piece records sourceId,
d12Part, d12Role and dimensionStatus; outputs/d12-parts-register.json lists them.
The source confirms only the features described below, not every dimension of the
mesh. Decorative fastener counts and reconstructed dimensions are not certified.

## Sources inspected

| Source ID | Component / evidence | URL or document | What is still unmeasured |
|---|---|---|---|
| FACTORY-525A | Both complete-engine sides; envelope 1575 x 1052 x 1070 mm | http://www.barnaultransmash.ru/d12a-525a | Individual castings, mounting coordinates and dated accessory versions |
| KMZ-525A | Identified D12A-525A overhaul; three oval covers per bank, valley pump, 12 injection pipes, intake runners, flywheel | https://kmz1.ru/news/kapitalnyyremontdvigateleyd12a525a.html | Perspective photos cannot supply tolerances, hidden pipe routing, tooth counts or original paint |
| D12-F11 | Crankcase arrangement; family manual | https://neva-diesel.com/f/rukovodstvo_d12.pdf | Transport-variant casting and all local dimensions remain to be checked |
| D12-F12 | Crankshaft, seven mains/six throws, flywheel (p31) | Same D12 family manual | 525A crank part number, web profile, flywheel dimensions and gear tooth counts |
| D12-F13 | Hollow journals, oil passages and gear-end tail (p31) | Same D12 family manual | Exact bore routing and plug sizes; not yet fully modeled |
| D12-F14 | Main/articulated rods, pins, bearing shells, hollow piston, ring types (p32–33) | Same D12 family manual | Bore 150 mm and main stroke 180 mm are nominal family data; other dimensions are reconstructed |
| D12-F15 | Six wet liners in each bank, through studs, one-piece head (p34–35) | Same D12 family manual | Cylinder pitch, jacket and head water passages, transport part revision |
| D12-F16 | Two intake/two exhaust valves, guides, nested springs, retainers (p36) | Same D12 family manual | Valve sizes, spring law and actual lift; target timing now checked against MAZ |
| D12-F17 | Generic family comparison only (p37) | Same D12 family manual | This edition puts the compound gear on exhaust; target MAZ places it on intake. Do not copy this variant assignment |
| D12-F18 | Bevel-shaft timing topology and accessory drive (p38–39) | Same D12 family manual | 525A drive ratios must be checked; family table is not applied to every transport accessory |
| MAZ-1977 | Variant identification, firing order, electric/air starting, dry sump, two radiator fans | https://djvu.online/file/zjMdLY3MFjmTL | Original parts catalog and dimensional drawings still needed |
| MAZ-1973-F7 | Original target gear scheme: cam spur pair 22/22, intake bevel 24 with 12 input; upper/lower and accessory ratios | https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/004.htm | Counts established; module, pressure angle, cutter profile and bearing coordinates not measured |
| MAZ-1973-F8 | Intake 20 BTDC/48 ABDC, exhaust 48 BBDC/20 ATDC, ±3 degrees; firing order | Same MAZ chapter, image 0329.jpg | Lift, lash and pressure traces remain unknown |
| MAZ-1973-F9 | Hollow camshafts, radial oil holes, seven paired split bearings, 41/10 spline sleeve, locking rings, handed retainers; intake clockwise/exhaust counterclockwise viewed from gear end | Same MAZ chapter, text 0336.jpg and exploded image 0343.jpg | Exact bore diameters, drilled angular datums, thread pitch, fastener forms and dimensions |
| GEAR-GEOMETRY | Standard involute and pitch-cone geometry, used only to construct fitted gears | https://khkgears.net/gear-knowledge/gear-technical-reference/calculation-gear-dimensions/ | Not an MAZ original tooth profile or manufacturing drawing |
| C5-PHOTO | C5-2C marked starter; C5 family shape only | http://www.dzmd.ru/wheeltag/s5_2c.html | -2C is not proven to be the 1977 C5 revision |
| MZN2-PHOTO | MZN-2 with MN-1 prelubrication motor, mounted to chassis | http://www.avtomash.ru/katalog/pred/electro/miela/mzn2tu.htm | Precise period mounting, pump clearances and port coordinates |
| MAZ-1973-F28 | Original circulating pump section: six stamped stainless blades, two bearings, square flange, drive dog, oil seal, corrugated water seal, four-tab washer and rotating wear sleeve | https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/007.htm | All local dimensions, blade curvature, bearing specification, manufacturing fits and pump curve; see D12_WATER_PUMP_NOTES.md |

Photographs remain reference files in D:/maz543-references/engine. They retain
their watermarks. No redistribution permission is implied. Detailed photographic
audit: D:/maz543-references/engine/ENGINE_REFERENCES.md.

## Reconstruction parameters, not factory measurements

The active source is lib/d12.ts. Cylinder pitch 180 mm, main rod 320 mm, slave
rod 242.426 mm and its articulation coordinates (30 mm,72.277 mm), valve lift 9 mm,
cam base radius 24 mm are provisional. The two rods are rigid links and their
shared articulation is solved geometrically. This is a substantial improvement
over twelve independent generic rods. The slave dimensions are numerically fitted
to the published family secondary stroke of 186.7 mm and equal bank top dead
centres, not measured rod dimensions. Authentic rod drawings remain necessary.
The target event window is now 248 crank degrees, with the 1973 nominal angles.
A fitted C1 quartic lift law generates the flat-tappet envelope. The previous
cosine-squared law, compressed to this window at the fitted 24 mm base radius,
would produce a nonconvex envelope; it was replaced rather than allowing mesh
penetration. The 9 mm lift and the quartic curve are not factory cam data.
Valve lash, acceleration loads and dynamic valve float remain unvalidated.

Engine bank names are viewed from its gear end; these are not vehicle-left and
vehicle-right names. Left-master/right-articulated is an inference from the 1977
rotation direction and D12 repair guidance, not a direct 525A dimensioned drawing.
Firing sequence and nominal cam events follow the target manuals; pressure
traces, lift shape and dimensional tolerances remain reconstructed.

## Cam-bank reconstruction increment, 2026-09-05

The four camshafts now counterrotate in each bank. Each has 12 profiled lobes,
seven journals, a through oil bore, radial oil ports, ten external rectangular
splines, a 41-external/10-internal adjusting sleeve, retainers and split rings.
Four 22-tooth spur gears mesh as two pairs. Each intake gear also has its target
24-tooth spherical-involute bevel portion, now meshed with its 12-tooth input.
The 25-gear train is described in D12_TIMING_SOURCE_NOTES.md.
The spur module is 64 mm / 22 = 2.90909 mm, derived from the provisional shaft
spacing, with 20 degree pressure angle and generated root clearance. Neither
this module nor the fitted 3 mm bevel module is an original specification.
The 14 paired bearing pedestals/caps have actual journal and stud bores.

Five original scans were viewed and packed into the editable Blender file;
their valid JPEGs and SHA-256 manifest are in
D:/maz543-references/engine/timing. The raw HTTP downloader first received small
HTML redirects; those were replaced with the images obtained from the normally
rendered browser chapter. The filenames retained from intake are imperfect:
`1973-maz-fig9-cam-assembly.jpg` is text, and `1973-maz-cam-caption.jpg` is the
actual exploded assembly. Refer to image numbers 0336/0343 in the manifest.

## Remaining modeled-engine work

The separately authored C5/MZN module now has a reduced causal start model;
its exact armature/windings and calibrated electrical data remain open (see
STARTING_REFERENCE_REGISTER.md). Generator internals, timing housing/shaft installation calibration, compressor/distributor,
fuel pump delivery valves/governor, complete coolant passages, dry-sump supply and
scavenge gears, oil galleries and pressure circuits remain open. Every missing
component requires its own photo/catalog reference before dimensional acceptance.
The browser must not advertise the engine as complete or physically calibrated.

Native asset: outputs/D12A525A_Engine_Master.blend. Its separate web module is
public/models/d12a525a-engine.glb. The neutral poses and native cycle share a
versioned source; animated joints have semantic names rather than numeric IDs.

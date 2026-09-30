# Original MAZ timing evidence — 2026-09-05

Primary source: [MAZ-543 Technical Description, 1973, engine chapter](https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/004.htm).
Figures 7, 8 and 9 were saved through the normally rendered browser page and
visually inspected at original resolution. Local JPEG hashes are recorded in
`D:/maz543-references/engine/timing/primary-pages-manifest.json`.
The [1977 original book](https://djvu.online/file/zjMdLY3MFjmTL) independently
confirms the target text on pp.40–45. The cached MAZ543-1977.txt is a challenge
response, not a downloaded book; do not use it as full local OCR evidence.

| Path in original fig.7 | Teeth and speed relative to crank n | Implementation status |
|---|---|---|
| Crankshaft bevel | 27, n | Modeled; ideal gear constraint |
| Upper vertical bevel | 18, 1.5n | Modeled; ideal gear constraint |
| Lower vertical bevel | 18, 1.5n | Modeled; ideal gear constraint |
| Inclined generator takeoff from crank | 18, 1.5n | Modeled; ideal gear constraint |
| Generator takeoff/output pair | 21 at 1.5n → 18 at 1.75n | Modeled; ideal gear constraint |
| Upper vertical to each inclined cam shaft | 12 at 1.5n → 18 at n | Modeled; ideal gear constraint |
| Inclined cam shaft to intake cam | 12 at n → 24 at 0.5n | 12/24 spherical mesh with intake compound |
| Intake to exhaust cam | 22 → 22, opposite rotation, each 0.5n | Actual spur mesh and linked opposite rotations |
| Injection pump/air distributor | 12 at 1.5n → 36 at 0.5n | 12/36 spherical mesh; pump internals still reduced |
| Lower shaft / circulating pump spur | 23 at 1.5n | Modeled; ideal gear constraint |
| Oil-pump intermediate and output | intermediate 36 → output 20 at 1.725n | Modeled; ideal gear constraint |
| Fuel feed takeoff | 23 at 1.5n, then bevel 11 → 21 at 0.786n | Modeled; exact ratio 11/21 × 1.5 |

The generator is not a direct 27/18 = 1.75 drive: the intermediate 21/18 stage
is necessary. Shaft axes now follow a coherent mounted layout. Signed rotation is expressed in
each shaft local X axis and inferred from the facing gear cones; mounting
coordinates remain reconstructed. This does not establish original machining dimensions.

Target-specific details in fig.9: compound bevel/spur gear on **intake**, spur
gear on exhaust; seven paired split bearings; hollow shafts with radial oil
feeds at the journals and lobes; 41 external triangular splines / 10 internal
rectangular splines on the adjusting sleeve; spring retention; left-hand front
intake retainer threads, right-hand exhaust retainer and rear plug threads.
The right-bank intake retainer carries the spring drive of the tachometer.
The generic D12 manual p37 puts the compound on exhaust; it cannot override
the MAZ target text and exploded drawing.

Fig.8 nominal events relative to firing TDC: intake opens 340° and closes 588°;
exhaust opens 132° and closes 380°. The diagram gives ±3° service tolerance.
This does not establish the 9 mm model lift, a cam acceleration curve, actual
running lash, shaft spacing, oil-port angular datums or manufactured tolerances.

Photo cross-check: `D:/maz543-references/engine/05-family-camshafts.jpg` (500×199)
was inspected for slender shaft proportions and stepped/journal surfaces. It
comes from a D6/D12 supplier specimen, without readable shaft numbers; it cannot
prove a specific 525A revision or any hidden dimensions. The image is packed in
the engine Blender source along with the original MAZ diagrams.


## Timing increment and verification

The native assembly contains 25 separately identified gear meshes and 15 mating
pairs, driven by one crank angle through tooth-count constraints. Ten additional
named shafts bring the engine pose set to 148. All bevel pairs use spherical
involute surfaces with conjugate swept-root relief; the previous Tredgold cam
portion has been replaced. The six bevel pair types and three accessory spur
pair types passed 721 angular samples per type. Native Blender BVH checks passed
73 positions per pair with no gear-surface intersections and axis error below
2e-7. These sampled tests do not certify physical contact under load.

The end caps are constrained triangulations of the actual undercut outline.
An initial radial quad fan filled a concavity and intersected the fuel-drive
mate at six sampled positions; correcting the caps removed these intersections
without shaving the operating tooth flanks.

Mathematical reference: [The spherical involute bevel gear: its geometry,
kinematic behavior and standardization (2011)](https://www.researchgate.net/publication/225659482_The_spherical_involute_bevel_gear_its_geometry_kinematic_behavior_and_standardization),
equations 8–9. The 20 degree pressure angle, module, backlash allowance, shaft
lengths, bores and bearing forms are reconstruction choices. No original cutter
geometry, load distribution, torsional compliance or measured clearances exist
in this implementation. The legacy accessory cases, water-pump and air-distributor
installation still need reconciliation with these new drive axes. Do not present
the assembled housing installation or complete accessory internals as accepted.

Browser controls add timing overview, crank takeoff and pump-train close-ups.
Moving shafts use accumulated crank angle rather than the UI's wrapped 720 degree
angle, avoiding phase jumps on non-integer accessory ratios. Starting, pause and
slow motion share this same accumulated state.

Additional part-photo search located the supplier's [308-68-2 inclined gear](https://neva-diesel.com/internet-magazin/product/103466841),
[508-67-1 / 308-67-1 shaft](https://neva-diesel.com/internet-magazin/product/valik-naklonnyj-privoda-gazoraspredeleniya-508-67-1-308-67-1),
[308-14-11 bearing](https://neva-diesel.com/internet-magazin/product/podshipnik-shesterni-naklonnogo-valika-308-14-11)
and [SB308-09-3 casing](https://neva-diesel.com/internet-magazin/product/kozhuh-naklonnogo-valika-sb308-09-3).
These identify D6/D12 family parts, not a verified 525A revision. The gear page
currently exposes n.png rather than a usable observed part photograph; these
pages are leads, not additional photographic evidence or dimensions. Search
results for unrelated D65 tractor gears were rejected.

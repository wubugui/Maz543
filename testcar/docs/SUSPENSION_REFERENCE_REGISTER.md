# MAZ-543A suspension reconstruction

The full source index is `D:/maz543-references/suspension/SUSPENSION_REFERENCES.md`.
Reference photos are research material, not licensed browser texture assets.

| Source ID | Primary evidence | Geometry supported | Limit |
|---|---|---|---|
| MANUAL-1973-F90 | [MAZ-543 technical manual, fig.90](https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/017.htm) | two longitudinal torsion shafts, sleeves, bronze bushes, forked arms, end pins, anchors, damper eyes, stops | family structure; no verified complete hardpoint dimensions |
| MANUAL-1973-F91 | same manual, fig.91 | double-tube hydraulic damper, rod, piston, guide, gland, base valve, telescoping guard | cylinder sizes and valve force curves unconfirmed |
| PHOTO-035 | [Tim Roberts MAZ-543 walkaround](http://www.primeportal.net/artillery/tim_roberts/maz-543_scud_b_tel/index.php?Page=2), image 035 | changing cast arm sections, raised ribs, clamping ears, sleeve covers, frame bolts | vehicle is identified as 543 family; A-specific year unconfirmed |
| UNIVERSITY-3.12 | [Zaporozhye Polytechnic construction text](https://eir.zp.edu.ua/bitstreams/48a05076-5f2c-48a1-8a44-f78f19784d84/download), page28 | cross-check four-bar and damper attachment topology | structural diagram, not dimensioned CAD |

Each authored mesh carries its source ID, part description and dimensional status.
Repeated washers/fasteners use the assembly photograph; no claim is made that a
separate documented photograph exists for every individual fastener.

## Unresolved calibration

Every hardpoint in `lib/suspension.ts`, bar length/diameter/spline count, damper
length, stops, material coefficients, sprung/unsprung masses and tire law remain
reconstructed values. Upper torsion bar is thinner than lower, as documented.
Eight stations use paired longitudinal anchors as a packaging hypothesis; exact
anchor directions and axle-specific positions remain open. The original 1977
manual now establishes the pre-twist handedness assignment below; this does not
calibrate those anchors or the numerical stiffness.
The later 7310 front/rear catalog is not copied as proof of early 543A castings.
The source drawing's incomplete `130 +5` annotation is not used as travel data.

## Original 1977 scan check (cloud, 2026-09-30)

Printed page 168 was directly inspected in the retained 1977 third-edition scan
(DJVU page 86; book SHA-256
`cf8ebb65dcbfca6dd3b6c55a3174cfe9d628a206cb8c846eceee0041a2bb1bde`).
The public source and provenance are recorded in
`CLOUD_REFERENCE_CALIBRATION_20260930.md`; the raw scan is research material,
not a browser texture or a new public deliverable.

The torsion end with the threaded hole carries its manufacturing pre-twist
mark. `Пр` applies to the right front wheels and left rear wheels; `Л` applies
to the left front wheels and right rear wheels. These labels describe the
documented handedness, not an inferred sign for the application's rotation
coordinates, and have not been stamped onto the fitted component geometry.

The same page describes upward travel being stopped by the rubber buffer in
bracket 12 and the upper-arm support pads; downward travel is stopped by support
bolts 17 in the suspension bracket. It supplies no numeric travel in this
passage. The current numerical compression/droop limits therefore remain
uncalibrated, and an arm pose inside those limits is not proof of real stop
contact. The additional rear torsion described at the bottom of the page is
explicitly a MAZ-543M distinction; it must not be added to the 543A from that
figure alone.

## Mechanics and presentation

The four-bar solves both rigid arms and upright by circle intersection. Two bar
twist energies produce wheel force by the virtual-work derivative. Damper force
uses the actual changing eye distance and its motion ratio, with independent
compression/rebound coefficients. Eight unsprung masses and body heave/pitch/roll
are integrated at up to 1/480 s. Tire forces are unilateral; the contact model
uses a loaded nominal radius. Tire deformation itself is not yet rendered.

The road test pads supply displacement to the tire contact calculation. Wheel
positions are force responses, not prescribed sinusoidal wheel animation. This
is an uncalibrated reduced-order vertical model: it does not certify MAZ ride
performance, material stress, fluid valve behavior, steering compliance or full
vehicle dynamics. Native articulation keys illustrate the geometric envelope;
the browser runs the force simulation. Native/web live-force parity remains open.

The damper contains real nested cylinders and rigid piston/rod parts. Metering
valve passages and flow internals still need complete geometry and hydraulic
parameter verification. Halfshafts, steering links, kingpin inclination and each
axle-specific casting revision are separate pending work.

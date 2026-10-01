# Original alignment specification and current native geometry

This is a read-only diagnosis of the retained production Master, not an adjusted
vehicle. All 16 whole-vehicle gates remain OPEN.

The original 1977 manual's printed page 24 gives the MAZ-543A steered wheels a
nominal camber magnitude of 1°. Pages 316–317 specify toe at a 1040 mm reference
diameter: first axle 8–14 mm, second axle 5–12 mm loaded; both 8–14 mm unloaded.
The first loaded figure is **8**, verified against pixels rather than the faulty
OCR figure 6. Source and procedure are recorded in
`../../reference/wheel-alignment-source-20261001.json`.

The actual production Master has four front tyre symmetry axes effectively
horizontal: extracted camber magnitudes are below 2e-14°. At the existing wheel
centres' height, ray intersections with the actual evaluated inboard tyre profile
at ±520 mm give simultaneous rear-minus-front separations of 0.000135 mm for axle
1 and 0 mm for axle 2. These are numerically zero at model precision. The measured
profile centroids coincide with their actual spin origins within 0.1 µm; the
PCA eigenvalues are retained so the axis-identification assumption can be checked.

These results expose missing nominal wheel alignment in the current neutral
geometry. They **do not** constitute the manual's qualified physical measurement:
there is no applied tyre pressure, compliant contact, load, rolling by half and
quarter turns, or steering linkage play assessment. The manual's nominal 1° does
not establish a sign convention or tolerance in the inspected table. No target
angle midpoint, suspension travel or rod adjustment has been invented.

The diagnostic opens the fixed original Master, reads its evaluated profile
meshes and native spin centres, and writes JSON only. The before/after source
SHA-256 matches. No object was transformed and no blend was saved. Sidewall rays
are deliberately restricted to horizontal axes: extending the method to cambered
wheels requires an explicit wheel-axis-height/reference-radius construction.

Next, inspect which retained native carrier, hub and suspension components must
share an alignment transform before attempting an independent assembled candidate.
Rotating only tyres to match the table would not establish a correct wheel-carrier
or tie-rod assembly.

Subsequent native topology readback records 196 descendants under each front wheel
carrier. Carrier and spin objects have retained animation actions covering frames
0–241. The separate S543 wheel marker has no children: the existing attach script
bakes its poses onto the carrier, while the webpage consumes `suspensionPose`.
Absence of a direct parent/constraint between the marker and wheel is therefore
not evidence that animation is absent. Merely finding names containing `tie_rod`
is also insufficient: C5/MN1 matches are starter/pre-oil components.

Original page 320 explicitly connects torsion-bar permanent set and chassis
settlement with changes in steered-wheel camber. Nominal alignment must therefore
be considered with suspension state. The inspected source does not justify
turning four tyres by a constant 1° while leaving supports and links untouched.
The topology report is an inventory, not a fresh validation of the full animation.

Run from `testcar` with the matching official Blender 4.5.13:

    blender -b -t 2 --python scripts/audit-wheel-alignment-native.py

The process completed with exit 0 on 2026-10-01. A successful diagnostic exit
means the stated measurement completed, not that the vehicle meets specification.

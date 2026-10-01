# Exact stationary local-modifier eligibility

This is a narrow extension for the pinned source,10exact modifier records and
8recorded local Position/XYZ/Math/SetPosition graphs. It is not a generic NODES or
SUBSURF whitelist. All original whole-object, upstream modifier, Boolean operand,
ancestor, moving hierarchy and released-button rules remain in force.

The graph's fixed local map is interpreted as
X = Z + offset + 0.4000000059604645 * max(Y - 1.940000057220459, 0),
Y = sign * (X + 0.5350000262260437), Z = Y.
Only each exact recorded offset/sign, defaults, links, interfaces and settings
is accepted. This explains dependencies, not manufacturer dimensions or a formal
proof of Blender arithmetic. Render evaluation and moving-object use are denied.

Run the tiny fixture with the official Blender4.5.13 binary:
--background --factory-startup --disable-autoexec --threads1 --python-exit-code1
--python ABSOLUTE_PATH/scripts/test-static-local-cab-modifiers.py

Then run the separate actual-source audit with the same startup flags:
--python ABSOLUTE_PATH/scripts/audit-complete-cab-static-local.py

Use separated CLI tokens (`--threads 1`, `--python-exit-code 1`), not the compact
illustrative labels above. The fixture creates a small temporary library solely
for a linked-ID rejection case; it never opens or modifies vehicle .blend files.
The real source audit opens the exact published Master read-only and records its
SHA before and after. Active mutation handlers, scene animation or simplification
cause rejection rather than silently disabling them.

Fixture:10positive profiles and49negative local cases; separate composition
controls reject an animated parent, moving Boolean operand and unsupported
upstream modifier while the local clause alone remains eligible. Full source:
406fixed objects and44door parts,582recursive contexts,10local modifiers,0issues.

The earlier fail-closed report remains unchanged in its own published directory.
No pose or geometry is repaired by this audit. Existing52unknown frozen pairs,
6closed surface candidates, untested hidden/outside-root geometry, inherited
Draco error, real browser QA and all16vehicle gates remain open.

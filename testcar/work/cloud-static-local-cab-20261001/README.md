# Exact stationary local-modifier eligibility

This is a narrow extension for the pinned source, 10 exact modifier records and
8 recorded local Position/XYZ/Math/SetPosition graphs. It is not a generic NODES or
SUBSURF whitelist. All original whole-object, upstream modifier, Boolean operand,
ancestor, moving hierarchy and released-button rules remain in force.

The graph's fixed local map is interpreted as
X = Z + offset + 0.4000000059604645 * max(Y - 1.940000057220459, 0),
Y = sign * (X + 0.5350000262260437), Z = Y.
Only each exact recorded offset/sign, defaults, links, interfaces and settings
is accepted. This explains dependencies, not manufacturer dimensions or a formal
proof of Blender arithmetic. Render evaluation and moving-object use are denied.

Run the tiny fixture with the official Blender 4.5.13 binary:
--background --factory-startup --disable-autoexec --threads 1 --python-exit-code 1
--python ABSOLUTE_PATH/scripts/test-static-local-cab-modifiers.py

Then run the separate actual-source audit with the same startup flags:
--python ABSOLUTE_PATH/scripts/audit-complete-cab-static-local.py

The fixture creates a small temporary library solely
for a linked-ID rejection case; it never opens or modifies vehicle .blend files.
The real source audit opens the exact published Master read-only and records its
SHA before and after. Active mutation handlers, scene animation or simplification
cause rejection rather than silently disabling them.

Fixture: 10 positive profiles and 49 negative local cases; separate composition
controls reject an animated parent, moving Boolean operand and unsupported
upstream modifier while the local clause alone remains eligible. Full source:
406 fixed objects and 44 door parts, 582 recursive contexts, 10 local modifiers, 0 issues.

The earlier fail-closed report remains unchanged in its own published directory.
No pose or geometry is repaired by this audit. Existing 52 unknown frozen pairs,
6 closed surface candidates, untested hidden/outside-root geometry, inherited
Draco error, real browser QA and all 16 vehicle gates remain open.

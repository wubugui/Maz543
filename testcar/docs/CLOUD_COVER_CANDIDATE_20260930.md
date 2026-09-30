# Cloud three-cover diagnostic candidate, 2026-09-30

Status: CANDIDATE, NOT PROMOTED. The production GLB and original vehicle masters are unchanged. All 16 whole-vehicle acceptance gates are still OPEN.

## Reproduced failure and actual repair

The original `hub-three-cover.py` was run unchanged against the received current Master under official Blender 4.5.13. It reproduced the empty evaluated geometry exception during rotation. Blender returned zero despite the Python exception; all new test/build invocations use `--python-exit-code 1` and check the expected report files.

Two separate defects were established, not merely inferred from successful output:

1. Panel Boolean operands were left fixed while the authored panel moved. The cloud candidate keeps each panel's editable construction operands attached to its actual transform and excludes construction objects from optional export.
2. The newly positioned hinge empty had a stale `matrix_world` when reparented. Its saved world origin was actually (0, 0, 0), contrary to the declared fitted hinge location. The helper now updates the dependency graph before capturing the world transform. A hard assertion checks the installed hinge at Blender coordinates (-4.58, 0, 2.336), with the placement still explicitly uncalibrated against the real vehicle.

The first cloud candidate could save but failed saved-shape regression at the hinge knuckles by 3.695 mm. It was retained and rejected. Candidate r2 fixes the true hinge and attaches its bore operands too. Both files were saved and independently reopened. All three moving objects over 21 discrete 0–60° poses retain their evaluated local vertex sets within 4.697 micrometres (20 micrometre numerical regression threshold). Eleven added panel/hinge solids passed the recorded manifold/positive-volume checks. These are limited native geometry checks, not proof of factory dimensions or exact surface equivalence.

## Checks that remain failed or untested

For each native r2 file, the sampled collision audit found:

- Closed pose: 232 surface triangle intersections with `BL_Front_cover_lip`.
- 3° pose: 61 and 60 surface intersections with the two existing static latch curves.

No collisions were silently filtered out except the explicitly named hinge-pin/mounting contacts in the inherited diagnostic. The audit samples 0–60° every 3° in a stationary vehicle. It is not a continuous sweep, complete mechanism collision proof, suspension-travel test, or structural/load assessment. The closed contact and latch release mechanism require actual reference-driven redesign. Passing the rigid-shape test does not pass the collision test.

Two Cycles CPU renders of the saved r2 candidate (closed and 60°) were actually rendered and visually inspected. The lid no longer departs around the world origin. These images are native renders, not webpage screenshots; they are not photorealism or full-vehicle visual acceptance.

## New reference changes the next modeling step

The [1977 technical description, printed p.173](https://djvu.online/file/zjMdLY3MFjmTL) supports three upper panels: the front is hinged and contains the coolant filling access, while the other two are removable. This prose does not establish the hinge's exact position or service angle.

A [543A-8400002 assembly catalogue](https://www.autoopt.ru/auto/catalog/special/maz/maz-543_7310/33) was retrieved, and its [linked drawing](https://www.autoopt.ru/acat/data/maz/543/84.2.gif) actually inspected at 825×638 pixels. The site labels the catalogue 2008, so revision/year applicability must remain explicit. It identifies front panel 543-8402020, middle panel 543A-8402060, rear panel 543A-8402120-01, two locks 543-8402078-A, and a separate hinge assembly 543-8402530-01. The illustration shows pressed panel ribs, a rear vent/mesh, and hardware that is not represented by the current simple fixed latch curves.

The drawing has no dimensional scale. Exploded perspective alone is insufficient to certify the installed hinge orientation. Therefore r2's fitted rear-edge axis is not promoted as a reference-accurate mechanism. Next: reconcile actual hinge, front-panel outline, latch release and support against the diagram and retained vehicle photographs, before generating a production export.

## Portability

A separate `pack-cloud-reference-images.py` workflow packs the four retained external reference images into an independent candidate copy only after matching the migration manifest's original bytes. It reopens the saved files and verifies packed-image SHA-256. Current source masters and original reference images are not rewritten. The actual run packed and reopened all four source images in each master with matching SHA-256. The same 21-pose rigid-geometry regression was then rerun on these portable files and passed at the same 4.697 micrometre maximum.

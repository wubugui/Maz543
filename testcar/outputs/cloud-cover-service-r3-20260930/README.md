# MAZ543A front-cover service candidate r3 — 2026-09-30

**CANDIDATE, NOT PROMOTED. Overall installation/service acceptance remains FAIL.**
All 16 whole-vehicle gates remain OPEN. Production assets, r2 sources and browser assets remain unchanged. This independent native candidate is not promoted or deployed.

## What was actually changed

1. **Fixed seating rabbet in the fitted front lip**, using Blender's native EXACT Boolean Difference and a 1 mm edge-break Bevel. The original complete lip is preserved as `ARCHIVE_R2_BL_Front_cover_lip`. The fixed box cutter belongs to `body`, not the moving lid. It cuts only the upper central region; it is not a dynamically deformed/subtracted clearance envelope.
   - Original lip: Blender XYZ bounds X −5.590…−5.470 m, Y ±0.710 m, Z 1.9455…2.0505 m
   - Closed lid minimum Z: 2.01014781 m
   - Rabbet floor Z: 2.00814781 m; fitted nominal vertical gap 2 mm
   - Rabbet width: 1.02598669 m, using closed-panel transverse bounds +3 mm each side
   - Retained lower rail minimum envelope height: 62.6478 mm; untrimmed shoulders: 197.0066 mm each
   - Lip remains one closed positive-volume solid: volume 0.01778759 → 0.01260441 m³, approximately 70.86% retained
   - These are candidate-fit values. **The gap is not a completed seal, seating/bearing contact, load support or factory dimension.**
2. **Explicit diagnostic latch-release stage**, rigidly rotating the existing two three-point Bezier proxies before the lid opens. The retained curve first points define fitted pivots (−5.598, ±0.46, 2.000) m; latch travel −100° and lid travel +60° are uncalibrated diagnostic choices. The original curves remain archived. The latch shapes were not replaced with easier test objects, and neither latch is excluded from collision tests.
3. **Native Weld modifier on coincident cap rims**, 1 µm threshold, keeping the editable Bezier source. `use_fill_caps` was already true. Caps had duplicated rim vertices, giving 48 nonmanifold boundary edges per latch. Welding changes 420→396 evaluated vertices and 48→0 nonmanifold edges; the bidirectional vertex-set displacement is exactly 0 m in both files. This is a topology repair, not movement of the latch surface.

The native control object is `BL_Cover_service_DIAGNOSTIC_CONTROL`, custom property `service_stage`:
- 0: closed lid, locked proxy positions
- 1: lid closed, proxies rotated −100°
- 2: proxies remain released, lid rotated +60°

The driver enforces a demonstrative sequence. It is **not** a physical interlock, real calibrated lock/hinge, load simulation, or factory-approved maintenance procedure.

## Saved/reopened checks

Both `MAZ543A_Master.blend` and `MAZ543A_Textured.blend` were independently reopened with Blender 4.5.13 LTS.

- Closed-pose topology: all **14 checked solids** (the inherited 11 panel/hinge pieces, lip, two repaired latch proxies) have zero nonmanifold edges and positive signed volumes
- 41 discrete service states: 21 latch states at 5° intervals, followed by 20 lid states at 3° intervals
- Five moving objects plus fixed lip checked for evaluated local vertex-set rigidity; maximum change **4.69668 µm**, within the existing 20 µm numerical regression threshold
- Fixed lip evaluated vertex-set change **0 m** in every sampled state
- Cutter and lip world-matrix change **0** in every sampled state
- Full active assembly broadphase selected **370 static objects in Master / 299 in Textured**, including previously ignored hinge pins and mounting lugs. All actual pairwise motion hits and fixed-lip installation hits are retained in JSON. Construction, archived comparisons and hidden-render/source objects are explicitly listed separately
- Original closed lid vs original lip reproduces **232 triangle pairs**. The new closed lid vs rabbet lip has **zero triangle crossings**
- Negative control with the actual lid at 3° but original proxy locks still locked reproduces **61 / 60 triangle pairs**. The collision test has not been weakened

This is discrete evaluated-triangle surface intersection plus vertex-set regression. It is **not a continuous sweep, complete solid-containment test, clearance/tolerance proof, load assessment, or whole-vehicle acceptance**. Topology is measured at the saved closed pose; rigidity is measured at all 41 poses.

## Remaining failures, with their locations

### 1. Latch root vs front lip during early release: FAIL

For each native file, the two locks vs lip respectively report:

| Diagnostic release angle | Triangle pairs (positive Y / negative Y) |
|---:|---:|
| 0° | 21 / 17 |
| −5° | 19 / 15 |
| −10° | 8 / 6 |
| −15° | 8 / 6 |
| −20°…−100° sampled every 5° | 0 / 0 |

This is at the **root next to the fitted pivot**, around X −5.594…−5.588 m, |Y| 0.450…0.470 m, Z 2.002…2.011 m, not at the released hook tip. The candidate provides no real mounting bearing or cutout explaining this overlap. Therefore it is recorded as **unresolved geometric interpenetration**, not waived as permitted mounting contact. Original lock construction and mounting need reference/dimensional clarification.

With the proxies fully released, the actual lid and knuckles at **3°…60° every 3°** have no reported triangle crossings with the tested active assembly, including the locks. This limited improvement does not erase the release-stage failure.

### 2. Fixed lower lip vs upper grille crossbar: FAIL

The lip intersects `BL_Radiator_horizontal_1.925` in Master, and the corresponding region of `BL_Merged_body_OD_green_aged_enamel` in Textured. The crossing is down at the **lower lip / top of the grille rail**, around Z 1.9534…1.9550 m in the intersecting triangles, below the new upper seating recess.

The original r2 lip already has this intersection (40 triangle pairs). The Boolean lip has 96 triangle pairs in the same region; changed tessellation means pair count is **not** penetration volume or a severity comparison. The original lip lower bound is 1.9455 m and the grille reaches 1.9550 m, giving a 9.5 mm overlapping vertical envelope. No assembly joint, tolerance or permitted-contact definition validates this overlap. Neither part was moved to hide it.

The verifier deliberately returns **exit code 1** after completing both files because these failures remain. It does not treat completed output generation as engineering success.

## Evidence files

- `build-service-candidate.json`: source hashes, exact fitted parameters, original preservation, zero-displacement cap weld
- `saved-service-verification.json`: both native files, complete per-state matrices/rigidity, all observed intersections, negative controls, fixed cutter, topology and explicit exclusions
- `latch-cap-diagnosis.json`: original cap-rim boundary evidence and native-Weld diagnosis
- `protected-input-sha256.json`: original production masters/GLB and both portable r2 source masters unchanged
- `verify-exit-code.txt`: expected 1, because unresolved installation/service contact remains
- `native-render-manifest.json`: real Cycles CPU paired-image camera matrices, settings and source/pose descriptions
- `native-visual-QA.json`: all six images opened and visually inspected; all three camera/projection pairs exactly identical; PNG dimensions verified
- `native-r2-closed-detail.png` / `native-r3-closed-detail.png`
- `native-r2-open-detail.png` / `native-r3-open-detail.png`
- `native-r2-open-context.png` / `native-r3-open-context.png`

The images are native renders, not webpage screenshots. Paired cameras are identical. r2 open images retain the original static locked proxies; r3 open images show their explicitly diagnostic release. No AI-generated image is used as reference or validation.

Initial failure reports/logs are retained separately; Blender `.blend1` files, if present, are the immediately preceding r3 pre-Weld backups, not the final candidate deliverables.

## Re-run

From the repository root, using the official installed Blender:

```sh
BLENDER=/workspace/shared/maz-tools/blender-4.5.13-linux-x64/blender
"$BLENDER" --background --threads 4 --python-exit-code 1 --python testcar/scripts/build-cloud-cover-service-r3.py
"$BLENDER" --background --threads 4 --python-exit-code 1 --python testcar/scripts/verify-cloud-cover-service-r3.py
# Expected verifier exit = 1 while documented failures remain; inspect JSON.
"$BLENDER" --background --threads 4 --python-exit-code 1 --python testcar/scripts/render-cloud-cover-service-r3.py
```

Only the dedicated r3 candidate folder is written by these scripts. The verification command intentionally returns failure while the recorded installation/release contacts remain unresolved. Rendering changes are not saved into either native model. Modeling uses native Boolean, Bevel, Weld, Bezier data and driver/transform tools, with no hand-assembled mesh construction.

## Reference limits and next engineering step

The retained 1977 manual printed p.173 supports one hinged coolant-access front panel and two removable following panels. The retained catalogue image `testcar/work/cloud-reference-20260930/543a-8400002.gif.png` shows locks and hinge hardware but supplies no scale or sufficient installed-axis evidence. No new request was made to the CAPTCHA-blocked catalogue site.

The fitted rear-edge hinge, central contour, new relief, original proxy locks and their mounting are not factory-accurate by evidence. Before promotion, obtain a defensible installed latch/bearing, lip-to-grille joint and real hinge reference, then redesign those actual interfaces and repeat service/contact checks. Do not reinterpret the 2 mm gap or the released-lid samples as completed sealing, support or mechanical acceptance.

# Single-side lower-step installation diagnostic

## Result: layout installation FAIL; frame solid validity UNKNOWN

The already-authored fitted lower step cannot be installed at these datums. Its second plain tread box contains surface points from eight distinct original front-wheel/tyre objects. This finding is separate from the retained old-step coexistence, and does not rely on interpreting the defective frame as a solid. No original object was deleted, moved, hidden, reparented or replaced. No model was saved, no render was made, and all 16 whole-vehicle gates remain OPEN.

Final native attempt 05 completed normally (exit 0, CPU1, 72.383540 s, 240 s hard bound; peak child RSS 2,239,608 KiB). Process completion is not a geometry pass. Exact frozen script SHA: 7cac8e75cf5488a62946ecddf90da5bd491d77030d3a6ec3071ec52bd23dcad8. Native report SHA: 90898f809647258cb1e2c3860437a3d8df30e18e554df25eedbd287f08fd662c.

## Direct wheel-conflict evidence

Second tread bounds, world metres: X [-3.9499998987, -2.9999999106], Y [1.4599999823, 1.5799999796], Z [0.9234999735, 0.9324999731]. Every witness below lies on an evaluated original triangle and is strictly inside this eight-corner axis-aligned box. The listed margin is the minimum coordinate distance to a box face, independently recomputed from the native report. It is not total penetration depth or a shortest clearance to the vehicle. Original component 0 in each row is an analytical exact-coordinate-seam-connected component; it is not a factory part number.

| Original object | Triangle | Point world X,Y,Z (m) | Minimum box-face margin (mm) |
|---|---:|---|---:|
| BL_Hub_0_cover | 267 | -3.132675290, 1.489463985, 0.923647493 | 0.147520 |
| BL_Rim_0_bead_lock | 78 | -3.391769171, 1.460500002, 0.930000007 | 0.500020 |
| BL_Rim_0_pressed_dish | 1614 | -3.377812986, 1.465316072, 0.927999973 | 4.500000 |
| BL_Tyre_0_VI203_profile | 362 | -3.416509937, 1.460790330, 0.931334525 | 0.790348 |
| BL_Tyre_0_mould_ring_-1_0.38 | 848 | -3.414038777, 1.470487416, 0.928547412 | 3.952561 |
| BL_Tyre_0_mould_ring_-1_0.49 | 896 | -3.535841703, 1.492772818, 0.925837517 | 2.337543 |
| BL_Tyre_0_mould_ring_-1_0.635 | 928 | -3.687955760, 1.476119639, 0.927999973 | 4.500000 |
| BL_Tyre_0_vent_-1_18 | 0 | -3.640916228, 1.487322092, 0.932367504 | 0.132469 |

The tyre profile occupies X [-3.809000015, -2.351000071], Y [0.884500027, 1.490499973], Z [0.0209999997, 1.478999972] m. The hub cover occupies X [-3.263999939, -2.895999908], Y [1.457000017, 1.491999984], Z [0.565999985, 0.934000015] m. Detailed rim/tyre-part bounds and all triangle-pair IDs remain in the native evidence. These are current authored vehicle dimensions, not manufacturer measurements.

## Retained coexistence and tools, kept separate

- Twenty tread-box witness pairs are intentional diagnostic coexistence with the previously authored low-step scheme: eighteen BL_Step_-1_* bars, plus BL_Cab_-1_step against both tread boxes. They remain present; this is not authorization to remove them
- Four tread-box witness pairs are the hidden CUTTER_Central_cover_* Boolean authoring tools. Actual modifier references establish that role; they are not counted as physical vehicle parts or wheel conflicts
- The old upper platforms in cab_0062 and old support batch cab_0063 have no AABB overlap with any of the three physical study envelopes. Their minimum Z values are 1.202499986 and 1.230000019 m, versus tread top 0.932499973 m. This does not assess their own installation or excuse their existing body/door contacts
- No actual cab body/door, chassis or suspension surface occurs in the physical-envelope overlapping-pair list at this saved state. Whole-scene componentwise AABB gaps are only sufficient separation where positive; no continuous or whole-vehicle safe-fit claim follows
- The 69 deduplicated targeted pairs contain 64 BVH surface-candidate pairs. Those candidate counts are not counts of physical collisions. The 32 tread-box witness pairs split into 8 wheel, 20 old-step and 4 tool pairs

## Frame recipe defect, no repair applied

The exact original Cube / four Exact Boolean unions / three-segment Bevel recipe reproduces the prior 1,092 vertices, 1,114 polygon faces and mathutils float32 bounds. Its triangulation has 2,188 triangles. Raw indexed topology is one connected, consistently oriented, two-incidence component, but geometric coincidence changes the interpretation:

- 366 extra exactly coincident vertices, in 177 location groups
- 478 exactly zero-length triangulated edges
- 845 triangles with exactly zero cross-product norm
- 1,461 triangles have cross-product norm below 1e-14 m² (twice triangle area), including the 845 exact zeros
- Exact-coordinate analytical welding has 418 non-two-incidence edges

The prior “one closed connected frame” result only established raw indexed incidence. It does not establish a nondegenerate embedded physical solid. This should be clarified alongside the earlier layout report. The detailed zero-edge IDs, coincident vertex groups/world locations, and degenerate-triangle indices/bounds are retained in frame-degeneracy-diagnostic.json. No Weld, repair, removal or geometry change was performed. Frame winding tests are numerical enclosed-region candidates only; frame solid validity is UNKNOWN. BVH candidates involving degenerate triangles are not mechanical clearance or robust volumetric evidence.

## Datum and source correction for the next item

The study transferred X -5.15..-2.95 m from the old upper platform extents into a lower-frame extent. That transfer was explicitly FITTED, but it has no established installation justification. The retained original low curve instead spans X -4.822999954..-3.528373480 m. Reinspection of both original iwm07/iwm12 photograph pixels shows the lower frame ahead of the first wheel, ending before the complete aft door/upper-platform span. This is a concrete wrong-datum hypothesis for the next independent refit; neither photograph supplies calibrated replacement dimensions. Do not shrink or move the tyre, infer symmetry, or carry upper-platform extents down without source evidence. Photo URLs/hashes and limits are recorded without republishing source pixels.

Upper-interface guides were never turned into solids. Three fitted station probes show why the horizontal sill minimum alone cannot define hardpoints:

- X -5.120: interface centre is about 89.778 mm from the nearest side-skin point. The upward centreline ray hits old upper-platform triangle 6 at Z1.202499986 m, 94.500 mm above the nominal interface top. The inboard Y1.48 ray reaches side skin about96.000 mm above the interface top
- X -4.035: nearest side skin is23.729 mm from the interface centre. The Y1.52 vertical ray misses within400 mm, while Y1.48 meets the sill at Z1.120000005 m,12.000 mm above the interface top
- X -2.980: the nearest original surface is the rim bead lock,42.053 mm away. The inboard upward ray encounters tyre geometry at Z1.198588252 m before the old platform at Z1.202499986 m; that is not a body mounting hardpoint

These are six finite rays and three nearest-point sets, not continuous bracket-envelope proofs. Actual upper mounts, fore/aft extent and stand-off, support section/flexibility/material, joints/fasteners, target batch applicability, and loaded wheel/suspension envelopes remain missing.

## Scope and preservation

Full broad phase retained10,353 geometry entries, comprising9,344 original geometry objects plus1,009 evaluated instance entries. Each instance was read directly from evaluated instance.object with its actual world matrix and preserved parent/persistent ID. All1,009 entries exactly duplicate their own source object world-vertex/triangle signature in this state; all entries remain in the inventory, but targeted counts include each source placement once. Source names are never merged merely because two distinct objects share coordinates. Hidden original geometry and Boolean tools were inspected, not removed. Nongeometry types are explicitly inventoried.

All10,353 evaluated position/triangle signatures read back unchanged after temporary-object removal. Original object inventory, matrices, parents, data links, visibility/selection, scene/collection flags and evaluated-instance manifests/matrices were preserved. Both the saved candidate 3b230c… and immutable original 8e962d6… remained byte-identical. These checks do not assert equality of all Blender RNA or shader displacement. The saved scalar door controls stayed0°; no doors were moved and no continuous-motion result is claimed. Six original closed-contact pairs remain OPEN.

## Failed and superseded attempts

1. Attempt01: exit17,21.837s. Explicitly refused1,009 unhandled evaluated instances before study reconstruction; no fit result
2. Attempt02: exit17,38.842s. Refused exact comparison of float64 affine diagnostic bounds with the prior float32 mathutils bounds; the later run compares the original mathutils arithmetic path exactly and records separate float64 deltas
3. Attempt03: exit17, 39.083s. Refused exact-coordinate-welded frame closure. This exposed the real coincident/degenerate output and is not dismissed as a test issue
4. Attempt04: native process completed, but its51 numerical interior rows double-counted some source/instance pairs, included authoring tools, and used an overly strong frame-solid interpretation. It is SUPERSEDED, not accepted installation evidence; its script/log/process/report remain unchanged
5. Attempt05: final bounded diagnostic. Instance geometry read directly/deduplicated by source+signature, tools identified through Boolean references, degeneracy locations retained, and frame-solid claims explicitly withheld. The layout result is FAIL for installation

## Replay and evidence packaging

The actual executed workspace was /workspace/scratch/a29d03198654/maz-step-installation-fit-20261001. All attempts contain their exact commands, at-launch frozen executed-script.py, logs and process metadata. Only attempts04/05 froze the runner at launch; attempt03’s explicitly named retrospective-runner-source-copy.py was copied later, and no at-launch runner-hash claim is made for attempts01–03. See PROVENANCE_NOTES.json. Those historical paths are not a promise that files exist at the same location after publication. No files from this task were written into the repository.

The portable run-bounded.py takes explicit --blender, --repo, --candidate and --layout-report paths plus a new --run-name. It copies the script/runner into a fresh run directory and enforces CPU1/240s. It was syntax/help checked after the final run, not presented as the historically executed runner. The only saved candidate remains local-only while new LFS upload is blocked; replay requires materializing that exact3b230c… input. The layout report must have SHA032e788a… .

pack-evidence.py packs only ordinary text diagnostics using JSON field dictionaries and array shards, with all native values retained. Restore via python pack-evidence.py restore --bundle PUBLICATION_FOLDER --out NEW_RESTORE_FOLDER. The package verifies exact native original byte lengths/SHA after restoring; it contains no model, texture, source photograph or encoded replacement asset. The exploratory attempt04 full broad inventory remains in the work directory; its report/script/log/process are retained in the package solely as superseded history.

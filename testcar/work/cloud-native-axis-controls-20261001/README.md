# Native fitted barrel-axis door controls

Current delivery update (2026-10-02): the unchanged native source and original closed/open PNG files are now completely published through the GitHub plugin at testcar/outputs/cloud-native-door-axis-20261002. Independent remote byte restoration and corrected native fresh-open passed. The LOCAL_ONLY/LFS-blocked labels below describe the historical run, and are superseded for artifact delivery only; all original mechanical/acceptance limits remain. See testcar/work/cloud-door-source-delivery-20261002/delivery.json.

Status: saved native controls passed a fresh Blender 4.5.13 reopen with autoexec disabled. The one candidate remains `LOCAL_ONLY_LFS_BLOCKED`; no asset upload or production promotion occurred.

## Actual final results

- Candidate: `MAZ543A_Native_Barrel_Axis_Controls.blend`, 67,937,160 bytes
- Candidate SHA-256: `3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f`
- Replay script SHA-256: `4390d1566fce69cff30e336ae21137d74b1927fff1067dedcbdd7b7ca71b95d9`
- Native build: exit 0, 175.456s, CPU1, peak RSS 2,205,040 KiB
- Fresh verification: exit 0, 187.631s, CPU1, peak RSS 2,581,024 KiB; autoexec disabled and no driver expression/target rewrite
- 44 states × 44 actual evaluated parts, 528 barrel-center checks and 1,320 exact closed-part comparisons in each run
- Maximum barrel-center drift: 0.382438µm; maximum actual vertex/formula error: 0.382997µm, against the unchanged 20µm threshold
- Maximum signed-angle error: 9.65934550834e-06 degrees. At 99 degrees, actual signs are ±98.999999292 degrees; sampled shell-tip travel is 1.314–1.421m
- All 10,434 original object names/type/data bindings/hierarchy and the explicitly compared rest fields below are retained. In-memory original object/mesh ID pointers are exact; fresh-file identity is checked by inventory and named bindings rather than process-local pointer addresses. All 7,470 stored mesh signatures match; source/candidate SHA checks pass
- Full actual reports are `build-report.json` and `verify-report.json`; bounded process receipts/logs and exact executed-script snapshots are retained

The `.blend` exists only at the explicitly recorded outside-repository local path in `completion-summary.json`. Text/script evidence can be published separately; that does not publish the native asset.

## Change

`native-door-axis-controls.py` installs an editable `open_angle_deg` custom property on the four original EMPTY controllers `cab_pivot_002`, `cab_pivot_003`, `cab_pivot_006`, and `cab_pivot_007`. The property has a 0–99 degree UI range and closed default 0. Source-side signs remain +,+,−,−. Original quaternion rotation mode, object identities, parent/child hierarchy, original authored transform values and pre-existing custom properties are retained. The previous authored values and fitted axis are also recorded in each controller's `maz_native_axis_control_v1` metadata.

No origin or parent operation, mesh creation/edit, object deletion/hiding, body movement, rivet repair, new step geometry, scene animation, handler registration, trusted autoexec, or software installation is involved.

Exactly 16 native simple-expression drivers are installed: four on each controller, targeting location X/Y and quaternion W/Z. Each reads only that same controller's undriven scalar property through one SINGLE_PROP variable. No transform, scene/frame, other-ID, Python namespace, or context variable is used; no Action, NLA, FCurve modifier, keyframe or sampled point is added. Exact driver topology, expression, variables, flags, validity and simple-expression status are checked.

The local motion is `original_basis @ Translation(p − Rz(angle) p) @ Rz(angle)`. The actual source is explicitly checked to have identity rest quaternion/scale/delta transforms and the expected static identity-parent chain before using this narrow implementation. Unsupported structure is rejected. The two translation expressions use `L + p*(1−cos) ± q*sin` so zero degrees has exactly zero correction. The local axis comes from the original 12 barrel meshes and pinned prior axis evidence, not from factory dimensions.

## Input

Original source (read-only): `testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend`

SHA-256: `8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70`

Blender: official 4.5.13 LTS. The actual executable SHA-256 is recorded by each bounded launcher process receipt. Source/evidence hashes are pinned by the script. The source is never saved or overwritten.

## Use and replay

In Blender select one of the four original hinge EMPTYs, then edit Object Properties → Custom Properties → `open_angle_deg`. Zero is closed; 99 is the maximum. Quaternion transform channels are now driven; the angle property is the intended editing control. No auto-executed Python is needed for the saved drivers.

Run the script with explicit testcar and outside-repository work paths:

```
"$BLENDER" --background --factory-startup --disable-autoexec --threads 1 \
  --python-exit-code 17 --python native-door-axis-controls.py -- \
  --testcar-root "$TESTCAR" --out "$OUT" --mode trial
```

`trial` never saves. `build` repeats the complete in-memory validation and saves one new `MAZ543A_Native_Barrel_Axis_Controls.blend` only if the path is absent and every gate passed. It refuses overwrite. `verify` opens the original read-only baseline, then freshly opens that candidate and checks identity and all positive poses without changing any saved driver expression or target. Its changes are limited to bounded scalar angle edits in memory; it never saves.

The supplied `run-bounded.py` is the actual workspace launcher, with a 240-second subprocess deadline, CPU1, exact process exit, elapsed time, RSS, start/end script hash, source hash and log hash. Paths in this local launcher identify the execution environment; adapt them deliberately for another installation. These timings are not isolated performance benchmarks.

## Verification scope

- 44 states: each controller individually at 0, 0.731, 15, 37.125, 45, 75, 83.61 and 99 degrees; six simultaneous/mixed states; three repeat full-open/full-close cycles
- All 44 moving parts at every state: actual evaluated vertices follow the measured-axis formula below the unchanged 20µm threshold; triangle indices stay exact
- Actual evaluated signed angle and farthest shell-tip travel provide nonzero-motion witnesses, so stationary invalid controls cannot pass by reporting zero barrel drift
- All 12 actual evaluated barrel centers per state stay below the unchanged 20µm drift gate
- Closed evaluated vertex arrays, triangle arrays and world matrices are numerically exactly equal by NumPy array_equal against the original source (not a separate bytewise/signed-zero comparison); repeated closure restores them exactly
- All 10,434 objects match the explicit rest-field comparison below, except the intentional new control properties and driver animation data. Unrelated objects retain the explicit transform fields in every sampled state
- All 7,470 original stored mesh signatures include positions, index topology, selection/hide/smooth/seam/sharp flags, material bindings, every native attribute payload, UVs, deform weights and original shape-key positions/settings/animation. Runtime caches and computed normals are excluded; custom split-normal attribute storage is included
- Invalid value/type/default/range, damaged metadata axis, nonidentity rest rotation, muted/wrong-expression driver and transform-feedback target are rejected

### Exact meaning of object preservation

“Object state” in the reports is the output of the replay script’s `object_state` function, not every Blender RNA field. At closed rest, it compares object type; parent name/type/bone; data-block name binding; collection membership; hide_render, hide_viewport and current-view-layer hide_get; pre-existing custom-property values; constraint type plus writable scalar RNA; modifier name/type plus writable scalar RNA and ID-pointer bindings.

The transform subrecord compares location; rotation mode; Euler, quaternion and axis-angle stored values; scale; delta location/Euler/quaternion/scale; matrix_basis, matrix_parent_inverse and matrix_world. These transform fields alone are additionally compared on all 10,386 unrelated objects at every sampled pose.

Intentional exceptions are explicit: the four controllers gain `open_angle_deg` and `maz_native_axis_control_v1`, plus four drivers each. These two new properties are removed only from the rest-field comparison view; their real values, bounds, metadata and exact driver topology are separately checked. Pre-existing custom properties remain unchanged. Driver addition means whole Blender object RNA/animation state is not claimed byte-identical. Unrelated animation records are compared by the script’s action-ID, NLA track/strip-count and detailed driver-record signature; this is not a full serialization of every animation RNA field.

Original process-local object and mesh ID pointers are checked in memory. Fresh reopen verifies the same named object inventory, parent/data bindings, explicit fields and payload signatures; it cannot retain memory addresses across processes. Mesh preservation is the separately documented stored-field signature, not an all-RNA or runtime-cache equality claim.

### Lossless small-file signature transport

The four original 1,664,080-byte mesh manifests remain unchanged and all have SHA-256 `77f22c327f85e4c2cf6e54c7840d5cec621ec01b344af207579d8c6e25c9ac2d`. The build/fresh reports retain those original filenames and hashes. For publication, `signature-pack/index.json` maps all four original names to one dataset represented by a field-schema dictionary and 10 ordinary JSON column-array shards. These compact files have their own sizes/hashes; they are not presented as the original bytes. This contains only mesh names, counts, field inventories and signature hashes, never model geometry.

Restore the exact original report-linked files in an empty destination (or beside the reports if those four filenames are absent):

```
python pack-mesh-signatures.py restore --index signature-pack/index.json --out "$RESTORED"
```

The restore command verifies every shard, reconstructs the original canonical JSON encoding and trailing newline, verifies the original size/SHA, and refuses existing output files. Actual local restore produced all four original files with exact byte equality; evidence is `signature-pack-validation.json` and the pack/restore logs. All pack files are below 150KB; the largest is 98,648 bytes, total 927,475 bytes. Original full files and actual restored readback copies are retained locally. No Blender run or native save was performed for this delivery-only step.

UI bounds and the public `set_angle` helper accept only finite numbers in [0,99]. Direct raw Python assignment can bypass UI bounds. Out-of-range raw assignment is tested to invalidate all four native expressions and is rejected by the validator; it may leave invalid evaluation requiring restoration/reset. This is not automatic fail-closed mechanical behavior. Do not interpret an invalid or clamped property as a valid pose.

## Failed attempt retained

`trial-attempt01-script.py`, its report/log/process receipt preserve the initial guarded failure: the raw-mesh preservation checker rejected an unrelated original spring shape-key mesh before installing controls. The accepted checker adds explicit preservation signatures for the original shape-key coordinates, settings, relative-key identity and animation; it does not remove those keys or reduce numerical motion tolerances.

The trial/build logs intentionally contain four native Math Domain Error lines when the negative test injects an out-of-range raw value of 100. All four drivers become invalid as expected, then are restored and checked valid before save. These are recorded rejection tests, not accepted motion.

`trial-attempt02-script.py` and its actual report/log/process receipt preserve the first complete in-memory pass. A static review then identified that a fresh-reopen test must precede any negative mutation that rewrites expressions. The final script runs pristine positive motion first; fresh `verify` mode skips expression/target mutation entirely. It also checks the original source hash after native save, not only before.

## Limits and delivery

The candidate is explicitly `LOCAL_ONLY_LFS_BLOCKED`. It is not a production promotion, Git/LFS delivery, uploaded asset or browser model replacement. No LFS pointer or Git object is created by these scripts.

All six original closed contacts and all 16 whole-vehicle gates remain OPEN. Exact retained closed geometry does not resolve those contacts. No new collision/continuous-clearance, scene-animation, physics, manufacturer/batch, material strength, hidden hinge mechanism, native rendering or browser acceptance is claimed. This work provides a real editable native motion correction about the already fitted original barrels only.

## Repository publication boundary

This evidence copy and the canonical `scripts/native-door-axis-controls.py` are
ordinary Git text deliverables. The candidate remains outside the checkout; no
`.blend` pointer or encoded substitute is included. The canonical script bytes
are identical to the executed4390d156… revision. All four original signature
files can be restored from `signature-pack/index.json`; native reports still refer
to their original names/SHA. An additional parent restore check verifies those
bytes and the actual source/candidate/script hashes without rerunning Blender.
The140-head attachment repair and independent step layout are NOT composed into
this native-axis-only candidate. All original mesh coordinates are retained.

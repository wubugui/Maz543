# Native saved four-door controls: two actual endpoint renders

Current delivery update (2026-10-02): the unchanged native source and original closed/open PNG files are now completely published through the GitHub plugin at testcar/outputs/cloud-native-door-axis-20261002. Independent remote byte restoration and corrected native fresh-open passed. The LOCAL_ONLY/LFS-blocked labels below describe the historical run, and are superseded for artifact delivery only; all original mechanical/acceptance limits remain. See testcar/work/cloud-door-source-delivery-20261002/delivery.json.

Status: **two same-camera native views accepted for bounded visual inspection**. The actual PNG pixels were opened and reviewed. This is not whole-vehicle, browser, continuous-clearance, materials, manufacturer/batch, or physical-mechanism acceptance.

The candidate remains **LOCAL_ONLY_LFS_BLOCKED**. Nothing was uploaded, published, promoted, saved, or re-exported by this task. The original six closed contacts and all 16 vehicle gates remain OPEN. The candidate contains only the native axis-control correction; it does not contain the separate 140-head repair or new step layout.

## Actual images

- `attempt01/closed.png`: 1,576,059 bytes; SHA-256 `87864120692a8ac6fd33cdfdc39b5493e2b304320ed3596494b41b327bfb57ad`
- `attempt01/open99.png`: 1,585,359 bytes; SHA-256 `0bbd1ee0462b738ed80b30b4e76937298052eb686a7de3385336bab2f4d99cf3`

Both are 1600 × 1100 native Cycles CPU2 renders at 32 samples with denoising. The original green materials remain; no image editing, compositing, asset substitution, or geometry edits were used. New native camera-facing FONT labels, a camera, three area lights, an explicit world, and one label-only emission material exist only during inspection.

The two near-side doors and their apertures are clear in the open image. Both far-side open door panels are visible around the opposite cab but partly occluded. The view does not show every hinge, surface, interior or contact. All four controls have independent numerical witnesses; visibility of every surface is not claimed.

## Exact source and controls

Input: `../maz-native-axis-controls-20261001/MAZ543A_Native_Barrel_Axis_Controls.blend`, 67,937,160 bytes, SHA-256 `3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f`.

Original read-only source: `../Maz543/testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend`, SHA-256 `8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70`.

Both hashes remain unchanged. The candidate was freshly opened in each process with `--background --factory-startup --disable-autoexec`; Blender preferences confirmed autoexec disabled. The builder was not imported or rerun. Saved expressions and targets were read and compared against the actual fresh-verification report, never rewritten.

Only the scalar `open_angle_deg` property was assigned on the original `cab_pivot_002`, `cab_pivot_003`, `cab_pivot_006`, and `cab_pivot_007` controllers. Each was update-tagged, then the view layer updated. No quaternion or location channel assignment was used. All 16 saved drivers remained valid simple expressions, with the original same-object scalar targets, no modifiers/keys/NLA/Action. They were checked before edits, at both endpoints, before render and after render.

The actual evaluated signed open angles are +98.99999929196937°, +98.99999929196937°, −98.99999929196937°, −98.99999929196937°. Sampled shell-tip displacement is 1.314436078m for the front pair and 1.420631498m for the rear pair. The closed state measures 0° with zero tip displacement. This is endpoint behavior, not a new collision or continuous-motion proof.

## Complete-cab isolation and resources

The retained scope is the entire `cab` hierarchy (598 descendants) plus all 24 cab/front/door-named geometry objects identified outside it, including original central covers, bumper, hook, crossmember, stays and mounts. There are 556 retained geometry objects, of which 472 had `hide_render=false`. All original in-scope render flags and collection flags are unchanged; all old geometry in this scope remains. 9,467 originally render-visible out-of-scope objects, including external lights/cameras/empties and vehicle geometry, are temporarily hidden. Every name and original flag is recorded. The full vehicle is not present in these images, as the labels state.

The separate preflight audits all 13 image datablocks and all three fonts before rendering. There are zero missing unpacked image or font references. Packed images and the packed DejaVu Sans font remain packed; builtin fonts remain builtin. No paths were remapped or resources reloaded/substituted. Original material bindings are unchanged. No cab/body surface was removed to improve a collision result.

Both endpoints were evaluated first to form a shared world union bound, with minimum `[-5.749101161956787, -2.4784822360002465, 0.572361325024566]` and maximum `[-2.8570001125335693, 2.4784822360002465, 2.994999885559082]`. The identical elevated front-left orthographic camera encloses that union with margins; camera matrix, scale, bound projections, light and color settings compare exactly across reports. AgX, Medium High Contrast, exposure 0 and gamma 1 are explicit; inherited compositor and sequencer are disabled.

## Execution evidence

Official Blender 4.5.13 LTS executable SHA-256: `e3ce4e960a2fd3beb1f9d2299e38b3804475ccd395193013aec239a4b75bfbfe`.

- Resource preflight: exit 0, 10.989 seconds, peak child RSS 1,863,528 KiB
- Closed: exit 0, 65.490 seconds, peak child RSS 3,229,848 KiB
- Open 99°: exit 0, 65.284 seconds, peak child RSS 3,229,180 KiB

Each process had a separate 240-second subprocess deadline and CPU2 thread settings. Timings are actual wall time, not isolated performance benchmarks. No timeout or failed render attempt occurred. Actual logs and process receipts are retained. The launcher froze an exact executed-script copy before each invocation and records its hash before/after alongside executable, source and output hashes.

`render-native-controls.py`, `closed-attempt01-executed-script.py`, and `open99-attempt01-executed-script.py` all have SHA-256 `a15467d582745b46efdcad21edfe8594c327ca54524de99b7251554a19e2237d`.

## Replay

`inspect-resources.py` audits a candidate into an explicitly supplied output JSON. `render-native-controls.py` accepts `--candidate`, `--verification` (the actual native controls `verify-report.json`), `--resource-audit`, `--out`, and `--pose closed|open99`. It refuses existing report/image filenames and never saves a blend. The full reports pin the actual verification and resource-audit hashes used. The script performs both endpoint checks to frame the same union in each invocation, then renders the requested endpoint.

`run-bounded.py` is the actual launcher, with this workspace's explicit official Blender/source locations. Use `--script SCRIPT --name UNIQUE_RUN --` followed by the script arguments. Keep each run name and image output path new; no failure overwriting. For another machine, deliberately adapt the paths while keeping the same pinned source/Blender versions and record the newly executed launcher/script hashes. Do not treat an adapted runner as the original executed copy.

Example for this exact workspace (the current `attempt01` files already exist, so choose a new output directory and unique run name):

```sh
python run-bounded.py --script render-native-controls.py --name replay-closed -- \
  --candidate ../maz-native-axis-controls-20261001/MAZ543A_Native_Barrel_Axis_Controls.blend \
  --verification ../maz-native-axis-controls-20261001/verify-report.json \
  --resource-audit resource-audit.json --out replay-new --pose closed
```

The candidate is not in Git/LFS. A checkout containing only the published text evidence cannot replay this exact file without obtaining the matching source asset. Rebuilding from the original source is a distinct run requiring fresh hash and verification, not recovery of the existing candidate's bytes.

## Full reports and ordinary small-file transport

The original reports remain unchanged: `resource-audit.json`, `attempt01/closed-render-report.json` and `attempt01/open99-render-report.json`. Each complete native render report includes the complete 9,467-name isolation inventory, original retained scope and all driver/witness information. Its terminal status is `NATIVE_RENDER_COMPLETE_PENDING_PIXEL_REVIEW`; the separate later `pixel-review.json` records the actual accepted visual review rather than rewriting the native report and invalidating its process hash.

`render-summary.json` is the readable machine summary. `pixel-review.json`, `report-pack-validation.json`, final hash manifest, actual logs/process receipts, and frozen executed scripts provide supporting evidence.

For bounded ordinary-Git publication, `pack-json-evidence.py` splits large top-level report arrays into ordinary JSON array shards and deduplicates identical shards. It does not encode or transport the model, materials, textures or a Blender asset. `report-pack/index.json` preserves original key order, byte sizes and SHA-256. Every raw report was actually restored into `report-restore-readback/` and compared byte-for-byte against the unchanged original. Run:

```sh
python pack-json-evidence.py restore --index report-pack/index.json --out NEW_EMPTY_DIRECTORY
```

The restored original bytes recover the exact report hashes already named in native process receipts; compact transport hashes are distinct. Restore refuses existing destination files. Full originals, transport and readback are all retained locally.

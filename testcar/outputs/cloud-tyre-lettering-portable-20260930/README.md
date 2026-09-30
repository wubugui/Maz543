# MAZ543A tyre-lettering candidate

NOT PRODUCTION / NOT WHOLE-VEHICLE ACCEPTANCE. Do not replace current production files before actual browser review.

These two portable Blender 4.5.13 files preserve editable text sources, fitted raised tyre glyphs and the old misplaced geometry. The portable-paired asset is `maz543a-blender-portable-reexport-v2.glb`; it has passed scoped decoded-asset checks and independent byte-identical re-export. The earlier `maz543a-blender-candidate.glb` remains preserved as v1 with the strict tangent mismatch documented below. Images are actual native Cycles inspection renders, not webpage screenshots. The current source model and tyre letter style/fitment are not factory-calibrated. All 16 acceptance gates remain OPEN.

This candidate starts from rear-box-frame-20260930 and does not include the separate unaccepted three-cover candidate. See ../../docs/CLOUD_TYRE_LETTERING_20260930.md. Original reference-image attribution remains in external/maz543-references/REFERENCE_NOTES.md.

## Recheck the delivered files

Install the locked JavaScript dependencies in `testcar` and use official Blender 4.5.13. Run from `testcar`; replace the Blender path below with your verified installation. The commands write reports or reconstructed exports under `work`, not to the production model paths. They do not require the untracked original cloud build folder.

```bash
BLENDER=/path/to/blender-4.5.13/blender
MAZ_CANDIDATE_GLB=outputs/cloud-tyre-lettering-portable-20260930/maz543a-blender-portable-reexport-v2.glb \
node scripts/verify-tyre-lettering-asset.mjs
MAZ_LETTERING_DIR="$PWD/outputs/cloud-tyre-lettering-portable-20260930" \
MAZ_NATIVE_REPORT="$PWD/work/cloud-tyre-audit/native-readback.json" \
"$BLENDER" --background --threads 4 --python-exit-code 1 \
  --python scripts/verify-tyre-lettering-native.py
```

## Reproduce an export from the delivered editable Textured master

```bash
"$BLENDER" --background --threads 4 --python-exit-code 1 \
  --python scripts/export-tyre-lettering-candidate.py
"$BLENDER" --background --threads 4 --python-exit-code 1 \
  --python scripts/prepare-tyre-glyph-reference.py
cp outputs/cloud-tyre-lettering-portable-20260930/pack-config.json \
  work/cloud-tyre-reproduce/pack-config.json
node scripts/preserve-unmodified-body-streams.mjs \
  outputs/cloud-tyre-lettering-portable-20260930/pack-config.json
MAZ_LETTERING_DIR=work/cloud-tyre-reproduce \
MAZ_REPORT_PATH=work/cloud-tyre-reproduce/asset-verification.json \
node scripts/verify-tyre-lettering-asset.mjs
```

The explicit pack configuration retains the eight changed wheel-rubber nodes and 144 added glyph nodes. Its output is a separate reconstructed candidate. It does not publish or promote that candidate. Passing these checks still requires later actual browser/runtime and reference-accuracy review.

### Observed reproducibility limitation

The clean reconstruction was actually executed from these portable files. Scoped checks passed again, but the resulting GLB SHA-256 was `a97860806ba1ff70b61cd7a01ac173f0f461c380704ab06246cd9352660ac422`, not the delivered `0222c801…` hash. A stricter decoded-stream comparison retained a **failure**: 417 primitive streams are byte-identical; wheel 051's stream differs by one encoded byte, with two tangent-vector entries differing by 0.000488400459 in one component. Position, normal and both UV multisets match exactly, as do the oriented triangle-attribute sets excluding tangents. The material uses a normal map; visual parity is not inferred. The reconstructed GLB remains under `work`, and has not replaced the delivered candidate or production.

Run `node scripts/compare-reproduced-tyre-streams.mjs` for that strict diagnostic after reconstruction. It deliberately exits nonzero for the recorded mismatch; the test has not been relaxed to manufacture a pass. See `reexport-comparison-failed.json`. Actual browser verification remains required.

### Portable-paired candidate v2

Rather than masking the v1 mismatch, the actual portable-master export is retained as the separately named `maz543a-blender-portable-reexport-v2.glb`, SHA-256 `a97860806ba1ff70b61cd7a01ac173f0f461c380704ab06246cd9352660ac422`. Independent exports with one and four Blender threads produced the same final packed bytes. All 418 primitive streams compare byte-identically between v2 and the independent reconstruction. The v1 failure remains recorded; neither asset has been promoted or browser-accepted.

```bash
MAZ_REEXPORT_REPORT=work/cloud-tyre-reproduce/v2-comparison.json \
node scripts/compare-reproduced-tyre-streams.mjs \
  outputs/cloud-tyre-lettering-portable-20260930/maz543a-blender-portable-reexport-v2.glb \
  work/cloud-tyre-reproduce/maz543a-blender-candidate.glb
```

Control experiments: re-exporting the unpacked source and a save-only copy both reproduced v1 exactly; packing source-reference images, with or without an image reload, reproduced the v2 result. These controls narrow the trigger to the packing workflow, without claiming the deeper Blender tangent-generation cause is established. The experimental direct-pack helper was not adopted.

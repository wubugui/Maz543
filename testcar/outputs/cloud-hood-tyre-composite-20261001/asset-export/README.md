# Combined candidate raw asset exports

These GLBs are independent raw exports of the saved Textured composite. They are not production replacements or browser-accepted assets. All 16 vehicle gates remain OPEN; the native strict evaluated-UV failure also remains unresolved.

The initial 14-bit-position export passed 144 decoded glyph comparisons (maximum 1.50 micrometres) but failed the unchanged 20-micrometre hood transport threshold: front panel error was 51.27 micrometres. Its files and failed report remain under `v1`.

`v2` increases Draco position quantization from 14 to 18 bits without changing geometry or loosening the threshold. Actual decoder checks pass for the front panel/two grips (maximum 3.343 micrometres) and 144 glyphs (0.304 micrometres). Both exports pass glTF Validator with zero errors/warnings. Validator reports unsupported Draco extension and unused-object/tangent information; that alone does not validate compressed geometry. The separate actual Draco checks cover only the stated parts.

The exporter reported missing tangents on some existing meshes. No claim is made that their PBR appearance, every shader, or all original geometry streams are preserved. This stage intentionally does not use the old tyre-only pack configuration, which would discard hood changes. A reviewed combined scope and native correspondence are still needed before selecting any packed asset for browser review.

## Reproduce

From `testcar`, use the verified Blender 4.5.13 with `MAZ_LETTERING_DIR` pointing to the saved composite and `MAZ_OUTPUT_DIR` to a new output directory. Run `scripts/export-tyre-lettering-candidate.py` with `MAZ_DRACO_POSITION_BITS=18` for v2. Generate native references using `prepare-tyre-glyph-reference.py` and `prepare-composite-hood-reference.py` against the same immutable Textured source.

Set `MAZ_COMPOSITE_EXPORT_DIR` to that new directory and run `node scripts/verify-composite-glyph-transport.mjs` and `node scripts/verify-composite-hood-transport.mjs`. The hood checker writes its report before failing the threshold so failures remain reviewable. These are static decoded-asset checks, not browser executions or continuous mechanism tests.

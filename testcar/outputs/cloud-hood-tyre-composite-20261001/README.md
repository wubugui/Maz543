# Continuous hood and tyre-lettering integration candidate

This combines the second photo-guided continuous hood relief with the existing native tyre-lettering restoration. Both editable vehicle files remain independent candidates. Production is unchanged and all 16 vehicle acceptance gates remain OPEN.

## Verified scope

The restoration ran successfully against the exact hood input SHA values recorded in `lettering-verification.json`. Both saved files reopen; 144 glyphs per file pass the existing closed-mesh and correspondence checks (288 results, maximum Master/Textured world correspondence 0.477 micrometres).

`integration-preservation.json` confirms 8570 Master and 6926 Textured original objects outside the deliberately changed typography scope preserve evaluated positions/triangles, world transforms, parents, visibility, authored mesh UVs, editable modifier inputs and material slot names exactly. The new glyphs retain the correct eight wheel-spin parents. This is not an assertion that every shader parameter or runtime operation was tested.

## Strict failure retained

The combined verification exits 1 because evaluated UV hashes differ on 3170 Master and 2277 Textured objects. No numerical tolerance or exception converts this gate to PASS. Controls on the front panel find small UV differences even between repeated evaluations of the unchanged input (up to roughly 3e-7 UV units), while all-modifiers-disabled authored UVs match exactly. The one-thread control still varies. This is evidence of pre-existing evaluation variability, not proof that every observed candidate difference is harmless or that textures have passed visual/export review.

The ordinary modifier IDProperties inspection failure is retained in `integration-preservation-scoped.log`; the corrected verifier's actual result is in `integration-preservation-scoped-v2.log`. Earlier strict and diagnostic failures remain available. `uv-readback-diagnostic.log` includes a final API-introspection error after its data report had been written; successful repeat controls provide the separate evidence.

No new GLB has been produced. `hood-tyre-composite-whole-front.png` is the actual combined Master candidate rendered at 1400×1000, 64 Cycles CPU samples with denoising disabled; it completed successfully and was visually inspected. Whole-vehicle corner framing and all added glyphs inside the vehicle envelope were checked. Visible grain/glass rendering remains unaccepted. Previous hood images predate the lettering integration and must not be relabelled as combined-candidate screenshots. Existing hood-lock/lip intersections and fitted, non-OEM hood dimensions remain unresolved.

## Reproduction

Use the verified matching Blender 4.5.13 installation. Run `restore-tyre-lettering.py` with `MAZ_TYRE_INPUT_DIR` pointing to the hood candidate and `MAZ_TYRE_RESTORE_OUTPUT_DIR` to a new candidate directory. The exact archived run used this directory. `verify-tyre-lettering-native.py` uses `MAZ_LETTERING_DIR`; `verify-hood-tyre-integration.py` targets this study and intentionally exits nonzero on its strict UV condition.

`diagnose-hood-evaluated-uv-repeat.py` performs the focused read-only repeated evaluation control. Set `MAZ_UV_CONTROL_OUTPUT` to a new directory to preserve prior reports and run with threads 1 or 4. Modifier visibility changes occur only in memory and are never saved to either master. Its portable path rewrite was syntax checked; existing `uv-repeat-control.*` and `uv-one-thread-control/` results came from the equivalent original diagnostic scripts, retained as evidence.

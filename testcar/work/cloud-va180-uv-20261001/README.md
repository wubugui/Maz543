# Re-encoded inherited mesh UV verification

Follow-up to the Textured/GLB candidate d1aa9ba. The four-seat-base mesh and
steering column are the only inherited meshes whose compressed geometry streams
changed. This check narrows the prior unverified UV transport statement.

Fresh Blender 4.5.13 readback supplies actual evaluated triangle-corner positions
and UVs. The source file is not edited or saved. Actual Draco payload decoding is
compared with a bijection of triangles and joint position/UV corners, preserving
cyclic winding. This checks 1200 seat-base triangles and 96 column triangles, with
no unmatched corners or triangles. It does not average UV seams or use modulo
wrapping to hide errors.

Maximum coordinate UV errors are 0.0000893511 and 0.0001221895 respectively. Both
are below half a 12-bit unit-range quantization step plus a 0.0000002 numerical
allowance. The official installed Blender exporter declares 12 UV bits by default
(`io_scene_gltf2/__init__.py`, export_draco_texcoord_quantization); this is the
fresh-process export setting used in d1aa9ba. Native ranges are explicitly checked
as [0,1]. Position error is bounded at 20 micrometres, maximum observed 8.191.
Synthetic controls reject UV corruption, position corruption and reversed winding,
and accept cyclic triangle reorder.

Reproduce from testcar: run `scripts/read-va180-reencoded-uv.py` in fresh Blender,
then `node scripts/verify-va180-reencoded-uv.mjs`. The latter uses the repository's
existing Draco decoder. It does not load a browser.

This establishes scoped, quantized triangle-corner UV preservation for these two
meshes. It does not establish identical rendered pixels, lighting/material
appearance, arbitrary later poses, browser behavior or whole-vehicle acceptance.
All 16 vehicle gates remain OPEN. No source model or production asset changed.

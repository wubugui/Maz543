# Textured cab / VA180 review candidate

This is an independent, editable Textured sibling of the already published native
Master cab candidate. Production is unchanged. All 16 whole-vehicle gates remain
OPEN, including known column/cushion and panel/wall installation contacts.

`MAZ543A_Textured.blend` retains the prior Textured sibling's own seat UVs and
materials, adds both panel studies, applies the exact published fitted steering
pose, and appends the same partial VA180 visual study at the fitted B4 hole. Four
seat-base regions survive native Separate with their semantic and geometry
identity. All 28 appended source objects pass fresh readback. Caption64 conflict,
unknown factory dimensions, electrical calibration and internal structure remain
unresolved. The source and reference hashes are recorded in `textured-pipeline.json`.

The independent development entry is `?asset-review=cab-va180-v1`, with delivered
asset `public/models/review/maz543a-cab-va180-v1.glb`. It is disabled in production
and render-worker/worker-build contexts. The entry preserves candidate metadata
when exporting a posed model. It is not a verified browser experience: cloud
preview access remains blocked and was not retried through another route.

Actual Draco decoding matches 261 native parts and 321 local/world poses, with
maximum bidirectional vertex distance 8.191 micrometres. Seven FONT labels are
included. The final pack retains 432 pre-existing mesh-node streams, original
materials, ordered embedded images, image/sampler bindings and samplers exactly.
Only the retained four-seat-base mesh and steering column are re-encoded; three
obsolete generic instrument nodes are omitted. Their re-encoded UV/pixel equality
is not certified. Source native conversion of 20 Curve/Font objects and temporary
native Triangulate modifiers remedy n-gon tangent fallback; the source blend is
never saved by export. Re-triangulated changed faces have maximum 0.490 micrometre
nonplanarity. One inherited multi-image sampler exporter warning remains, while
final original image/texture/sampler preservation is exact.

The first export with tangent-generation errors is retained under
`work/cloud-va180-web-20261001/iteration-01-tangent-fallback`; it was not accepted
as the final export. Final Khronos validation reports 0 errors and 0 warnings,
1806 information messages, without truncation. Draco data itself is verified by
the dedicated decoder because the validator does not support that extension.

The candidate-only steering binding extracts spin from the legacy Euler pose,
then applies it around the candidate wheel's local Y axis. It prevents every
frame from restoring the old wheel tilt and prevents the wheel normal from
precessing around the old world axis. The real binding statement passes 721
synthetic states and a deliberately failing old-loop control. The 480 old-asset
states still pass. These are code/geometry checks, not full steering linkage,
continuous clearance or browser motion acceptance. New instrument labels and the
button are static in this GLB.

Reproduction (from testcar, official Blender 4.5.13):

1. `scripts/build-textured-cab-candidate.py` uses the existing Textured baseline,
   published Master poses and existing partial VA180 study. It refuses to overwrite
   prior final/intermediate files. Intermediate native files under work are
   reproducible build products; the editable final native artifact is retained here.
2. Run `verify-va180-panel-fit.py --directory outputs/cloud-va180-textured-20261001`
   and `verify-va180-appended-identity.py` with the same directory in fresh Blender.
3. Run `export-va180-cab-candidate.py` in a fresh Blender process. It refuses to
   overwrite an existing raw export. Native references and failure history are
   retained under `work/cloud-va180-web-20261001`.
4. Run `node scripts/verify-va180-cab-transport.mjs`, then
   `node scripts/prepare-va180-cab-pack.mjs` and
   `node scripts/preserve-unmodified-body-streams.mjs work/cloud-va180-web-20261001/pack-config.json`.
5. Run `verify-va180-cab-preservation.mjs`, transport verification on the packed
   GLB, `verify-va180-pose-binding.mjs`, selector and legacy-pose checks, TypeScript
   and the application build. Retained JSON/logs distinguish each scope.

The new image is an actual native Textured Cycles capture, not a browser image.
Its source SHA and camera are recorded alongside it. No additional geometry is
hidden for this image.

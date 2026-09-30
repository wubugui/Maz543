# Driver-side front roof searchlight correction — 2026-09-30

The project remains ACTIVE. All 16 whole-vehicle gates in ACCEPTANCE.md remain OPEN.
This increment fixes the side and fore/aft placement of the existing searchlight;
it does not accept factory dimensions, lamp construction, electrical operation,
complete exterior accuracy, or photoreal rendering.

## Source and actual change

The inspected `E:/Maz543/external/maz543-references/museum-front.jpg` and
`museum-front-oblique.jpg` show the lamp above the driver's left cab, near its
front roof edge. The roof framework and box on the museum vehicle are fitted
equipment and were excluded from the chassis reconstruction. The later
`maz543a-7.jpg` / MZKT brochure is not used as an early-production dimension source.

The recovered native audit task `6c9ca96b-a3de-4fe1-a024-6b8be591746a` confirmed
the original housing, lens and stand on `cab_pivot_001` (right cab, rear).
Its downloaded report SHA256 matches the Hub result.

Blender 4.5.13 Hub task `3fa57c84-8019-4790-8358-d38b00592b7d` relocated the three
parts as one rigid assembly and reparented them to `cab_pivot_005` (left cab).
Browser coordinates of the housing centre changed from (-3.42, 2.875, -1.03) to
(-5.02, 2.875, 0.90) metres: a photographic fit, not a measured factory dimension.
Native geometry, UVs and materials were retained. The baked assembly was separated
with Blender's native Separate operator. Other object transforms were checked.
Both editable full-vehicle masters were saved and their downloads SHA256 checked.
The source builder was updated for future reconstruction without running a full rebuild.

`outputs/MAZ543A_Master.blend`, `outputs/MAZ543A_Textured.blend`, the production
`public/models/maz543a-blender.glb`, its metadata and body URL revision were updated.
Original files remain in `../restoration/searchlight-correction-20260930/`;
the raw new Hub export remains in `work/searchlight-correction-20260930/`.

## Export regression and repair

The new native export has 332 nodes rather than 360. Exactly 31 old transmission
placeholder nodes are absent; the existing runtime already removes their four
roots and installs the independent transmission module. Three named lamp nodes
were added. The effective body still has exactly 1,458,152 triangles.

Strict verification detected an unrelated decoded tyre-surface change during
whole-body re-export. It was not accepted. The separate production packaging
step `scripts/preserve-unmodified-body-streams.mjs` copies the original compressed
geometry streams for all 229 unaffected mesh nodes and uses the new export only
for the three split cab streams and three lamp objects. It remaps accessors and
buffer views, preserves materials and embedded images, and writes the actual
production GLB. The read-only verifier never replaces scene objects or changes
assets. All 229 unaffected compressed mesh streams and all three image streams
now compare byte-for-byte with the pre-change production file.

## Passed checks

- Native relocation: all six parts across both masters share the same rigid
  displacement and correct parent; local geometry and UVs retained.
- Native/browser bounds agreement: maximum deviation 1.1920929e-7 metres.
- Full-quality real browser, GTX 970 / ANGLE D3D11: HTTP 200, 3,258 real native
  meshes (baseline 3,255), no page errors; front, oblique and top views inspected.
- Left front door button and current-pose GLB download operated in the real app.
- Body GLB: zero glTF validation errors and warnings; effective triangle count,
  original embedded textures and unaffected surface streams retained.
- `node scripts/verify-model.mjs`, `npx tsc --noEmit` and `npm run build` passed.
  The model script's legacy control-rig checks are not complete rendered-vehicle
  mechanical acceptance. glTF validator does not validate Draco internals; actual
  browser decoding and bounds checks provide the scoped decoder evidence.

## Failed attempts and limits

- First Hub attempt `79536e85-3810-4857-aaa0-fe3e1a80e29b` failed on the Separate
  enum (`SELECT` instead of `SELECTED`); its partial output was never promoted.
- Corrected 8GB queued task `25f8f2d4-47c2-4ce0-816d-6d713c1df72b` was cancelled
  before execution because the shared Hub was waiting for memory. Its 4GB
  replacement succeeded, peak RSS 2,450,665,472 bytes, no GPU render request.
- The first browser capture returned the initialization control rig. It was
  rejected and overwritten after waiting for real native GLBs to load.
- Original compressed byte / decoded surface parity failed for an unaffected tyre
  in the raw Hub export. The final production packaging repairs this regression.
- Baked AO at the old mounting position needs rebaking/review. Exact mounting
  dimensions, roof contact under loads, lamp optics and electrical function,
  full-fidelity FPS, all vehicle features and subjective appearance are unaccepted.
- The inherited merged-object `detail_meshes` extras on split pieces are historical
  batch metadata, not a valid original-part count or an acceptance measure.

## Evidence and sharing

Evidence: `outputs/searchlight-correction-20260930/` (real before/after PNGs,
native verification, export parity, stream-preservation and glTF reports).
Hub submission/status/download records: `work/searchlight-correction-20260930/`.
Current-pose download is a large standalone GLB in the `after/` evidence folder.

Slack destination is the user's verified self-DM `PRIVATE_SLACK_DESTINATION` only. Independent
thread timestamp: `PRIVATE_SLACK_DESTINATION`.
Thread: PRIVATE_SLACK_DELIVERY_LINK
The historical front baseline and this round's three real before screenshots have
been uploaded and finalized there. Subsequent after screenshots and the final
stage report are sent in this same thread; local paths are not shared as attachments.

## Next implementation

Continue the documented front-face mismatches: central hinged cover, bumper and
tow-hook structure, calibrated windscreen outline, mirror arms and protective
grille. Before closing the central cover, audit actual engine/cooling envelopes
and operating clearance. Keep the engine-bay length and Cardan/torque-converter
installation issues open until reference-backed assembly closure is demonstrated.
Use the user-required native Blender curve/revolve/Boolean/modifier workflow via
Hub. Do not launch local Blender, rebuild all old modules, lower standards or
interpret this placement correction as full exterior acceptance.

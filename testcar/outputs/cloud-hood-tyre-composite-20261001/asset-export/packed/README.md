# Packed combined candidate, still unaccepted

The actual raw 18-bit native export was packed against the previously verified tyre-v2 asset, retaining 414 unrelated mesh nodes with their original compressed bytes and material definitions. Only the fixed front lip and two existing diagnostic latch meshes change; thirteen hood/grip meshes and four control/pivot nodes are added, and the obsolete single NURBS hood is removed.

The checker independently verifies original embedded texture bytes, original unaffected node transforms/parents and closed world matrices, original compressed bytes/materials, plus all 16 changed/new native primitive streams. The two diagnostic latches have explicit new parents but preserve their closed world matrices. An injected 10mm local displacement was rejected by the actual checker; no candidate was modified by that negative control.

Actual Draco decoding of this packed file confirms the three hood/grip parts match the saved native source within 3.343 micrometres and all 144 glyphs within 1.500 micrometres. Glyph precision is the preserved tyre-v2 precision, not the smaller raw 18-bit glyph error. The unchanged transport threshold is 20 micrometres. These are static transport checks, not a full-vehicle geometry, materials, browser or mechanism acceptance.

The native derived-UV bitwise FAIL remains recorded. Reusing already existing unrelated asset bytes does not make the editable native evaluation deterministic or resolve it. Lock/lip interference, fitted geometry and all 16 OPEN gates remain. Neither production nor the development browser selector was changed.

Use the retained pack configuration from `testcar` after recreating its independent work paths. `preserve-unmodified-body-streams.mjs` is the packer; `verify-composite-packed-asset.mjs` checks it. For actual decoding, point `MAZ_COMPOSITE_GLB` to the packed file and `MAZ_COMPOSITE_EXPORT_DIR` to a separate directory containing native world-reference data before invoking the hood/glyph transport checkers. Those checkers write their own reports there; do not target archived evidence directories.

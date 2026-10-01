# Driver-side asset transport

This packed candidate preserves423 unrelated mesh nodes from the prior hood/tyre asset. Four cross-cabin material meshes lose only the seven precisely separated driver parts; those seven are exported independently. The existing steering group has one declared +2.05m browser-Z translation. Its pivot identity and parent are unchanged.

The first packed iteration reused the older steering wheel streams. Actual decoding found its rim differed from the saved native source by20.3444 micrometres, exceeding the unchanged20-micrometre transport threshold. That failed file/report remains in `iteration-01-preserved-wheel-streams`.

The corrected pack uses the actual18-bit native encoding for the three wheel meshes as well. No geometric reshaping or threshold relaxation was used. All10 moved-part comparisons now pass, maximum1.3341 micrometres. The checker verifies original unaffected streams/materials/textures and every new or re-encoded native stream. glTF Validator reports0 errors and0 warnings, with informational unsupported-Draco/unused-object notices; the separate decoder check supplies actual compressed-geometry evidence.

Neither this static transport check nor the synthetic runtime-binding check is browser acceptance, complete interior accuracy or clearance validation. The previous native derived-UV strict failure and all16 vehicle gates remain OPEN.

Reproduce from `testcar`: export the saved Textured driver candidate with `export-tyre-lettering-candidate.py`, `MAZ_DRACO_POSITION_BITS=18`, and independent input/output environment paths. Prepare native world references with `prepare-left-driver-reference.py`. Use `preserve-unmodified-body-streams.mjs` with the retained configuration, followed by `verify-left-driver-packed-asset.mjs`. Run `verify-left-driver-transport.mjs` with `MAZ_COMPOSITE_EXPORT_DIR` containing those references and `MAZ_COMPOSITE_GLB` pointing to the packed file. Use new work directories to retain archived evidence.

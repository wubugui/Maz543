# Cloud tyre-lettering candidate, 2026-09-30

Status: CANDIDATE, NOT PROMOTED. The original rear-box-frame production GLB and both production masters are unchanged. This candidate is independent of the unaccepted three-cover candidate. All 16 whole-vehicle gates remain OPEN.

## Actual defect and scoped correction

The current Master contained 144 visible FONT objects for the eight tyre legends at the world origin instead of their tyre sidewalls. Each wheel's 31,060 misplaced text triangles also matched the corresponding Textured wheel-rubber mesh by an exact quantized world-triangle multiset. This was an authored placement error, not simply a missing name.

The scoped script preserves the old geometry and editable font sources. It retains the existing legend and reconstructed size/range, corrects the outward-facing readable arrangement, and uses Blender's font conversion, Shrinkwrap and Solidify to fit raised closed solids to the existing sidewall. No replacement tyre or manually constructed mesh is used. Native edit-mode separation removes only the previously matched misplaced glyph geometry from the Textured wheel streams; the other native wheel position triangles are checked unchanged.

Neither the selected VI-203 fitment nor the exact moulded letter style/size is now certified against a specific historical MAZ543A. The pre-existing source register's tyre-product/vehicle-fitment distinction still applies.

## Saved native and export checks

- Both saved native files independently reopened: 144 closed positive-volume glyphs each, with real sidewall attachment. The lower surface reaches approximately 0.050 mm into the existing tyre, and the raised surface reaches at most 0.821 mm out. These are candidate modeling values, not factory dimensions.
- Master/Textured world-vertex correspondence: maximum 0.477 micrometres after using an exact snapshot of Blender's evaluated modifier result. An earlier duplicated-modifier export differed by 105 micrometres at one vertex and was rejected without relaxing the threshold.
- Candidate GLB: 20,293,572 bytes; SHA-256 `0222c801815584c040154b7c6150a5e7953c8fa84f4c8ef82e8f9d83b2fb5cf1`.
- 266 unrelated mesh nodes retain their original compressed byte streams; three embedded texture byte streams are unchanged. Only eight wheel-rubber streams and 144 new glyph meshes are changed/added.
- Shipped Draco WASM actually decoded all 144 glyph meshes. Their standard glTF world positions differ from the saved native reference by at most 1.50 micrometres, with preserved triangle counts. glTF validation: 0 errors, 0 warnings.
- This is an asset check, not a browser check. The eight changed rubber streams are re-encoded, so this does not claim their previous decoded attribute values are bit-identical. Browser performance, final materials and runtime integration remain untested.
- Two genuine Cycles native renders use identical cameras and inspection lighting. They were visually reviewed. They are not webpage screenshots or final photorealism evidence.
- Four original exterior reference images were packed into separate portable candidate copies, checked against the migration manifest, reopened and SHA-verified. Native glyph correspondence was rerun successfully on the portable copies.

## Rear-box/tyre motion boundary

A separate read-only test derives a conservative longitudinal separating plane from actual evaluated native vertices. Under the current code's explicit motion contract—fixed rear axle X positions, zero rear steering, rigid tyres, arbitrary wheel spin, camber about X, transverse/vertical motion and common chassis rigid motion—the 12 rear-box/mount objects remain separated from all 432 rear-tyre objects by at least 53.46 mm after numerical padding.

The same construction was applied independently to actual decoded candidate bytes, including all mesh descendants of the four rear wheel-spin groups. Its minimum padded separation is 53.41 mm. The small difference includes export quantization; neither calculation silently substitutes native coordinates for decoded asset coordinates.

The argument uses a bound valid for all permitted rotation angles, not a finite time sampling. It does **not** prove original-vehicle dynamic clearance, tyre deformation, longitudinal axle/bushing flex, rear steering, clearance to other suspension/brake/body parts, real loads, full-vehicle continuous sweep, or actual browser-runtime pose parity. Those remain open.

## Cloud numerical bootstrap

Starting, cooling, transmission and the 240 Hz mechanical-timeline checks ran successfully in the cloud. The suspension test initially could not bootstrap its missing generated module because static ESM linking occurred before the preparation side effect. It now awaits preparation before dynamically importing that module. A fresh isolated workspace with the compiled module genuinely absent ran the original numerical assertions successfully. This repairs the test entry point, not the model's uncalibrated physical parameters.

## Next

Verify the actual candidate in an approved browser preview before promotion. Reconcile real hood hinge/latch/pressed-panel construction using the newly available migration references and the documented 543A catalogue; continue asymmetric equipment and fuel installation work without inventing unverified components.

## Preventing the original parenting regression

The retained legacy `blender-model.py` helper has now been narrowly repaired to update the dependency graph before capturing `matrix_world` and after reparenting. `verify-parent-keep-regression.py` extracts and executes that exact helper definition from its AST, without running the old full-vehicle generation script. Four disposable native FONT/MESH/CURVE cases reproduce the old failure (maximum matrix-element error 2.68) and pass after the repair (maximum 2.3842e-7, tolerance 2e-6). Both failed-before and passed-after results and source hashes are retained. This is a generator regression fix, not permission to regenerate or replace the current production masters.

## Portable verification and fresh re-export

The saved package initially omitted its small pack configuration and its verifier still referenced a temporary build directory. Both dependencies are now explicit in the delivered package and environment-overridable scripts. A real fresh export from the portable Textured master, fresh native vertex reference and original-stream packaging completed, and the scoped asset checks passed. The README includes tested commands that write only separate `work` results.

An additional strict decoded-attribute comparison **failed**: one wheel-rubber compressed stream has a one-byte encoding-length difference, caused by two tangent entries differing in one component by approximately 0.0004884. All 417 other primitive streams are byte-identical. The affected wheel's positions, normals, UVs and oriented surface triangle attributes excluding tangents are identical. Since its baked material includes a normal texture, no rendered-equivalence claim is made. The original delivered GLB remains unchanged; the re-export and failed evidence are retained separately. This failure does not invalidate the narrower glyph/native checks, but it prevents claiming byte-identical or visually identical reproduction.

The subsequent correction is versioned rather than concealing that failure: `maz543a-blender-portable-reexport-v2.glb` preserves the actual portable-master export under its own filename. Its SHA-256 is `a97860806ba1ff70b61cd7a01ac173f0f461c380704ab06246cd9352660ac422`. Independent one-thread and four-thread exports produced identical packaged bytes, and all 418 primitive streams match the independent reconstruction. The previous v1 asset and failed comparison are retained unchanged. Unpacked-source and save-only controls reproduced v1; reference-image packing with or without reload reproduced v2, narrowing but not fully explaining the trigger. The experimental packing change was not adopted. v2 still requires actual browser/PBR and factory-reference review.

The asset verifier now also checks all 144 real glyph nodes' motion hierarchy: each group of 18 is directly under its original wheel spin (`002,009,016,023,030,037,044,051`), then the matching carrier (`001,008,015,022,029,036,043,050`), then `wheels`. Each shares that spin with the retained rubber mesh and carries the correct tyre index. This guards against a correct closed-pose position with an incorrect moving parent; it is still not browser motion execution.

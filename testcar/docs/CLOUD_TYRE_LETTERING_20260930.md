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

# Correct driving controls to the left cabin

Independent candidate; production remains unchanged and all 16 vehicle acceptance gates remain OPEN.

## Source and error

The original 1977 technical description assigns the steering column, transmission controls, brake/fuel pedals and parking brake to the left cabin (p11 and Fig101 p174). Fig102 pp176–177 depicts the right cabin without a steering wheel. The vehicle faces -X with Blender up +Z, so its right is +Y, equivalent to browser -Z. The inherited steering group `cab_pivot_004` was in that right cabin, while the corrected searchlight already occupied the left cabin.

Original manual: https://djvu.online/file/zjMdLY3MFjmTL ; the inspected original uploaded scan has SHA-256 `cf8ebb65dcbfca6dd3b6c55a3174cfe9d628a206cb8c846eceee0041a2bb1bde`. Source p110 puts the transmission selector on the steering column. The existing floor-side lever is therefore retained as an unidentified proxy, not called an accurate gear selector.

## Bounded correction

Seven existing parts (column, two pedal links, two pedal plates, floor-side lever and knob) were separated with Blender's native Edit Mode separation from four material meshes that span both cabins. All 788 selected vertices and source face-corner UV/material records remain accounted for. No new control shape was invented and no entire cross-cabin material mesh was moved.

The seven parts and complete existing steering group share a pure -2.05m Blender-Y translation, using the existing fitted cabin-centre spacing. Geometry, orientation, handedness and fitted longitudinal/vertical placement are retained. This spacing is not a newly established factory dimension. Two fresh file reads confirm all seven parts lie in the left half-space, preserve original face data, and preserve unrelated original geometry/UVs/parents/transforms. The retained parts' existing manufacture/detail accuracy, pedal identities/order, lever identity, clearances and full interior remain unaccepted.

## Runtime dependency

The legacy viewport recopies named source-rig transforms every frame and would undo a Blender-only steering move. The new development-only `left-driver-v1` selection uses one explicit post-copy offset for `cab_pivot_004`. It does not change source rig construction or automatic pivot numbering. The actual binding statement was exercised for120 synthetic poses each under production, tyre, hood/tyre and left-driver selections: only the left-driver candidate receives the offset, it does not accumulate, and other pivots stay untouched. This is not browser execution or whole-vehicle motion acceptance.

The new native/source assertions do not resolve the earlier strict derived-UV failure, hood/lock interference or any untested mechanism. The right-cab tilt axis remains uninstalled: the source gives38° full and18° intermediate positions, but no usable three-dimensional axis or spring dimensions. Two actual same-camera native inspection images have now completed and been viewed: `left-cab-before.png` uses the prior composite; `left-cab-after.png` uses this corrected candidate. No geometry was hidden or replaced for the view. The simplified retained instruments/interior and inspection lighting are not appearance acceptance. Their precise source and image SHA values are in `render-provenance.json`. The first24-sample denoise run exited137 without an image; the later64-sample no-denoise run succeeded, without establishing the earlier cause.

The native build/readback reports record the runtime dependency as it stood before the later scoped binding patch. `browser-entry/pose-binding.json` and `selection-tests.json` document the subsequent limited checks. Final TypeScript and build checks pass; actual browser execution remains unperformed.

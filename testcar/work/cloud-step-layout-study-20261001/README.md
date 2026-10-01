# Independent MAZ step layout study

Status: bounded native layout study complete. This is not an installed vehicle fix, original factory part, or whole-vehicle acceptance. No vehicle was opened. No new `.blend` or GLB was saved. The native study was executed outside the repository. This evidence copy contains only scripts and text, not PNG or native model payloads; new LFS entity publication is not claimed.

## Result

One side has one connected lower frame, two separate plain tread envelopes, and three support stations including a shared middle station. Unknown supports are dashed orange centerlines. Unknown upper interfaces are cyan wire envelopes. Their line widths are presentation choices, not physical sections. There are no modeled cables, rods, crimps, bolts, holes, tread perforation counts, strand lays, or physics.

Actual native evaluation found one connected lower frame with zero edges having incidence other than two, plus two separate closed tread envelopes. The measured inter-region gap is 0.1700000763 m. The maximum Z of all layout geometry, including guide line thickness, is 1.1092990637 m, 0.0107009411 m below the inherited fixed sill minimum of 1.1200000048 m. This is only compliance with a chosen placement datum. It does not establish contact with a real mounting surface or clearance from body geometry.

## Reference and provenance

Before design, the actual pixels of `manual1973-1204.jpg` (figure 92), `manual1973-1218.jpg` (figure 93), and `catalog-2008-84.6.png` were inspected. The historical illustrations support a continuous lower frame with two tread areas and three support positions. Figure 93 label 17 concerns the cab-tilt cable, not these lower supports. The later catalog additionally shows upper braced forms. Its fasteners, dimensions, and revision are not applied to a 1977 target.

The 1973 attribution comes from the scan host; the title page/colophon and 1977 MAZ-543A applicability were not established. The source image hashes and inspection notes are in `PIXEL_REVIEW.json`; URLs and further historical limits remain in the input `cab-step-primary-topology-20261001.json`. Source image pixels are not republished in this deliverable.

Every design parameter has its own provenance string in the native reports and authoring script:

- Inherited, rounded model datums: one-side Y center 1.520 m, tread width 0.120 m, lower-frame center around Z 0.900 m, tread center Z 0.928 m, tread thickness 0.009 m. The tread top is approximately 0.9325 m, not 0.928 m
- Inherited exact datum: fixed side-sill minimum Z 1.1200000048 m
- Fitted frame span: X −5.150 to −2.950 m, using legacy platform outer extents as placement leads only
- Fitted tread regions: X [−5.100, −4.120] and [−3.950, −3.000] m
- Fitted station X: −5.120, −4.035 and −2.980 m, giving 1.085/1.055 m spacings. The middle is fitted to the legacy gap midpoint; none is a verified hardpoint
- Fitted rectangular frame section 0.014 × 0.047 m and 0.002 m edge treatment; these are simple modeling envelopes, not manufactured section/radius claims
- Fitted guide interval Z 0.9235–1.105 m; interface envelope size 0.080 × 0.160 × 0.014 m, centered at Z 1.101 m. Graphic radius 0.0015 m is not a support diameter

All dimensions are fitted or inherited-model data, never factory measurements. Only one side is studied; symmetry is not asserted.

## Replayable native construction

`scripts/build-step-layout-study.py` starts with a factory-empty scene in verified official Blender 4.5.13. Native Cube primitives, editable exact Boolean unions, Bevel modifier, editable Curve paths, native Font labels, cameras, and lights are used. No custom mesh vertex/face construction or encoded asset substitute is present. The Boolean tools remain editable but are hidden as construction tools; there are no original vehicle objects in this scene to move, hide, delete or reparent.

The actual executed launcher is retained as `executed-runner.py`. For portable replay use `python scripts/run-step-layout-study.py --repo /absolute/repo --blender /absolute/official/blender --out /absolute/new/outside-repo/run --view oblique` (or `elevation`) from `testcar`. The portable wrapper takes explicit paths, uses factory startup and disabled autoexec, two threads and a180-second bound. It is syntax/help checked only, not claimed to be the launcher of the recorded native runs. Each output path must be new. Inputs are SHA-pinned; the script writes IN_PROGRESS before work, never accepting a stale result after failure.

Final script SHA-256: `b295070b1d492c0d376ee732586003928bb94f12db503dbfc089dca93d152812`.

## Native views and checks

Final actual PNGs, both directly pixel-inspected:

- `oblique.png` (outside checkout): 1,630,258 bytes, SHA `e370743200dbb45f5c8ad85d343238e8d907201dd066b6f558ac7da80a129394`
- `elevation.png` (outside checkout): 1,613,160 bytes, SHA `0081e97d3e0f548681f63cc4f8d118b453a1868d1e570fc646fa77350673ad53`

Both are native Cycles CPU2, 32 samples/denoised, 1600 × 1000, explicit AgX / Medium High Contrast / exposure 0 / gamma 1. The final processes exited 0 in 23.5921 and 23.9397 seconds, each under the explicit 180-second bound. These are observed wall times, not isolated benchmarks. Script SHA before/after, log SHA, report SHA, exact command and exit are recorded for each run. The CPU1 head sweep had finished before these render windows.

All layout geometry is numerically in frame. Pixel review confirms both tread zones, three guide stations, frame continuity, readable labels, and study limitations. Elevation visibly establishes below-datum ordering; oblique supplies depth and gap context. No raster edits or composited annotations were used.

The first oblique preview failed annotation contrast. Its actual PNG, script, log, report and rejection remain under `iteration-01-oblique/`. Only graphic shader/colors were repaired. Exact report parameters, model bounds/component/count/modifier summaries and measurements match the final oblique; both final view reports also match these fields. This is not a full independent mesh-signature comparison. Four predicate-level negative controls reject a single deck, four stations, an above-sill value and overlapping tread regions; they do not claim physical collision validation.

## Preserved limits

The original current-candidate source file stayed byte-identical at SHA `8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70`; it was only hashed, never loaded in Blender. No source or production asset changed. New LFS asset upload remains unavailable; no new native asset was saved or asset data encoded as text to bypass it.

All six original closed-contact pairs remain OPEN and unchanged; this separate scene did not test or repair them. All 16 whole-vehicle gates remain OPEN. Actual hardpoints, complete support shape/material/flexibility, joints, 1977 batch applicability, physical attachment, continuous motion/clearance, fabrication, strength, and browser behavior remain unverified.

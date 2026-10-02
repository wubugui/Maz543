# Native step-frame topology correction

## Result and scope

The old defect reproduces exactly in a factory-empty Blender 4.5.13 scene. A corrected editable Cube/Difference/Bevel recipe passes the bounded evaluated-surface checks below. This is **not geometric-solid certification or installation acceptance**. Original fitted station/section/placement parameters and provenance are unchanged. The newly effective 2 mm bevel intentionally changes the evaluated shape and volume; geometry is not claimed byte-identical.

The known second-tread conflict with the front tyre/hub/rim remains FAILED. All six original closed-contact pairs and all 16 whole-vehicle gates remain OPEN. No vehicle was loaded, moved, hidden or reparented. No native asset was saved/exported; no render, repository edit, publication, browser, network or settings action was performed.

## Measured cause

The unchanged published script prefix, SHA `b295070b1d492c0d376ee732586003928bb94f12db503dbfc089dca93d152812`, is executed through native geometry construction and stopped before rendering:

- Original empty-scene result: 1,092 evaluated vertices / 2,188 triangles; 366 exact duplicate vertices; 845 exactly zero-area triangles; 1,461 triangles with cross-product norm below 1e-14 m²; 418 non-two-incidence edges after analytical exact-coordinate welding
- Raw vertex-index topology still reports one component, edge incidence two and balanced winding. Those tests alone masked the defect; the old “closed” interpretation is insufficient and must not certify a geometric solid
- Before Bevel, the four exact unions already have two tiny triangles (minimum crossnorm 7.02563e-17 m²). The first tie union already creates two duplicate positions/four tiny triangles. Thus installation is not the source
- Existing Bevel settings are ANGLE 30°, width 2 mm, three segments, overlap clamp enabled. The old bevel changes measured volume by only about 6.6e-17 m³. Disabling only overlap clamp removes the duplicate/tiny counts and changes volume; restoring it reproduces 366/1,461 exactly. This isolates the Boolean-sliver/overlap-clamped Bevel interaction in this recipe; it is not a general Blender defect claim

A pre-Bevel native Weld at 0.1 µm removes the Boolean tiny triangles but leaves two after Bevel. Adding post-Weld removes those counts but leaves three raw vertex-connectivity components. Planar-dissolve trials do not resolve that condition. All failed trials are retained. No acceptance threshold was increased and no faces were deleted to obtain a pass. Unclamped Bevel is retained as diagnosis only, not selected as the correction.

## Corrected editable construction

Use one native outer Cube with the unchanged nominal X [−5.15, −2.95] m, Y width 0.120 m and height 0.047 m. Subtract four native through-Cube tools for the open space between two 0.014 m longitudinal rails:

- End opening: X [−5.160, −5.127] m
- First internal opening: X [−5.113, −4.042] m
- Second internal opening: X [−4.028, −2.987] m
- End opening: X [−2.973, −2.940] m

Opening width is 0.092 m. The end tools extend 10 mm beyond the outer Cube, and every tool extends 10 mm beyond each Z face. Those overshoots are construction-tool settings outside the retained envelope, not new hardware dimensions. They preserve open rail ends rather than adding end closures. Remaining transverse bands are exactly the nominal 14 mm bands centered at the original fitted stations −5.120, −4.035 and −2.980 m.

**Set-equivalence applies only to these nominal real-valued, unbeveled rectangular intervals**: outer box minus four openings equals the original two-rail/three-tie union. Nominal volume is

2 × 2.200 × 0.014 × 0.047 + 3 × 0.014 × (0.120 − 2 × 0.014) × 0.047 = 0.003076808 m³.

Actual original/corrected unbeveled native volumes are 0.003076807328206 / 0.003076806870174 m³. Actual Float32 geometry is compared separately. Final modifiers are four editable EXACT Differences plus the existing fitted 2 mm / three-segment Bevel with overlap clamp still enabled. No Weld, dissolve, manual vertex/face construction or mesh deletion is used in the final recipe. The original fitted parameters/provenance exactly match the pinned original layout report.

## Final checks and quantified shape change

Final native frame: 480 vertices, 486 polygons, 964 triangles; zero exact duplicate positions; zero duplicate triangle coordinate sets; zero unused vertices; zero triangles below the unchanged 1e-14 m² crossnorm threshold. Minimum crossnorm is 4.1931192e-7 m². One connected component, all edge incidences two, balanced directed edge winding, all native BMesh vertices manifold, Euler characteristic −2, positive oriented volume.

Supplemental native BVH finds zero nonincident-triangle overlap candidates at epsilon zero. It skips pairs sharing any vertex and is not a complete self-intersection or geometric-solid proof.

Seven ordinary rail/tie sections preserve nominal 14 × 47 mm envelopes within the fixed 2 µm Float32 comparison guard. Measured top-flat setbacks are 1.999974–2.000000 mm, showing the intended fitted bevel is now effective.

Measured old degenerate → corrected bevel volume change: −0.0000190996795 m³ (−0.62076294%). Bounds change by at most 0.1192093 µm. Exhaustive Float64 point-to-triangle calculations on all vertices, unique triangulated-edge midpoints and triangle centroids give:

- Old/new unbeveled maximum directed sample distances: 0.08940697 / 0.09339731 µm
- Old degenerate/new beveled maximum directed sample distances: 1.5092177 / 0.8712982 mm
- Clean unbeveled/new beveled maximum directed sample distances: 1.5091328 / 0.8712957 mm

These are finite sampled distances, **not full-surface Hausdorff bounds**. The 2 µm guard applies only to fitted dimension comparisons, never to duplicate/tiny-triangle acceptance.

An earlier audit using native BVH nearest distances failed its 2 µm comparison (up to 377 µm on the old/new unbeveled pair). That failed report remains in attempt-04. Only the audit-distance method was replaced by exhaustive Float64 plane/edge projections; the native geometry stayed unchanged. Independent analytic controls cover 414 point/triangle, reversed-winding, rotated/thin and translated cases, plus rejection of an all-degenerate target. Maximum observed helper error is 9.58e-16 m. Degenerate triangles are omitted only from nearest-surface distance targets, never from native meshes or acceptance counts.

## Historical replay and retained evidence

- Historical final executable: `repair-and-verify-native-frame.py`
- Final script SHA: `3e84b3a24038871cb429f6e4c656d7c839589362ddeb4f74141e598ee5a5f7f4`
- Historical command: `python run-bounded.py repair-and-verify-native-frame.py NEW-UNIQUE-RUN-NAME` (prefer the portable entry below after recovery)
- Requires sibling original study script/report and current `Maz543` inputs; all are SHA-pinned. Original model is only hashed, never opened
- Final/fresh reports: `attempt-07-final/native/report.json`, `attempt-08-fresh-replay/native/report.json`
- Both reports are byte-identical at SHA `16a16158c65d2104d656eafd58f80ce61a5db7aa61570c08f5a1fae6d6aa688b`
- CPU1 native processes exited 0 in 3.226 / 3.023 seconds, each bounded externally to 120 seconds. These are observed timings, not isolated benchmarks
- Each attempt retains frozen executed script/runner, true exit, log and start/end hashes. Attempts 01–06 preserve diagnosis, unsuccessful cleanup and distance-method failure
- `FINAL_VERIFICATION.json`, `distance-helper-controls.json` and `manifest.json` summarize evidence. Every file is below 200 KB; no encoded geometry payload is stored

The original-prefix auxiliary IN_PROGRESS file is intentionally left by stopping the unchanged source before render setup; it is not this task’s process status. Actual terminal records are the enclosing `process.json` files. Read-only Blender extension-cache warnings are preserved; no configuration was changed to suppress them.


## Recommended portable entry (2026-10-02)

Use `repair-and-verify-native-frame-portable.py` with explicit required `--repo`, `--original-script`, `--original-layout-report`, and `--out` paths. The matching `run-portable-bounded.py` also requires `--blender` and `--script`; it supplies CPU1, the unchanged 120-second bound, `--disable-autoexec`, frozen executed files, and true terminal records. No sibling private scratch path or output-parent naming convention is required.

Example, with REPO set to the recovered checkout:

```sh
python /path/to/run-portable-bounded.py \
  --blender /path/to/official/blender-4.5.13-linux-x64/blender \
  --script /path/to/repair-and-verify-native-frame-portable.py \
  --repo "$REPO" \
  --original-script "$REPO/testcar/scripts/build-step-layout-study.py" \
  --original-layout-report "$REPO/testcar/work/cloud-step-layout-study-20261001/iteration-02-elevation/layout-report.json" \
  --out /outside/repository/unique-frame-verification-run
```

The original script/report are read directly from published repository paths and checked against their unchanged SHA pins. The original study's other SHA-pinned repository inputs, including the materialized original source model for hashing only, are still required. The wrapper's `--out` is the run directory; the native script receives its new `native/` child. Outputs are rejected if inside the repository.

The historical eight runs did **not** supply `--disable-autoexec`; they were factory-empty runs with no vehicle load. Their frozen scripts, runners, reports and logs are preserved byte-for-byte, with no retroactive claim about their runtime preference. The new entry explicitly requires the disabled preference at entry, after the original factory-empty prefix, and before completion; all three checks passed. It does not change persistent Blender preferences.

One bounded official Blender 4.5.13 CPU1 replay through the new entry completed in 2.973 seconds, exit 0, at `attempt-09-portable/`. The original input files came directly from the published checkout. All prior report fields except documented metadata match runs 07/08 exactly, including parameters, provenance, geometry signatures, counts, topology, volume, sampled distances, sections and checks. The script SHA and explicit path/autoexec metadata necessarily changed; the full report is **not** claimed byte-identical.

- Recommended script SHA: `13223b829fe8b66b0351ca158e419ed5c3d7213a038e38c0b99a2629f6accdee`
- Portable runner SHA: `88c390794bd0da9b7628245c689595a46ab493b5490ce336e426100da6380d4c`
- New report SHA: `25e935adc03490d470ebdfbd37932ab486bd1c317b707f9d5509482a7ab8242d`
- Comparison evidence: `PORTABLE_REPLAY_VERIFICATION.json`; historical before-hash list: `portability-before-historical-hashes.json` (48 files unchanged)

This was entry-point finishing only. No geometry, parameters, numerical criteria or modeling method changed. No new render, asset save, vehicle load or repository write occurred. The known installation failure and all 16 OPEN gates are unchanged.

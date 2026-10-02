# 离线GLB观察 / 待核对 / normal+joint FAIL / 16 OPEN

This package is **prepared, not executed**. No Blender process or image was produced
during preparation. Publish and verify this preparation before an authorized real run.
Run one view at a time: first `overview`; publish that attempt and its actual results
before starting `side`. A failed or partial image is retained and never called accepted.

This independent observation layer imports only the already published and independently
restored GLB. It does not establish the blocked webpage's loading, interaction or PNG
download behavior. Browser QA remains NOT_RUN. Do not change browsers, proxy, URL,
deployment, network or security configuration to work around the denied browser route.
No native source `.blend`, old GUI rendering call, model replacement or AI image is used.

## Exact input and official runtime

- GLB: `/workspace/scratch/a29d03198654/maz-static-glb-remote-cfe242a8-20261002/restored/native-static.glb`
- Size: 134267928 bytes
- SHA-256: `e99d275080737a520293c548d947401c6910cda3bc86d101dc57396bee9c587d`
- Source JSON inventory: 2675 nodes / 2374 unique glTF meshes / 34 materials / 5 images /
  0 animations; only `KHR_materials_transmission`. Actual imported Blender counts are
  recorded separately and are not assumed to be identical to the glTF inventory.
- Blender: `/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/blender`
- Binary SHA-256: `e3ce4e960a2fd3beb1f9d2299e38b3804475ccd395193013aec239a4b75bfbfe`
- Official 4.5.13, build `daeeeca98fb0`; installed official importer source is used.

The importer uses `NORMALS`, no vertex merge, no material-slot merge, packed images
and retained unused materials/images. Actual GLB PBR materials and textures are used
through the official importer and Cycles; this does not claim the original native
shader is visually equivalent. There is no Workbench fallback or shader replacement.

## Small, bounded execution

From `testcar`, after preparation publication and explicit execution coordination:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 work/cloud-glb-offline-observation-20261002/run_observation.py --view overview --output work/cloud-glb-offline-observation-20261002/run-overview-01 --window-note 'Describe actual concurrent work here'
```

After the overview attempt is reviewed, published and verified, separately:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 work/cloud-glb-offline-observation-20261002/run_observation.py --view side --output work/cloud-glb-offline-observation-20261002/run-side-01 --window-note 'Describe actual concurrent work here'
```

Each fresh output directory must be a direct child of this package. Existing attempts
are never overwritten. `--help` is safe and does not launch Blender. No automatic retry,
second view or fallback renderer occurs.

Each invocation pins two available CPUs with `taskset`, sets two Blender/render threads,
and renders one 1024×640 image in Cycles CPU at 16 samples, without denoising or adaptive
sampling. Low sample noise is an observation limitation. AgX color management is
explicit. Import, finite guards, Cycles BVH preparation and one render share a 900-second
wall limit. This is an operational ceiling with room beyond the past 96-second native
preload experience; it is not a prediction or performance acceptance. The native file
is not loaded here. Import and render time are measured independently when reached.

The runner emits a 10-second elapsed/stage heartbeat. The Blender script updates the
stage at import, guard, observer setup, render and final guard boundaries. Native output
is preserved in `blender.log`. Timeout/interruption signals only the runner's own newly
created process group; TERM and KILL each have a five-second grace. There is no process
tree scan or dependency on `/proc/PID/task/TID/children`. The actual terminal observation,
exit code, timeout flag, elapsed time and child peak RSS are recorded, including failures.

## Observation and finite non-mutation protection

Factory startup data is removed before import; a new in-memory scene receives the exact
GLB. Nothing opens or saves a native source, and nothing exports another GLB. Only
observer cameras, two sun lights and a world background are added. No model geometry,
pose, material, visibility or collection visibility is assigned or hidden.

The original glTF front is −X and up is +Y. The official importer maps `(X,Y,Z)` to
`(X,−Z,Y)`. Overview direction `(-1.4,+0.72,+1)` therefore becomes `(-1.4,-1,+0.72)`;
side `(0,0,+1)` becomes `(0,-1,0)`. Camera targets and framing come from actual imported
world bounds without moving the model. Overview is 35° vertical perspective; side is
orthographic, with vertical sensor fit and 12% framing margin. The camera, bounds and
settings are recorded in `observation-report.json`.

Before observer setup and after rendering, finite signatures compare imported object
identity, parent/data bindings, four transforms, visibility, material slots and collection
visibility; mesh positions, topology, corner normals, UV, vertex colors and material
assignments; material editable value properties, node/sockets/links and image bindings;
and image packed bytes, identity and color settings. Full input SHA-256 is checked
before and after. The runner additionally checks the Blender binary and all prepared
files before and after. These guards establish only their listed non-mutation scope,
not cross-engine fidelity or the existing failed normal/joint qualification.

## Labels and delivery

Every image record uses the title **离线GLB观察 / 待核对 / normal+joint FAIL / 16 OPEN**.
The raw PNG filename includes `offline-glb-pending-normal-joint-fail-16-open`.
To avoid unreliable font overlays, status is not burned into pixels: deliver each image
with its generated `README.txt` or an equally clear accompanying message carrying that
title. Keep the unchanged **2299 issues**, **FAIL_STATIC_NATIVE_TRANSPORT** and **all 16
whole-vehicle gates OPEN** visible in the delivery. Do not call this browser QA or
production acceptance.

`process.json` is authoritative for the attempt's terminal status. A successful image
must have exit 0, a timely terminal observation, intact input/preparation hashes and
the scoped post-render model guard. Preserve `launch.json`, logs, heartbeats, stage events,
before/after signatures, the report and actual PNG. Existing repository PNG LFS
attributes remain unchanged; publishing the preparation and later image bytes is handled
by the coordinating task, not this runner.

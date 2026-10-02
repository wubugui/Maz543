# Saved wheel export graph inspection preparation

**REVISION3 PREPARED, NOT EXECUTED.** Ready for independent review, followed by complete
GitHub-plugin publication/readback of this preparation before one native run.
This correction launched no Blender process and made no browser, render, model
save, GLB export, upload, runtime, Git ref/index or application change.
All 16 vehicle gates remain OPEN.

The original revision2 at `0bb73ec8f3d304e2f2cb7c80f0cd785d09fbb3f3` ran once:
run-01 exited1 in 15.773098 seconds because the inspector incorrectly assumed
rear stations4–7 had steering kingpins. Its nine original records are preserved
unchanged in `failure-01-evidence`, published and remotely recovered at
`e8bfd43ce053ec3764503cef15bf9621084663ce`. No second snapshot/graph read was
reached. Its prefilled protection description was a plan, not completed proof.
This revision corrects the role assumption and makes planned/reached reporting
explicit; it does not alter the source model or the original failed evidence.

## Exact inputs

`inputs.json` gives the explicit absolute path, byte size and SHA-256 of each
input. It pins the source recovered independently from the published Git parts:

- Candidate: `MAZ543A_Textured_Front_Wheel_Parent_Study.blend`, 100052636 bytes,
  SHA-256 `48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea`
- Official Blender 4.5.13 LTS, build `daeeeca98fb0`, executable SHA-256
  `e3ce4e960a2fd3beb1f9d2299e38b3804475ccd395193013aec239a4b75bfbfe`
- Original recovered `fixed-01/inputs.json`, `saved-state-expected.json`,
  `native-report.json`, source builder and helper, with exact original hashes
- Actual old review GLB, 24743400 bytes, SHA-256
  `fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e`
- Actual external suspension GLB, 8154920 bytes, SHA-256
  `02820335705e230b5a70a4debbc9649e4a2cf66eb180117c8d65a17f19e2ba18`
- Current exporter, `nativeWheelBindings.ts` and `vehicleViewport.ts`, pinned at
  clean preparation HEAD `79160c48326f42816c81172c597718d157b92e06`

The static role controls additionally use the independently recovered run-01
8522-object inventory: 10668164 bytes, SHA-256
`3c9d293ee551a1ab6dfa93c6c82ce98634e1997c8ed691f94d534169e434feb3`.
Its explicit local path is in `inputs.json` under `static_role_fixture`; it is
preparation evidence, not a new native execution input. The original12 native
inputs and their hashes are unchanged. Revision3 is prepared at the published
failure checkpoint `e8bfd43ce053ec3764503cef15bf9621084663ce`.

The original evidence can also be restored with the already published
`../cloud-textured-wheel-fixed-20261002/package-fixed-evidence.py`. The run does
not consult the historical cloud model path or rebuild a candidate.

## Planned command (not run)

From the repository root, after independent review and preparation publication:

```sh
PYTHONDONTWRITEBYTECODE=1 python testcar/work/cloud-wheel-export-graph-20261002/run_graph_inspection.py \
  --inputs testcar/work/cloud-wheel-export-graph-20261002/inputs.json \
  --preparation testcar/work/cloud-wheel-export-graph-20261002/PREPARATION-MANIFEST.json \
  --output testcar/work/cloud-wheel-export-graph-20261002/run-02 \
  --window-note 'One bounded graph inspection; record actual competing jobs at launch; not an isolated performance measurement'
```

`run-02` must not exist. Existing run-01 must remain untouched. Both scripts use explicit CLI paths; the input JSON is
the complete path/hash contract. The runner checks preparation hashes and all
input bytes, owns one new child process group, sets affinity to exactly two
available CPUs and two Blender/BLAS threads, disables autoexec, and supplies
`--python-exit-code 1`. The native budget is 60 seconds, followed only if needed
by SIGTERM/1 second and SIGKILL/2 seconds for that owned group. It records the
actual final child return code separately from timeout and cleanup state.
Every poll/wait terminal observation immediately receives a monotonic time.
Success requires the first terminal observation to occur within the native
deadline; exit0 first observed after 60 seconds remains exit0 but fails the
deadline. Later cleanup observations cannot replace that first observation.
The native-phase boundary and cleanup elapsed time are recorded separately.
Unconfirmed termination or any missing final native report is INCOMPLETE.
There is no retry. The output path is constrained to a fresh direct subfolder
of this dedicated package. Operational elapsed time includes loading and
inspection and is not an isolated performance result.

## Evidence produced by the future run

- `launch.json`, `child-started.json`, `heartbeat.jsonl`, `run.log`, `process.json`:
  actual command/PID, timeout/cleanup/terminal state, and before/after hashes of
  source, executable, GLBs, recovered evidence, app context, scripts and inputs
- `native/object-inventory.json`: all 8522 saved objects with native parent,
  object/data identity, collection membership, action binding, rotation mode,
  raw visibility and modifier inventory; session pointers are explicitly local
- `native/collection-visibility.json`: raw Collection and all Scene/LayerCollection
  paths/flags, including master scene Collections
- `native/native-graph.json`: actual old predicate result and losses, exact
  minimum ancestry closure, complete native S543 subtree, its union with the
  old850, any additional required ancestry, data-sharing references, and local,
  world, basis and parent-inverse matrices for that entire relevant union
- `native/stations.json`: all eight saved carrier/spin/brake/drum/upright
  identities and matrices; front-four kingpin/native joint identities and legacy-chain
  compatibility. Rear drum names are checked against the actual old GLB mesh
  and brake parent; this does not reread or requalify their geometry
- `native/external-conflicts.json`, `native/glb-graphs.json`: complete GLB node
  JSON structure, minimal/full overlaps and paired native/external records;
  names are not silently merged, removed or reparented
- `native/visibility-summary.json`: exact visible and nonvisible names by scope
  in the saved active view layer. Per-object records include all active-scene
  view layers and raw ancestor flags, with Collection/LayerCollection paths
  available through the inventory
- `native/protection-before.json`, `native/protection-after.json`,
  `native/native-report.json`: original saved inventory and exact all-world,
  parent and original action-data digests before/after, plus same-run comparison
  of the fields enumerated by `snapshot()`. A second `graph_records()` read over
  the same relevant set compares its local/world/basis/parent-inverse matrices,
  graph links, raw ancestor fields, and per-object hide/select/visible fields in
  every active-scene view layer. Both relevant-record digests and the exact
  equality result are retained in the native report

The report initializes only `planned_protection_scope`. `completed_checks`
starts empty and adds each hash check, saved-state check, role validation,
first/second read and exact comparison only after that step succeeds. A failed
run therefore cannot imply that later protection reads or comparisons happened.

Only the original read-only `allowed` predicate and exclusion constant are
extracted from the exporter. Only four read-only helper definitions and the
original exact `action_record` definition are extracted from the source
scripts. No builder/helper main routine, modifier operation or exporter runs.

## Checked during preparation

`preparation-checks.json` records syntax/AST checks and the actual GLB JSON
parser checks, plus two focused pure-memory deadline controls using the actual
runner observation/success logic. The original loop's witness was entry at
59.9 seconds followed by the first exit0 observation at 60.1 seconds; it
incorrectly left `timed_out=false`. The corrected late-observation control
retains exit0 and rejects success; the within-deadline control passes and keeps
its first terminal time despite a later cleanup observation. These controls
launch no child process. A single explicit48-name role table requires
carrier/spin/brake/drum/upright at stations0–7 and kingpin/joint_frame only at0–3.
The same table drives native membership checks and record extraction; no
existence-based role filtering is used. Static controls against the saved
inventory pass the complete table and reject each of40 missing common roles,
each of4 missing front kingpins and all48 role assignments to another station.
The old review has 850 unique node names exactly equal to
`inputs.previous_export_names`; all 160 moved-scope names are present. The
external suspension has 549 unique names. All eight legacy carrier/spin/brake/
drum names and old parent edges resolve. Binary GLB payloads were hashed for
identity but not decoded or converted. No native execution of revision3 has occurred.

## Interpretation and remaining decisions

The expected nine new ancestry EMPTYs are `S543_SUSPENSION` plus four uprights
and four native steering joint frames. The 859-name minimum closure is not
the full suspension display. The run inventories the entire native S543
subtree separately and includes every one of those objects, even if hidden.
Native Blender row-major matrices and glTF Y-up transforms remain explicitly
separate coordinate systems; overlap alone establishes no pose/data equality.

The current viewport rejects the changed front-four parent chain, then on a
legacy-compatible path clears the suspension holder, adds the old external
module, copies same-name local transforms and visibility, and updates wheel,
suspension and torsion poses. A complete static candidate should therefore be
reviewed as a dedicated route retaining the full native S543 graph, without
loading the old549 suspension alongside it or applying legacy pose/visibility
updates. This is a future design decision, not an enabled or accepted route.

There is no `frame_set`, property/selection/pose/visibility change, explicit
dependency-graph update, evaluated mesh access or geometry payload reread.
The script requires the artifact to open already at saved frame0 and fail-stops
if its saved digest differs. Nine original NODES retain their blocked global
timeline status; no NODES/SUBSURF whitelist is granted. Collection/object flags
and `visible_get` without a viewport are source inventory, not camera framing,
local-view state, occlusion, shading, render or browser acceptance. Exact export
membership/visibility policy, native-to-GLB parity and the dedicated static
runtime route remain unresolved until the actual graph evidence is reviewed.

Protection claims cover only the explicitly enumerated snapshot and relevant
graph fields. They do not claim equality of all Blender RNA, caches, geometry,
or dependency-graph state. No geometry payload is reread and no hidden-object
setting is changed.

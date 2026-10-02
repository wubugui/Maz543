# Ten-target fresh normal capture preparation

Prepared only. No Blender invocation, source evaluation, GLB export, source save,
render, browser work, commit, push, or Slack delivery was performed for this item.
The parent publishes and independently verifies this preparation before the one
native run. Preparation cannot establish any new normal measurement.

## Fixed scope and evidence

`capture.json` pins the saved 100052636-byte source, official Blender 4.5.13
`daeeeca98fb0`, existing 134267928-byte GLB, run-03 reference, diagnosis and exact
helper/addon sources. The ten object-to-reference mappings come from the published
diagnosis. Only two mirrors and eight halfshaft bellows are evaluated, with the
exact modifier list `BEVEL`, `WEIGHTED_NORMAL`; no default allowance for other
modifier types. Frame/subframe must already be 0/0 after opening. Nothing advances
the frame or calls save, export, render or mesh.validate.

The official nodes.py apply-modifier read path is followed: evaluated_get and
to_mesh(preserve_all_data_layers=True, depsgraph=...), then per-object finally
to_mesh_clear. Materials come from that temporary mesh, with only the official
single-None-slot fallback. No exporter entry point or its mesh validation/property
writes runs. Selected pure definitions from pinned helpers are AST-extracted;
their top-level imports, assignments and action entry points do not execute.

Each target receives a normal compact engineering JSON file containing numeric
arrays for raw native float32 normals, native coordinates, loop-to-vertex,
triangle-to-loop, triangle material slots, all UV fields and their metadata.
Arrays include dtype, shape, byte count and SHA256 of little-endian buffers; JSON
readback immediately reconstructs and verifies every buffer including -0.0. This
is approximately 3.65 MB of binary-equivalent correspondence data, with normal
numeric JSON expansion. No encoded binary is inserted into text.

Finite before/after guards cover ten authored source meshes, their materials, and
the target objects and ancestor chains. All pinned input and preparation files
are hashed before and after. This is not a new whole-project audit. Raw records
already written remain available if later correspondence or guards fail.

## Comparison order and limits

The collector replays the saved arrays in the same Blender process and NumPy
runtime. It first reproduces the entire old per-mesh record, including material
buckets, all/POSITION/NORMAL/TEXCOORD hashes, counts, bounds, native mesh name, UV
metadata, omitted counts, old scalar errors, both zero counts, and full material
records. Nothing uses approximate matching. A mismatch is explicitly
FRESH_NOT_CORRESPONDING_RUN03; the raw measurement is retained, no UV adjustment
occurs, and the +0 experiment remains NOT_RUN_OLD_REFERENCE_MISMATCH.

Only after all ten old records match, a separate copy canonicalizes NORMAL and
TEXCOORD zero values to +0 and compares material-aware oriented signatures with
the actual existing GLB. POSITION bytes and the generic oriented_signature,
including its negative-zero sensitivity, remain unchanged. This changes no
numeric vector value. Coverage remains ten targets, not the remaining 2364.

Raw magnitude, round4 perturbation, conversion vector error and normalized
direction error/angle distributions are saved. Worst corner records include loop,
vertex and triangle identities, raw/rounded/converted vectors, native coordinates,
lengths and whether any triangle actually uses the corner. The conversion metric
is raw versus reproduced official conversion before yup, not directly raw versus
GLB. A fresh match never reconstructs omitted historical raw bytes: rounding and
normalization lose information.

CAPTURE_COMPLETE_GUARDS_PASS and runner READ_ONLY_CAPTURE_COMPLETE mean that this
finite capture finished with its guards. They do not mean correspondence passed;
the adjacent correspondence and signed_zero_comparison fields are authoritative
for those separate questions, including explicit mismatch with process exit 0.
Original FAIL_STATIC_NATIVE_TRANSPORT, 2299 issues, raw-vector FAIL, 2e-4 limit and
all 16 OPEN remain unchanged regardless of this experiment. Browser QA is NOT_RUN.

## One execution, only after preparation publication

From the repository root, the parent may run:

```sh
python3 testcar/work/cloud-ten-normal-capture-20261002/run_capture.py \
  --output testcar/work/cloud-ten-normal-capture-20261002/run-01 \
  --window-note 'Replace with the actual concurrent-work context'
```

The runner confines this one owned process session to CPU2, emits a heartbeat
every 10 seconds including its current stage and target, and uses a 300-second
operation ceiling. Prior source load/evaluation histories of roughly 20–100
seconds justify room for the readback, ten-target decode and actual contention.
Timeout/interruption uses TERM/5s then KILL/5s for that session only. It does not
scan /proc child trees or touch other jobs; repeated signals are ignored during
final cleanup, and the terminal record reports the actual exit state. An attempt
directory must be new and a direct child of this preparation folder.

Later numerical replay, without Blender evaluation, must use the pinned bundled
Python interpreter, not host Python. Runtime mismatch stops before comparisons:

```sh
/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/4.5/python/bin/python3.11 -B \
  testcar/work/cloud-ten-normal-capture-20261002/replay_capture.py \
  --capture-dir testcar/work/cloud-ten-normal-capture-20261002/run-01 \
  --output testcar/work/cloud-ten-normal-capture-20261002/run-01/replay-independent.json
```

`preparation-checks.json` records only the bounded static and pure numerical
checks actually performed, source/input hashes, and explicit unexecuted stages.

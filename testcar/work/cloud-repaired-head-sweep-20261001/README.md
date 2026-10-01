# Repaired heads versus measured-axis door sweep

The exact published native140-head attachment replay was compared with the
original closed snapshots for44 door parts ×140 actually changed head components,
including every opposite-side combination:6160 pairs before and6160 after.
The motion is the published measured-barrel-axis formula over signed0–99°, not
the stored old pivot and not the web/Draco asset.

Both snapshots have6160 conditional frozen-box separations, all using one complete
closed-angle interval. There are0 unresolved and0 newly unresolved pairs. The
smallest proved padded axis gap is0.013511261445376288m in both snapshots; it is
not an exact shortest surface distance. Each moving and fixed box is expanded
by20µm. This remains an adopted numerical guard, not a proved bound on Blender's
whole-angle floating-point implementation.

The3080 same-side chosen gap bounds remain equal. The3080 opposite-side bounds
become about12mm smaller because the heads move inward, while remaining strictly
separated. **Do not describe every clearance as improved.** Chosen separating
axes are1808X,1272Z and3080Y in each snapshot.

## Scope and actual execution

- The repair script is imported unchanged at SHA ec323735…; its replay report is
  byte-identical to the published attachment report
-44 closed evaluated door meshes/triangles and four hinge basis/world matrices
  remain exact; both sides'70 repaired components are identified by the original
  component report and the actual replay. The10 other heads remain unchanged
- The measured local axis is rederived from the pinned barrel centers and checked
  against the published trial; signed left/right intervals and the full Cartesian
  pair set are explicitly verified
- The original interval function/20µm/max_depth6/max_cells127 are pinned. A
  deliberately overlapping bound retains all64 unresolved leaves/127 cells;
  missing, duplicated and omitted-opposite-side pair controls reject
- Native Blender4.5.13, one thread,40.685s, peak2113008KiB, exit0; source and
  executed script SHA are unchanged. Not an isolated performance benchmark
- No native door is rotated in this audit. The calculation uses frozen evaluated
  frame0 snapshots and analytic measured-axis rigid motion. It does not add a
  new native dependency, actual-pose or roundoff proof
- No claim for10 untouched heads, six retained closed-contact pairs, other moving
  doors, hidden/outside geometry, web, manufacturer fit or whole-vehicle acceptance

The original six closed contacts remain; all16 gates OPEN. No source save,
rendering, export, new native asset or LFS entity is produced by this item.

## Complete reversible evidence, not dropped rows

The four native per-door files were already minified (~695–698KB each). The
ordinary JSON evidence bundle interns repeated domains, intervals, results and
statuses while retaining every pair, numeric value, separating axis, empty or
nonempty clear/unresolved list and flag. It is not binary model encoding.

`compact-delivery/delivery-manifest.json` records BOTH native and compact
filenames, bytes and SHA256. Four door files become56701/56316/56422/56037B;
main report becomes107021B. All10 native outputs total3411672B and are represented
by717382B of transport files, excluding the manifest. Even the three repeated
native repair reports are included, not silently omitted.

Native filenames and native detail_sha fields refer only to reconstructed original
bytes. Do not rename a compact file to its native filename or replace the original
hashes with compact hashes. Restore before ordinary consumption.

The native evidence was independently restored twice without Blender; the
published parent readback compares all10 reconstructed files byte-for-byte with
the actual original outputs, then rechecks complete6160 coverage, signed intervals,
input hashes, status/axis/gap semantics and expected limits. A synthetic mixed
clear/unresolved CELL_BUDGET codec fixture also round-trips. Readback is not a
second native evaluation.

## Restore and recheck

From `testcar`:

    python scripts/compact-rivet-sweep-evidence.py unpack \
      --bundle work/cloud-repaired-head-sweep-20261001/compact-delivery \
      --out /absolute/new/restored-evidence
    python scripts/verify-rivet-sweep-evidence.py \
      --evidence /absolute/new/restored-evidence \
      --audit-script scripts/audit-repaired-head-sweep.py \
      --out /absolute/new/readback-report.json

Targets must not exist. For a genuinely needed fresh native run:

    python scripts/run-repaired-head-sweep.py \
      --repo /absolute/path/to/Maz543 \
      --blender /absolute/path/to/official/blender \
      --out /absolute/new/outside-repo/native-evidence

The portable launcher is syntax/help checked, not the launcher used for another
native rerun. It pins the original executed audit and source SHA, requires a fresh
outside-repo directory, one owned process and a180s bound. The actual original
command, terminal state, hashes and timing are preserved in reconstructed
process.json. No installation, credentials, network or publication is automated.

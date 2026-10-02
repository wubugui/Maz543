# Eight-station legacy wheel binding guard — 2026-10-02

**SCOPED PASS: existing viewport binding and fail-before-mutation checks only.**
This closes the missing-carrier array-index defect. It does not implement or
activate the unexported native-joint wheel candidate. All16 whole-vehicle gates
remain OPEN. No Blender, Godot, browser, Draco decode or rendering was run.

## Change

`lib/nativeWheelBindings.ts` records all8 exact carrier/spin/brake identities.
The actual viewport invokes it immediately after resolving the native root,
before assigning `renderedRoot`, clearing suspension children, adding subsystem
models or replacing the displayed root. Every station and its legacy parent
chain must resolve uniquely. Missing targets/sources, duplicate required names,
incorrect source side or unsupported parents reject the entire binding group.
The function does not mutate its input objects.

The per-frame wheel loop now reads the station stored in the binding record.
It no longer derives physical station/side from the compacted array index.
For valid existing assets, all remaining pose math is the original code.

The source selector, production asset/default URL, existing preservation gates,
cab precision gates and old exporter were not changed. The new native-joint
parent chain is deliberately rejected by this **legacy** binder. It still
needs its own actual exported asset, retained suspension assembly and validated
pose-binding path; accepting its names alone would be incorrect.

## Actual inputs and checks

| Actual GLB | SHA-256 | Nodes | Tested modes |
|---|---|---:|---|
| `public/models/maz543a-blender.glb` | `4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698` | 371 | production |
| `public/models/review/maz543a-cab-va180-v1.glb` | `fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e` | 850 | cab-va180-v1, cab-va180-axis-v1 |

The verifier reads exact GLB node identities, parents and TRS/matrix values into
Three Object3D graphs. These are transform/data checks, not substitute vehicle
geometry or a claimed GLTFLoader/browser run. It uses actual `createMAZ543`,
`model.update`, the current shared viewport pose-copy statement and review-pose
function, and the current wheel loop. The regression reference is the exact
historical wheel loop from commit `3a7bd1322b6b72f3d8168ab16c935cdc55b5035f`,
whose viewport SHA is locked in the verifier.

- 97 frames per mode vary steering, explosion and eight distinct suspension
  travel inputs. All200887 node world matrices match the old loop coefficient
  for coefficient; maximum error0. This is sampled code behavior equivalence,
  not native mechanical qualification or continuous motion/collision proof
- Reversing source-wheel order still finds the correct named station. Reversing
  binding order before each frame also produces maximum matrix difference0
- 171 rejection cases cover all missing carrier/spin/brake stations, all26
  duplicated required target names, missing/duplicate source and wrong-side
  sources at stations0/3, and a clearly synthetic four-front-joint parent tree
- On each rejection, the actual preflight block leaves `renderedRoot` pointing
  to `model.root`, returns no bindings, and leaves the input graph's parent,
  children, local TRS and visibility snapshots unchanged. Source-order checks
  establish that later scene replacement and subtree clearing were not reached
- The original compacting loop is a failing negative control: deleting station0
  puts surviving station1 at the wrong position by2.375000000063m; deleting
  station3 puts station4 at the wrong position by4.065787131700m
- Both asset byte hashes are checked before and after. Source/entry/exporter
  hashes are recorded in `binding-report.json`

## Failure presentation and limits

The following paths were inspected in source, not exercised in a browser.
In the ordinary main-thread viewer, no `onFatal` is supplied. Existing `onError`
shows the load error; the generated provisional `model.root` remains displayed
and animated, `nativeLoaded` stays false, and no native `onReady` is emitted.
This is not a fallback to a validated production native asset. The existing
API remains present in this main-thread path.

In render-worker mode, `onFatal` sends a fatal message. The worker client stops
its render/mechanics workers, clears its owned API/canvas and forwards `onError`.
It does not retry the main-thread renderer for an asynchronous fatal. The
synchronous worker-start fallback is a different existing path. No change to
these error/fallback policies is included in this item.

`prior-review-records.json` records source paths/hashes and the narrowly reviewed
historical preservation contracts for tyre-v2, hood-tyre and left-driver. Those
three GLBs are not materialized here and were not newly tested. Their reports
do not replace actual fresh asset checks. Axis review uses the same actual
fde04 bytes and was included in the fresh three-mode test above.

No actual wheel candidate exists from this item. Candidate export selection,
full Textured identities, suspension merge, new-parent pose preservation,
native timeline, kingpin/CV relationships, nominal1° camber, brake construction,
contacts, full vehicle rendering and all16 acceptance gates remain unresolved.

## Reproduction and bounded check outcomes

From `testcar`, run `node scripts/verify-native-wheel-bindings.mjs` to regenerate
the report. This run used Node v24.19.0. The checker needs native TypeScript
stripping and module.registerHooks (added in v22.15.0 / v23.5.0), as documented
in https://nodejs.org/api/module.html#moduleregisterhooksoptions . It also needs
the two real SHA-locked GLBs; no browser
or native 3D application is started. `run-check.py` preserves per-command
stdout/stderr, launch record, CPU affinity, timeout and actual process outcome.
Its output directories are single-use to avoid overwriting a recorded run.

All following checks used CPUs0/1 with a120-second bound and completed exit0:

| Check | Actual elapsed seconds | Evidence |
|---|---:|---|
| final3-mode binding test | 4.184323 | `binding/process.json` |
| TypeScript noEmit | 2.723069 | `types/process.json` |
| focused oxlint, new module/test | 0.917113 | `lint/process.json` |
| vinext production build | 20.338185 | `build/process.json` |

The short final binding run overlapped the end of build; elapsed values are
execution records, not isolated performance measurements. Build logs retain
npm proxy/config notices, plugin timing warnings and the existing large-chunk
warning. No deployment was performed. `git -c core.whitespace=cr-at-eol diff
--check` passed; the viewport's existing CRLF bytes were preserved.

`binding-first-two-modes/` retains the earlier successful2-mode bounded check,
its then-executed script and report. It is superseded by the final3-mode report,
not a failed candidate and not extra asset coverage. Publication preserves these execution records with the corresponding code changes.

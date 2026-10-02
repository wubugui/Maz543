# Saved front-wheel candidate: export and static review boundary

The saved editable source is100052636bytes, SHA-25648dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea. Its complete plugin publication, clean remote restoration and native fresh-open are verified in bf88d253; all identified native/view assets were subsequently closed out in f2b800c. This document records the next integration decision from the code and original data at79160c. No new GLB or application route is claimed here. The first graph inspection and its failed role assumption are recorded below.

## Existing data and concrete failure paths

The actual retained cab GLB fde04e48 has850 unique node names. All160 objects in the front-wheel operation scope occur in that file. The saved native candidate changes12 parent edges and adds four EMPTY steering frames. Keeping the old850 objects with their new parents requires nine additional transform ancestors: S543_SUSPENSION, S543_0..3_upright and S543_0..3_native_steering_joint_frame. This is a minimum graph closure, not a complete suspension display.

The old exporter in scripts/export-va180-cab-candidate.py excludes S543_SUSPENSION by ancestry. Applied unchanged to the new source, it omits the reparented front-wheel assemblies. Its native references cover the earlier cab work, not the new wheel/ancestor geometry.

The existing external suspension GLB,8154920bytes/SHA25602820335705e230b5a70a4debbc9649e4a2cf66eb180117c8d65a17f19e2ba18, has549 unique node names. Five names overlap the minimum closure: the S543 root and four front uprights. Keeping two copies creates ambiguous first-name lookups and last-write maps. Removing the candidate branch deletes its front wheels. Grafting the new joint to the old external upright changes its actual parent and introduces additional transform/geometry correspondence requirements. Equal initial translation alone does not establish that correspondence.

The current lib/nativeWheelBindings.ts correctly rejects a nonlegacy parent chain before assembly mutation. Its eight-station identity and missing-station safeguards must remain intact. A candidate needs a separate explicit qualification path; it must not silently fall back to the old binding.

lib/vehicleViewport.ts currently clears the suspension holder before attaching the external module. It also creates generic same-name source bindings and copies local position/quaternion/scale/visible every frame. That copy would overwrite the new parent compensation even at zero rotation: a drum formerly had zero local translation under its brake parent and now needs an approximately0.29m offset under its spin parent. Protecting only carrier/brake transforms is insufficient; the entire160-object changed scope and its ancestors matter.

Stopping the wheel loop alone is also insufficient. The runtime separately writes suspension/upright poses, torsion vertex arrays and whole-vehicle heave/pitch/roll. Its focus visibility follows the old group ancestry: wheels/brakes focus hides the suspension ancestor containing the front wheels, while suspension focus leaves the rear stations under hidden wheels/brakes groups. Per-mesh visibility cannot override an invisible ancestor.

## Chosen initial boundary

Prepare a distinct, explicitly selected static/frame0 candidate path, preserving the source's complete native S543 subtree and omitting the old external suspension replacement in that path. Keep production and all existing candidate/legacy behavior unchanged. The first route should show the complete static assembly; station-specific focus, motion and exploded views need their own explicit membership and transform qualification.

Before implementing that route, read the actual saved source at its existing frame0. Record the old exclusion result, minimum ancestry closure and full S543 union separately. Inspect original parent/type/data bindings, relevant local/world matrices, actual viewport visibility and the object/ancestor/Collection/LayerCollection states. Inventory unknown or hidden content explicitly. Do not change selection, hide flags, frame, pose, properties or source geometry to make an export selection pass.

A full S543 inventory is necessary because the minimum nine ancestors do not prove complete native suspension geometry. The proposed read-only inspection will establish the exact source scope, rather than assuming the old549-node module and native subtree are interchangeable.

## Export and runtime evidence still required

- Actual candidate export must retain all eight station identities, the front four new chains, the rear four legacy chains, all12 changed parent edges and every required ancestor. Duplicate/shared names and unsupported mixed chains must fail before scene replacement
- Preserve original parent compensation and source geometry through export. Obtain actual native position/topology/UV/normal/material/image references for the front assemblies and relevant suspension scope
- Verify actual Draco-decoded data. The existing fde04e48 door stream remains a known14bit precision failure; a new export must not silently preserve that failing stream or reuse unrelated cab-only reference results as proof
- Isolate every runtime transform/deformation write in the static candidate path, including generic bindings, wheel/upright updates, torsion arrays and the vehicle root. Keep original frame0 geometry and effective visibility after the first and subsequent frames
- Qualify focus/section/picking and all eight station membership rules separately. Unsupported motion controls must not imply validated native operation
- Register a new review kind only after a real GLB exists, its actual GLB hash is known, and complete plugin publication/readback succeeds. A blend hash is not a GLB hash. Preserve development-only, duplicate-query and worker restrictions
- Use real GLTFLoader and browser evidence for the imported candidate. Do not substitute a procedural or legacy model when candidate loading/qualification fails

The native source currently has finite fixed-frame spin evidence only. Nine original NODES still block global timeline qualification; no generic NODES/SUBSURF whitelist is introduced. Steering, CV, suspension installation, continuous mechanics, renderer/material equivalence and all16 vehicle gates remain OPEN. The old rejected GUI launch is not retried by this preparation.

## Reviewed read-only preparation

The dedicated work/cloud-wheel-export-graph-20261002 package is frozen at preparation manifest SHA-2561cbddd23e8c0ac76e4eb1b3d77f195ffedf84e0fcab08ded54c355ff424c9a3d (8files/65553bytes). Independent review confirmed the12 actual input hashes,850/549 GLB graphs, all8 legacy station identities and the absence of model-mutating operations beyond loading the pinned candidate. A first-observed-late exit0 boundary in the draft runner was corrected before any native run. Two pure-memory controls distinguish59.95-second timely completion from60.1-second late observation while preserving the real exit code. A second relevant-record read covers local/world/basis/parent-inverse and all inventoried active-scene view-layer states. Protection claims are limited to those enumerated fields. No concrete preparation blocker remains; actual native graph/visibility results are still pending.

## First inspection outcome and corrected role preparation

The first native run exited1 after15.773098 seconds, within the60second window, with all protected files unchanged. The raw8522-object inventory and all nine original text records were completely published in e8bfd43ce053ec3764503cef15bf9621084663ce and independently recovered from39 remote paths/8392545bytes. The inspector incorrectly manufactured steering-kingpin names for the rear four stations. Only the front four have that role; no model part was removed or created.

Revision3 uses one explicit48-name table: five shared roles at every station, plus front-four kingpin and joint-frame roles. The identity/name-presence checks and native records consume that same table. It retains all eight old GLB chain checks and original front-four evidence matching;92 focused negative cases reject missing common roles, missing front kingpins and cross-station identities. Existing inventory resolves all2675 subsequent relevant names. The complete original S543 subtree contains1985 objects, and its union with the old850 is2675 with no missing ancestors. These offline facts do not replace the pending native second snapshot, relevant matrix/visibility comparison or geometry qualification.

The corrected report separately identifies planned protection and actually completed checks. The60second deadline and real exit-code recording remain unchanged. Manifest0c15194b8048455ad0329b664cbc45143c2f537d28893bcdce8ed04dea029705 fixes the9 preparation files/81384bytes. Narrow independent review reran the role/deadline controls and verified the manifest, five Python compilations and twelve pinned native inputs without finding a concrete blocker. Complete plugin publication/readback is still required before its native run.

Local official Blender4.5.13 glTF exporter source also establishes an export requirement: blender/exp/export.py:28–29 and47–48 call frame_set when gltf_current_frame is false, even when animations are disabled. A future static candidate export must explicitly set export_current_frame=True and export_animations=False. This observation does not execute or qualify that export.

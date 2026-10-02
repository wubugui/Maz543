# Six-object appearance component readout

Two complete six-object readouts across two separate official Blender processes locate the newly reproduced combined-signature differences in the evaluated SurfaceUV float32 byte digests of four representative objects. The two stable controls have identical recorded components. This is a small read-only diagnostic, not a new vehicle or native-repair acceptance.

## Actual executions

- appearance-components-01: CPU1, hard30seconds. Wrapper124 after30.054seconds; native exit unknown. The first fresh-open case was completely recorded. The requested second fresh-open case and combined report were not completed. All original partial records are retained; its unfinished second open is not used.
- appearance-components-02: CPU1, hard30seconds; one fresh open only. Exit0 after16.513028925997787seconds, peak1917160KiB. Complete report and case recorded. Official4.5.13/builddaeeeca98fb0, disabled autoexec, explicit python-exit-code1. The actual frozen scripts, runner copies, launch argv, process outcomes, and logs are included.
- Both use exactly the same six objects, component reader and initialization order: open_mainfile, scene.frame_set(0), view_layer.update, evaluated_depsgraph_get in VIEWPORT mode. Both saved/evaluated frame0/subframe0, spin QUATERNION. The new process performs only one open to fit the existing30second bound.
- Neither assigns object transforms, applies modifiers, renders, or saves a blend/GLB. The66,069,335byte original Master SHA remains8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70.

## Component result

Four variable representatives: BL_Hub_0_cover, BL_Wheel_0_nut_0.26_1, BL_Wheel_0_washer_0.343_12, BL_Tyre_0_curved_tread_blocks. Each differs in exactly three reported fields: the evaluated SurfaceUV float32 byte digest, its repeated value inside the old combined-signature components, and the resulting combined digest. These are one observed component change and its repeated/derived digests, not three independent faults.

For these four objects, raw source-mesh appearance components, evaluated material lists, object slot bindings, polygon material indices, local vertex float/loop vertex/triangle ordering digests, UV shapes/byte counts, active flags, min/max values, nonfinite counts, and negative-zero counts match. All measured nonfinite and negative-zero counts are0. Identical extrema do not establish identical UV values or bound their differences.

Stable controls BL_Tyre_0_VI203_profile and BL_Rim_0_bead_lock have no differing recorded fields. Full per-component results are in cross-process-comparison.json; the two unmodified native case JSON files support independent comparison. first-open-prior-hash-check.json compares the earlier complete first sample with the two older combined-only datasets; those old records cannot localize their own changing component.

## Limits and unresolved work

- This establishes evaluated UV-byte variability for four selected representatives across these two independent processes. It does not establish a root cause, identify a modifier responsible, or prove all301 historically differing objects have the same cause.
- Complete raw/evaluated UV arrays were not written. No per-loop error distribution, maximumUV delta, ULP difference, render effect, or tolerance conclusion is available. The source UV bytes are stable in these samples, but evaluated UV bytes are not.
- The six-object fixed read order differs from the original776-object native-candidate traversal. Historical reports contain combined hashes only, so their exact component change cannot be proven retrospectively.
- Only material names/list/bindings and face material indices were read; this is not full shader state or rendered appearance verification.
- The existing complete native candidate remains a bounded parent/drum/72lettering Apply pass with within-run appearance preservation; no cross-process byte-identity claim is made. Nominal1degree camber, physical CV/bearing interfaces, export ancestry compatibility, and all16vehicle gates remain OPEN. No promotion or model asset is included.

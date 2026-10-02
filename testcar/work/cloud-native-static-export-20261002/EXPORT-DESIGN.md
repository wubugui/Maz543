# One saved-frame full-native static export

Revision3 preparation, based on published/read-back
`63a431d2b31c5496d1d1c53cceac8050fcf9ab21`. The earlier run-01 exited1 after
27.833s at the broad shape-key guard, produced no GLB and preserved all inputs.
Its complete seven original records were published and remain unchanged. This
revision has not been executed; no new GLB/source save/render/application change
has occurred. Independent review and complete plugin publication/readback
of this preparation are prerequisites to the separately coordinated native run.

## Deliverable and exact scope

One real `native-static.glb` from the remote-restored editable source
`48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea`
(100,052,636 bytes), using official Blender4.5.13 executable
`e3ce4e960a2fd3beb1f9d2299e38b3804475ccd395193013aec239a4b75bfbfe`.
`inputs.json` pins140 inputs: source/binary, retained source/protection helpers,
original graph dependencies, independent remote graph records and119 installed
exporter Python files, plus three retained torsion construction/neutral/verifier scripts. The preparation manifest pins every new preparation file.
No old GLB geometry is copied into the new asset.

The selection is exactly the ancestry-closed union of old850 names and the full
native S5431985-object subtree:2675 names,2386MESH/269EMPTY/13CURVE/7FONT. The exact
48-role/eight-station table and every native parent/local/world matrix come from
the recovered graph. Front-four joint→carrier/brake and spin→drum edges and
rear-four legacy edges remain native. No external549-node suspension is grafted,
no reparenting, hiding, object deletion or generic modifier whitelist occurs.

The official exporter directly supports CURVE/FONT. No preconversion,
triangulation modifier, hand-written mesh, geometry repair or saved model is
added. Native triangulation is the exporter's own calc_loop_triangles operation.
The exact source remains at saved frame0/subframe0, with export_current_frame=True
AND export_animations=False. This avoids both frame_set calls in official
blender/exp/export.py; no caller advances the timeline.

## Precision and materials

The first asset uses uncompressed float32 GLB, explicitly disabling Draco and
gltfpack. It does not inherit the old cab's known14-bit position failure, but
actual precision must pass the new native-field comparison. No second comparison
GLB is produced. If this actual asset ever uses compression later, actual decoded
correspondence is a new requirement; no prior two-object Draco result qualifies it.

Export applies native modifiers at this one saved state, preserves hierarchy,
exports normal/UV/material data and extras, and disables animations, skins,
morphs, GPU instances and derived GN instances. Preflight rejects every shape-key object outside the exact16 neutral torsion
exception below, armature modifiers, separate evaluated instances, color attributes,
material-variant resets, nonmesh empty-slot remapping and tiled images instead of
silently omitting their effects. These are execution-time unknowns, not passed
preparation facts. All34 exact options are in inputs.json.

Tangents are explicitly omitted; this avoids claiming that the source's known
problematic tangent streams have been repaired. Runtime tangent/normal-map
appearance still needs real loader/browser evidence. UV seams and every exported
TEXCOORD layer are retained in exact triangle-corner comparison. Materials are
exported by the official shader translator, with source authored node graphs,
material-slot assignment and actual GLB material/texture definitions recorded.
Procedural Object-coordinate/Noise/Bump shaders do not become equivalent glTF
shaders. Images use the official AUTO encoder; embedded bytes and decoded PNG
pixels are inventoried, not claimed equal to Blender's linear float pixels.

## Exact16 neutral torsion exception

Only S543_{0..7}_{lower|upper}_torsion_bar with its same-named `_mesh` is eligible.
The recovered graph identifies unique unshared data and no modifiers; retained
blender-suspension.py:185–196,286–303 creates Basis/Twist_-1/Twist_1 and neutral
frame0 keys, and finalize-suspension.py:13–18 repeats the neutral save. Historical
construction is not treated as evidence that the current values pass.

One preflight collects and writes all current guard failures before rejection,
including unexpected shapes, colors, visibility, instances, armatures, variants,
nonmesh slot remapping and tiled images. Every exact16 live key schema/value/
relative-key/mute/vertex-group/coordinate hash, key animation/action/driver/NLA,
show-only flag, mesh identity/user and topology count is recorded. Require exactly
these16 shape-key objects, relative Basis plus Twist_-1/Twist_1, all values0,
unmuted keys, no vertex groups, no key drivers/NLA, no modifiers, no sharing,
show_only_shape_key=False and800/1568/3072/768 counts. Existing key actions are
recorded and protected, never removed or advanced.

At the unchanged saved frame0, official evaluated_get(...).to_mesh with all data
layers supplies each eligible bar's actual mixed native geometry. Native position,
edge/loop/polygon/triangle topology, corner normals, all UV data/layer state and
material identities must be byte-exactly equal to the actual raw export input.
The same key/action state is required after evaluation. Every temporary mesh is
cleared; any mismatch fails, without baking, data replacement, new_from_object,
dummy modifiers or shape-key deletion. This is the sole explicit exception to
the broad shape guard and remains static-frame-only.

The hook allows shape keys only by the previously proved original Mesh pointer,
reconfirms the original object binding and entire live key/action record, and
compares the hook's native fields against the retained evaluated proof. All16
hook identities must occur; every other keyed mesh fails. Raw-source/whole-source
protection and actual decoded GLB correspondence remain required. No generic
shape-key permission or dynamic qualification is introduced.

## Economical evidence and actual checks

A temporary in-memory wrapper around official.save only injects the observing
extension, then calls the unchanged original_save. A finally block restores the
original function; no installed official source file is edited.

A supported gather_mesh_hook reads the actual native blender_mesh coordinates,
loop triangles, corner normals, all UV layers and material slots. Expected arrays
never come from generated glTF primitives. The supported gather_node_hook maps
every source node to a captured mesh identity, including shared-mesh cache hits;
null geometry is allowed only when a separate native read proves no polygons.
Hooks store caught exceptions and the caller requires zero errors and complete
coverage because Blender otherwise logs hook exceptions and continues.

Per material bucket, canonical signatures retain oriented triangle-corner
attributes, seams and multiplicity. Only cyclic triangle rotation and storage
ordering are ignored. Expected normals model official float32 round4,
normalization, zero substitution and (x,z,-y) axis conversion; raw-normal changes
are measured separately. UV V conversion uses native float32 negation then +1.
This is transport from the native fields used in this export. It does not claim
independent curve/font tessellation, cross-evaluation MetricUV determinism, raw
normal identity, connectivity-storage identity or shader/render equivalence.
The earlier four-kingpin MetricUV cross-evaluation gate remains failed/open.

After Blender exits, a fresh Python process parses the actual GLB binary and
validates chunk/accessor bounds, all2675 unique reachable names and parents,
material buckets and exact joint corner signatures. There must be no animations,
skins, morphs, quantization, Draco, external URI or unexplained geometry.
Reconstructed native-axis-converted local/world matrices are compared against
actual glTF TRS; matrix component tolerance1e-5 and actual vertex world position
error≤2e-5m are explicit finite limits. Position corner bytes must match exactly;
this matrix tolerance cannot hide vertex quantization. Official nonzero-normal
conversion vector error must be≤2e-4; zero substitutions are disclosed as source
normal defects and never raw-normal equivalence. No scene-fitting or pose changes
are used to pass.

Raw source preservation is separate from disk SHA. Before/after captures protect
all original Mesh datablocks' authored coordinates/topology/attributes/UVs,
material slots and shape keys using the pinned existing helper, plus original
curve/font records, authored materials/node graphs/images, object local/basis/
parent-inverse/world fields and original actions/visibility. This catches the
official Mesh.validate() path repairing original geometry in memory. Selection
and active object are restored. The exporter's documented TEX_IMAGE node `used`
bookkeeping is reported and restored exactly; unrelated differences fail and are
retained. No whole-RNA/cache/render equivalence claim is made.

## Run boundary, resources and delivery

After review/publication and a coordinated CPU window, the replay command is:

    python -B testcar/work/cloud-native-static-export-20261002/run_export.py \
      --inputs testcar/work/cloud-native-static-export-20261002/inputs.json \
      --preparation testcar/work/cloud-native-static-export-20261002/PREPARATION-MANIFEST.json \
      --output testcar/work/cloud-native-static-export-20261002/run-01 \
      --window-note 'Actual Aether-coordinated competing-work context'

New output only; the runner refuses overwrite. CPU2 native wall-clock budget900s,
TERM3s/KILL3s for only its owned process group; actual exit and first-terminal
deadline observation are recorded. Decode runs after Blender exits with a separate
300s deadline. Decode terminal states distinguish timeout, interruption, failure
and missing report from not-run. Require4GiB free disk and stop if output exceeds768MiB;
recheck actual total after native exit before permitting decode. Capacity failure
is recorded separately from wall-clock timeout, and all generated bytes remain. These are
operational guards, not a verified performance or memory forecast. Source preload
was about15s; actual graph run27.874s/1,751,400KiB RSS. Prior render SIGKILL near
1,992,300KiB has unknown cause.900s allows full mesh extraction and export instead
of recycling an unrealistic120s limit. One-second runner heartbeat records RSS,
peak RSS and output bytes; native phase/node milestones identify progress.

Native geometry arrays are processed per mesh and released; persisted references
are compact hashes/graphs. Decoding in a new process avoids retaining the Blender
scene alongside the parsed GLB. Preparation is roughly140–180KiB. Actual GLB size
is unknown until export; reserve roughly50–300MiB planning capacity, potentially
more. At768KiB rawparts that would mean about67–400 binary parts. Compact native,
protection and decoded evidence is expected to be several MiB, not a second full
geometry/GLB copy. Failure evidence can exceed that estimate and must be retained.

Immediately after this one run, stop for complete plugin-only publication of ALL
produced bytes, including partial/failed output. A large asset uses one canonical
ordered rawparts+manifest+restore representation in this repository, exact new
paths only, with existing LFS rules preserved. Independent remote restoration
must match whole SHA/length and actual GLB parsing before the next work item.
No upload mechanism is included here. A later static app route must explicitly
restore the canonical GLB; it cannot claim a missing asset path is runnable.

The old GUI-render rejection is independent and not retried. No vehicle gate is
closed: all16 remain OPEN; the nine original NODES stay unqualified for global
timeline. Renderer/material, dynamic motion, actual loader/browser, full physical
installation and reference-image acceptance remain subsequent work.

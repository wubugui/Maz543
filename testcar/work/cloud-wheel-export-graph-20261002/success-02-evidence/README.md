# Saved-frame native graph inspection: completed

After revision3 was published and read back in106aa448e0b36f0e2b5346dda4495e65507db35b, one official Blender4.5.13 child opened the recovered48dbc498 candidate at its saved frame0. It exited0 after27.874054138seconds, within the unchanged60second native budget; peak observed child RSS was1751400KiB. Twelve source/context inputs and all preparation bytes remained unchanged.

The run matched8522 saved object identities/world matrices/parents and552 original action records. All48 mandatory station roles exist. It read the2675 relevant local/world/basis/parent-inverse matrices, graph bindings and active-scene view-layer fields twice, and all enumerated fields matched exactly. The full original S543 subtree has1985 objects; the union with the original850 exported objects is2675 and already ancestry-closed. All2675 were visible_get=True in the active view layer and have hide_render=False; this does not establish camera visibility, occlusion, material fidelity or render quality.

The old selection predicate selected690 objects and lost exactly the160 reparented front-wheel-scope objects. The full union shares241 names with the old external suspension module, compared with five names for the minimum859-node closure. Actual front0–3 station chains differ from the legacy path; rear4–7 retain the legacy path. The full union has2386 MESH,269 EMPTY,13 CURVE and7 FONT objects. Nothing was hidden, removed, reparented, saved, exported or rendered in this inspection.

All15 original records total22210654bytes. Nine small records are direct exact copies under raw/; six large JSON records are represented by ordinary JSON values and backwards references in records-table/. No model, mesh binary, image, compression or binary encoding is included. Restore every original byte into a new directory:

    python -B restore-records.py --out /tmp/maz-graph-pass-restored-NEW

The unchanged codec reconstructs JSON values; the restoration script uses each original UTF-8 serialization and verifies all15 original lengths and SHA256 hashes before creating output. The local check ran in a separate process and compared every restored byte with the original. Remote publication and restoration are separately verified after commit creation.

No geometry payloads were reread. Nine original NODES still block global timeline qualification. The269 empty frames and all original parts remain; static graph qualification does not certify continuous mechanics, steering/CV, suspension installation, actual exported data, browser behavior or any of the16 whole-vehicle gates, which all remain OPEN. The first failed run and its original code are retained.

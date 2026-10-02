# First saved-frame graph inspection: failed

The official Blender child exited 1 after 15.773098061 seconds, before the 60 second deadline. All protected file bytes remained unchanged. The actual inventory contains 8522 objects. The inspector incorrectly required rear S543_4 through S543_7 steering kingpins; only front stations have those roles. No model correction or export was performed.

The original nine text records total 10,717,613 bytes. Eight are exact copies under raw/. The original 10,668,164 byte object inventory is represented once by ordinary JSON value/reference tables, using the unchanged codec. This is text evidence, with no image, mesh or model binary payload. Restore exact original UTF-8 bytes to a new path:

    python -B restore-inventory.py --out /tmp/maz-graph-inventory-NEW.json

The codec table reconstructs normalized ASCII JSON, and restore-inventory.py serializes it with the original ensure_ascii=False format, checks the pinned original SHA256 and byte count before writing, and refuses an existing destination. All original file hashes are in original-records.json. The executed preparation source remains in commit 0bb73ec8f3d304e2f2cb7c80f0cd785d09fbb3f3.

The report's prefilled protection_scope describes intended coverage. This failed run did not reach second snapshot/graph_records or the final comparison. File protection passed; complete in-memory protection and graph/visibility acceptance did not. All sixteen vehicle gates remain OPEN.

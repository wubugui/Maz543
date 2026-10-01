# Cloud continuation rules

At the start of every task, read `CLOUD_CONTINUATION.md` first. It is the single
maintained progress record: current published checkpoint, exact inputs, completed
checks, failed candidates, recovery state and the next concrete action. Check the
actual working tree, running jobs and remote status before acting. Then consult
`CLOUD_HANDOFF.md` for the immutable migration/production baseline and
`testcar/docs/ACCEPTANCE.md` for the original requirements. All16 whole-vehicle
gates remain OPEN unless their complete evidence is independently established.

For each completed, verifiable work item, update that same progress document in
the same commit and immediately make a normal push; do not accumulate multiple
items until a stage ends. Verify remote SHA/tree and relevant LFS payloads before
marking delivery complete. Explicitly preserve failed candidates and limits. If
write authentication is unavailable, coordinate its authorized restoration and
avoid accumulating substantial unpushed work. Never create credentials yourself.
Stage reports and actual images still go to the existing project Slack channel.
GitHub Git/LFS is the version source; no new separate backup ZIPs or desktop sync.

The current editable vehicle is `testcar/outputs/MAZ543A_Master.blend` with `MAZ543A_Textured.blend`; the current browser asset is `testcar/public/models/maz543a-blender.glb`, rear-box-frame-20260930. Do not promote failed candidates or rebuild everything from old scripts.

The user requires actual reference comparison from multiple views, native structure and installation checks, retained original references and historical candidates. Preserve unrelated uncommitted work. Do not lower acceptance standards or replace game objects in tests to manufacture a pass.

On 2026-09-30 the user explicitly authorized Blender execution on the dot cloud computer, superseding the former Hub-only restriction for this project. Use verified official Blender 4.5.13 to match the current masters, preserve current sources, and validate candidate files before promotion. The existing Hub is not reachable from this environment; do not change network/security settings or duplicate unknown jobs. Modeling must use Blender engineering tools/modifiers and appropriate curves/Spin/Screw/Boolean operations, not manual script mesh construction.

The user authorized continued development in the cloud and Git pushes to wubugui/Maz543. No force pushes, history replacement, deployments, paid services, or new credentials. No further development on the original Windows workstation after this migration.

User-authorized progress reports and real screenshot attachments belong in the already established dedicated private Slack MAZ543 progress channel. Its private destination is intentionally absent from this public repository; obtain it from the delegation/session context. Never publish signed upload URLs or private delivery metadata here.

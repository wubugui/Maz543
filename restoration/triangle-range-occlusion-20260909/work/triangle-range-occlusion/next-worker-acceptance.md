# Next concrete display task

Full goal ACTIVE, all 16 whole-vehicle gates OPEN. Range culling stays DEV only.

Ordinary UI still uses main rendering; components/vehicle-viewer.tsx enables the complete worker only behind development render-worker=1. viewport.worker.ts also gates native RAF behind development native-raf=1. Complete client/host/physics transport already exists; do not introduce a reduced scene or different mechanical model.

Read docs/RENDER_WORKER_20260909.md and docs/WORKER_LIFECYCLE_20260909.md with later lifecycle/context/tangent stages in mind. Outstanding acceptance: production worker, labels, resize, real picking, xray/section, cross-context complete pixels, multi-switch cleanup and measured UI responsiveness. Older whole-export tangent errors were separately investigated; do not redo finished source/tangent work or confuse that with the worker transport.

Current compiled artifact dist/client/_next/static/viewport.worker-CWehxGlQ.js is 900600 bytes, SHA256 49895ff8fc5f23e3b14ad0d29293f99fdf8b0346dfd98a52d0aa425c1e026b1f. Existing server is still localhost:3000. A read-only /@fs fetch returned 3439092 bytes and different SHA, so that response is NOT accepted as byte-exact production code. See next-production-worker-availability.json. No process/port/settings changed.

Possible next safe fixture: copy the built worker to a task-owned public validation asset, verify actual HTTP response byte-for-byte, then use the existing render client with that exact production Worker constructor. Inspect relative/dynamic asset paths first. Keep existing server/port, restore ordinary preview and remove only exact fixture files when finished. Do not call a transformed development response production proof. Complete real app interactions and compare main/worker output before changing defaults. Source-pose and quality comparisons remain required.

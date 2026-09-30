# MAZ543 cloud handoff — 2026-09-30

This is the complete audited engineering-file snapshot for **https://github.com/wubugui/Maz543**, branch **migration/maz543a-20260930**. It replaces the older migration instructions as the entry point. The repository was public and had no remote branches at preflight; the original workstation has one local commit `4b89e61c2c99fe01fa251df1e5de3e3fc54ccfbd` plus extensive later uncommitted work. That original checkout/index/history remains untouched. This sanitized snapshot begins an independent migration history, with a GitHub noreply author identity. No force push, deployment or account/security change is authorized by this migration.

Local modeling/development has stopped. Cloud development may continue under the user's existing instructions. Uploading these files does **not** pass game, accuracy, physics, performance or subjective visual acceptance. All **16 whole-vehicle gates are OPEN**, as recorded in `testcar/docs/ACCEPTANCE.md` and the retained original requirement/history notes.

## Unique current working version

Use the **rear-box-frame-20260930** engineering version. Older candidates in `restoration/`, `work/` and stage reports are retained evidence, not replacements for the production assets. SHA-256:

| Current file | Bytes | SHA-256 |
|---|---:|---|
| `testcar/public/models/maz543a-blender.glb` | 20,544,268 | `4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698` |
| `testcar/outputs/MAZ543A_Master.blend` | 64,847,547 | `0391bfde5b7474a5f1ac4eac955f2fd8dbbb6febd33fb7d772a2cd18575edec3` |
| `testcar/outputs/MAZ543A_Textured.blend` | 98,107,810 | `f927cfffae77e443fe6f7c8536bb2344d6b7694f335a071a26d4bba22e350f5d` |

The source asset URL has `v=rear-box-frame-20260930`. Current module GLBs, editable component masters, all raw reference files, code, material data, original requirements, source registers, screenshots, native audits and previous candidates are included. `migration/cloud-handoff/MANIFEST.json` lists every original included path, size, public SHA-256 and original SHA-256, plus explicit exclusions and public-copy redactions. Original files were not redacted or deleted locally.

## Space and selective retrieval

Audited included original files total **10,000,026,585 bytes (9.31 GiB)**, 3,486 files, before the small handoff additions. `SIZE_AUDIT.json` contains exact Git/LFS object totals. Full working tree plus a complete local LFS cache requires roughly **16.4 GiB**, before Node dependencies/build outputs; it is a poor first choice for a cloud disk with 30GB shared by two projects. LFS deduplicates storage/upload, but repeated historical paths still occupy working-tree space when fully materialized.

All history is retained in the repository. Start with source, current browser assets, current two vehicle masters and raw references; leave historical LFS objects as pointers until needed. Install Git LFS using the cloud environment's approved package setup if unavailable. Normal Git/LFS authentication must use the user's existing authorized GitHub connection; do not create credentials or change spending limits.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --branch migration/maz543a-20260930 https://github.com/wubugui/Maz543.git
cd Maz543
git lfs install --local
git lfs pull --include='testcar/public/**,external/**,testcar/outputs/MAZ543A_Master.blend,testcar/outputs/MAZ543A_Textured.blend' --exclude=''
python3 migration/cloud-handoff/verify-files.py
```

This initial asset selection has about 294MB of materialized files, with an additional LFS cache copy; source/dependencies/builds require separate space. Add current component masters when modeling a module:

```bash
git lfs pull --include='testcar/outputs/*_Master.blend' --exclude=''
# Inspect available paths before fetching historical candidates:
git lfs ls-files
git lfs pull --include='restoration/rear-box-frame-20260930/**' --exclude=''
python3 migration/cloud-handoff/verify-files.py restoration/rear-box-frame-20260930/
```

Most historical volume is `restoration/` (~5.07GB), `testcar/work/` (~2.55GB) and `testcar/outputs/` (~2.24GB). Do not interpret an LFS pointer as a missing original or a valid Blender/GLB file. Full retrieval, only when disk and existing LFS quota permit:

```bash
git lfs pull --include='' --exclude=''
python3 migration/cloud-handoff/verify-files.py --all
```

No paid plan or extra budget was enabled. This snapshot alone has approximately 7GiB of unique asset storage; remaining account-wide quota has not been independently verified. Stop and report actual quota/payment errors rather than buying capacity.

## Dependencies and run/verify commands

The viewer uses React 19.2.6, TypeScript 5.9.3, Three 0.183.2, vinext 1.0.0-beta.5 and Vite 8.0.13. Node **22.13+** is required. `testcar/package-lock.json` is authoritative. Installed Windows dependencies and runtime binaries are excluded; reinstall for the cloud OS. No external model decoder CDN is required: retained `testcar/public/draco/` provides decoder files.

```bash
cd testcar
npm ci --no-audit --no-fund
node node_modules/typescript/bin/tsc --noEmit
npm run build
MAZ_NODE_PREVIEW=1 npm run dev -- --host 0.0.0.0 --port 3000
# Open the preview with ?quality=full for actual full-quality comparison.
```

From the repository root, `node migration/cloud-handoff/verify-current-gltf.mjs` validates the current browser GLB after dependencies are installed. `verify-files.py` needs only Python standard library. Older QA scripts can require Playwright/Chrome, NumPy, Pillow, Shapely or pdfplumber; reinstall compatible versions only for the relevant workflow. Some old scripts still contain `D:/...` or `E:/...` paths, Windows Chrome paths and dependency imports. Their Linux portability has **not** been established; adjust project/reference/dependency path resolution in cloud before use. Do not blindly run historical rebuild scripts against current assets.

Original personal `.openai/hosting.json` was excluded. A non-secret placeholder (null D1/R2 bindings and zero UUID) is supplied solely because the unchanged Vite config imports that file. It creates no deployment target or credentials. Original project code/model contents are otherwise preserved, except the recorded redactions of private Slack delivery metadata and a personal email in public text copies/three evidence ZIP reports. Evidence images in those ZIPs are retained.

## Hub jobs and modeling boundary

Blender execution was mandated through the existing authorized LAN Inference Hub, `http://denghong01:8765`, Blender **4.5.13**, CPU 4 threads / 4GB for these latest jobs. Cloud access to that LAN service is **unverified**; do not assume it works, and do not replace it with local/cloud Blender without user authorization. Do not change ACLs, service accounts/security or terminate unrelated work. HTTP read-only checks and saved job records can establish state before a new approved job.

| Saved task ID | Last verified state | Result |
|---|---|---|
| `48aad07d-787d-4401-a723-f6317dd5a894` | succeeded | Current rear-box/frame masters and GLB stage |
| `0b6e697f-ee60-4415-bad1-49bb203b834e` | succeeded | Read-only native rear-parts/tyre audit |
| `e22f799b-9782-464b-b11a-e0c29b8a18a4` | succeeded | Prior hinge/material native work |
| `68e36a53-73d3-4396-ba32-2ab9aee05c1b` | succeeded | Corrected native door-axis sweep |
| `f7e5773e-efd6-47c8-ad72-850e6bf10ddd` | **failed**, exit 1, no output | Three central plates/hinge candidate; `ValueError: min() arg is an empty sequence` during moving native-panel bounds audit |

No new Hub job was submitted for migration. The last task is terminal and was not retried. Its scripts and `testcar/work/three-cover-20260930/{task-record.json,task-result.json,stdout.txt,stderr.txt}` are retained. Diagnose empty evaluated Boolean geometry/operand installation at rotation in the future; do not substitute objects or weaken the audit. The failed candidate never replaced the current assets.

## Evidence, results and remaining work

Latest real local browser check: **2026-09-30 17:41:31.372 UTC**, HTTP 200, no browser errors, GTX970, 3,297 full-quality meshes. Six before/after view pairs had identical camera/projection matrices. Twelve new rear parts matched native world bounds to max `1.1920928955e-7 m`; their native static intersection audit against 432 rear-tyre/tread objects found zero intersections. Suspension travel remains untested for that installation. Current export reported zero glTF errors/warnings, with 260 unaffected compressed mesh streams and three embedded textures byte-preserved. See `testcar/docs/REAR_BOX_FRAME_STAGE_20260930.md` and `testcar/outputs/rear-box-frame-20260930/`.

Prior hinge/rubber/upper-mirror stage evidence is in `testcar/docs/CAB_HINGE_RUBBER_STAGE_20260930.md` and front-stage outputs. Actual runtime closed/99-degree hinge matrices matched native within `1.525879e-7`; the corrected native front-only 0–99-degree sweep found zero tested intersections. These limited tests do not establish whole vehicle functionality or dimensional accuracy.

Continue the actual reference-driven restoration: central cap with three plates and real front hinge, asymmetric equipment covers and missing right battery/filter/regulator/blower and left filtered ventilation equipment, fuel mounting brackets, rear installation under motion, windshield/mirror/bumper/searchlight dimensions and old-location AO, and remaining steering/brakes/transmission/fluid/mechanical functions. Engine/cooling envelope and rear equipment-cover naming need joint verification; do not just shrink a hood to imitate one camera.

The consulted original manual is https://djvu.online/file/zjMdLY3MFjmTL (technical description, 1977); pages 173, 48, 202–203 and 228 informed the latest uncompleted candidates. Two retained web fetches, `work/reference-docs/MAZ543-1977.txt` and the sinref intro HTML, are challenge/cookie pages, **not** a captured full manual. Original references and variant decisions remain in source registers; an MZKT image and prototype were excluded as MAZ543A shape standards. Original reference copyright/attribution information remains in registers.

Mechanical simulation/calibration, original dimensions and variant-specific installation, light behavior, appearance and practical full-quality GPU performance remain open under the 16 gates. Tests that pass, fail, or have not run must stay separate; the user retains subjective acceptance. Linux/cloud runtime, GPU, Blender Hub connectivity and the full set of historical script paths require validation on the receiving environment.

## Explicit exclusions

Original private session/config folders (`.claude`, `.codex`, `.agents`, `.aws`, personal `.openai`), conversation exports, credentials/key/environment-file patterns, signed Slack upload/receipt manifests, global Hub telemetry, original `.git`, installed Node/Python/Blender runtimes, `node_modules`, bundled Python packages, caches/build outputs, incomplete `.part` files and reproducible negative-test/runtime probe fixtures are omitted. An old dist `.tar.gz` containing personal hosting config and the 106MB installed-file migration manifest are rebuildable and omitted. The live project's local Git/history/unstaged files are preserved on the workstation; they were not reset or replaced. The complete per-path exclusion list is in `MANIFEST.json`.

Original raw references, all 130 native `.blend`/`.blend1` masters and retained historical model candidates, 67 GLBs, source/acceptance documents and genuine screenshots/audits remain in the audited snapshot. Sanitized ZIP reports retain all evidence images. Private Slack destination details are available in the parent session, not this public repository. Migration build results and remote verification are reported separately after the actual checks; do not infer cloud validation from this document.

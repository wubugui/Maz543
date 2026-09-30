# Cloud baseline, 2026-09-30

This is receiving-environment evidence, not whole-vehicle acceptance. All 16 gates remain OPEN. The complete historical migration is still pending according to the received DELIVERY_STATE; this checkout deliberately does not materialize the historical asset tree.

## Received and checked

- Repository snapshot: `571b25bf0b1860e1ccf1abc61eda7e55488e7b13`, independent branch `development/cloud-maz543a-20260930`.
- Core verification: 159 files, 294,419,491 bytes; all sizes/SHA-256 match the handoff manifest. This includes current browser assets, raw exterior references and both current vehicle masters.
- Five additional engine/cardan/cooling/starting/suspension editable masters match their manifest SHA-256 values.
- `rear-box-frame-20260930` remains the production version. Original Master/Textured SHA values remain those in CLOUD_HANDOFF; candidate modeling has not overwritten them.
- Node 24.19.0; `npm ci` installed 577 packages successfully using a writable workspace cache. First attempt with the unwritable default home cache failed and was replaced with this verified installation.
- `tsc --noEmit`: PASS. `npm run build`: PASS. Existing chunk-size and static route-classification warnings remain.
- Current GLB validator: 0 errors, 0 warnings, 565 informational messages. This does not establish visual fidelity, motion or physical accuracy.

## Native environment

Official Blender 4.5.13 Linux archive was verified against Blender's published SHA-256 list before unpacking. Runtime identifies as Blender 4.5.13 LTS, build `daeeeca98fb0`, matching the authoring release.

Both current files opened successfully without rewriting them: Master 9,716 objects / 13 images; Textured 7,936 objects / 16 images. The four unpacked exterior reference image paths still contain the original workstation's relative traversal and need portable relinking in subsequent delivery copies. The source image files themselves passed the manifest checks.

The user explicitly authorized cloud Blender on this date after the old Hub endpoint was unreachable. No network/security settings were changed. Older Hub-only text is historical; AGENTS.md records the superseding authorization.

## Browser verification boundary

The original QA script used Windows-specific module/executable paths. `capture-rear-assembly.mjs` now accepts executor-local Playwright/Chromium inputs and an explicit preview base URL, retaining `quality=full`, object inspection and the same six cameras.

The shell browser process was blocked by the execution environment's Unix-socket restriction. A cloud desktop browser could launch, but the initial server command used `--host`; vinext documents `--hostname`, so the requested IPv4 binding was not applied. A separate CDP preview attempt returned `ERR_BLOCKED_BY_CLIENT` for the localhost URL. No other browser access is being used to route around that denial; supported forwarding is pending clarification. No cloud webpage screenshots or GPU/interaction pass are claimed.

Correct vinext invocation for an approved preview context is `MAZ_NODE_PREVIEW=1 npm run dev -- --hostname 127.0.0.1 --port 3100`. This is a local preview, not a deployment.

## Next work

Repair the failed three-panel native candidate, test actual stored hinge coordinates and rigid evaluated geometry after reload, retain all failed candidates/evidence, and address closed-pose interference before promotion. Continue source-backed asymmetric equipment and fuel installation work. Factory dimensional calibration, continuous motion clearance, original mechanical functions and user visual acceptance remain open.

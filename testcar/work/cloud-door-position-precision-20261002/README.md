# Door POSITION precision guard, not a repaired asset

The published `fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e`
GLB (24,743,400 bytes) remains **FAIL** against the adopted 20µm comparison.
Its pivot correction does not restore quantized geometry. All 16 whole-vehicle
acceptance gates remain OPEN.

## Cause and narrow source change

`export-va180-cab-candidate.py` already requests 18-bit POSITION. However,
`prepare-va180-cab-pack.mjs` approves only two old meshes for replacement;
`preserve-unmodified-body-streams.mjs` therefore restores the 20 old door streams.
Their inherited 14-bit precision survives the newer export.

The patch adds a static door-stream precondition before any packaging mutation
or write. It reads the real selected stream's Draco transform metadata, rather
than trusting exporter settings or pre-encode accessor bounds. Both baseline
and candidate determine scope, so deleting or renaming all known pivots cannot
disable the guard. Retained, changed, and new stream selection is exercised
using actual asset bytes and deliberately invalid candidate attribute bindings.

The policy limits the full local POSITION grid step to 10µm, half the existing
20µm comparison. Required bits are the smallest supported integer satisfying
`range / (2^bits - 1) <= 10e-6`; the supported ceiling is Blender's 30 bits.
This is a grid precondition, **not** an end-to-end world-space or Float32 error
proof. Unknown/lossless paths need separate review. Scaled, matrix-form,
skinned, morphing, malformed, or animated door ancestry is refused in this
explicitly static scope.

No stream, material, UV, topology, attribute binding, production selector,
Blender source, or shipped GLB is changed by the guard. It stops the current
unsafe packaging path. A future genuine native re-export and complete transport,
preservation, upload and readback checks are still required before asset repair
or promotion can be claimed.

## Exact native source and measured result

The native experiment used the actual published Textured input of the exporter:
SHA `6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266`,
99,960,163 bytes, restored from its existing LFS object. The separate Master
`8e962d6…` and door-control candidate `3b230c12…` were not substitutes for the
merged/baked source or its UVs. Published provenance manifests are referenced by
path and full SHA in `summary.json`, not duplicated here.

Official Blender 4.5.13 LTS/build `daeeeca98fb0`, factory-startup,
disable-autoexec, CPU1 and a 120-second process-group deadline were used. The
real installed gatherer/compressor and native decoder are pinned by file SHA;
the repository's independently pinned WASM decoder reads each real stream's
quantization metadata. Only the 20 original door primitives are encoded, entirely
in memory. Geometry and index buffers are never saved or disguised as text.
Temporary image encoding and final buffer/file writing are explicitly blocked.

Successful run: exit 0, 20.735 seconds, Linux RUSAGE_CHILDREN peak 1,762,468 KiB
(not aggregate concurrent memory or an isolated performance benchmark). Source
and frozen script hashes are unchanged. All 20 primitives have 3 real encodes,
60 total, using 14 bits, their required bits, and 18 bits.

| Actual encode | Primitives | Failing finite 20µm checks | Largest chosen-vertex distance | Largest whole-mesh span error | Largest barrel span error |
|---|---:|---:|---:|---:|---:|
| 14 bits | 20 | 12 | 64.416381µm | 32.901764µm | 54.478645µm |
| Policy selected: 12/13/17 bits | 20 | 0 | 8.123744µm | 2.861023µm | 3.933907µm |
| 18 bits | 20 | 0 | 4.129531µm | 2.026558µm | 2.145767µm |

The 12 genuine connected barrels retain the identifying 192 unique positions
and 380 triangles; all 12 reproduce the coarse 14-bit span failure. Barrel
association uses a separate grid-derived envelope, never a relaxed acceptance
threshold. Distances are finite bidirectional distances to chosen real
input/output vertices, recomputed in Float64 after KD lookup; they are not
indexed vertex/corner correspondence or continuous surface/Hausdorff proof.
Attribute names/types and index counts were checked, but UV/normal value
transport and complete topology correspondence were not certified. There is
no full GLB, browser, rendering, collision, motion or factory acceptance claim.

## Final checks and retained failures

- Final guard regression: all 20 shipped door streams inspected; 12 rejected;
  12 scope/routing/eligibility controls pass. Actual packer exits 1 before any
  output-write attempt. A preload also prohibits model writes if the guard fails.
- Final repository-config oxlint: 4 files, 208 rules, zero diagnostics, exit 0.
  The initial external-directory run could not locate installed tsgolint; only
  an external symlink to existing repository dependencies was added. Earlier
  empty-output lint receipts are retained but are not the final coverage proof.
- Native attempt 01: exit 1 in 0.466 seconds before source loading, because the
  script expected the version string `4.5.13` instead of `4.5.13 LTS`. Its exact
  source and logs are retained. Final code checks `(4,5,13)` plus the build hash.
- Guard attempt 01: the isolated packer could not resolve existing `three`;
  its failure and verifier source copied after that run are retained. Later
  runners link the already installed dependencies, with no installation.

After native execution, the final policy module gained only clearer comments
and static eligibility checks for translation arity, skin, weights and targeted
animation. `native/executed-policy.mjs` preserves the exact executed bytes.
`executed-policy-comparison.json` verifies policy values and the three actual
grid/decoder functions have identical source. The final guard regression covers
the new checks. The native run is not attributed to future code.

## Replay and publication

Apply `door-position-precision.patch` from the repository root. It changes one
existing packer and adds the guard, regression and bounded native-probe scripts.
Use the exact paths appropriate to the restored source location:

```
node testcar/scripts/verify-door-position-guard.mjs --repo /path/to/Maz543 --out /new/guard-output
python testcar/scripts/run-native-door-position-probe.py --blender /path/to/official-4.5.13/blender --source /path/to/exact-6e406eca-source --scripts /path/to/Maz543/testcar/scripts --decoder-dir /path/to/Maz543/testcar/public/draco --out /new/native-output
```

No further native run is needed to accept these existing bounded results.
`execution-source-map.json` identifies the exact bytes for both native attempts:
unchanged executed scripts are supplied by the patch; only differing historical
sources are duplicated. `manifest.json` lists every delivered file, byte size
and SHA. This worker made no repository, GitHub or Slack write; parent owns
progress-record integration and publication. No new LFS upload is claimed.

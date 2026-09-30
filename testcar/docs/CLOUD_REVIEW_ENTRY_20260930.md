# Explicit tyre candidate review entry

A development-only selector now feeds the existing complete viewer, rather than introducing a separate simplified scene. In an authorized, working local development preview, append `?asset-review=tyre-v2&quality=full` to select the separately stored portable tyre v2 asset. This does not deploy a site or change ordinary production selection.

- Ordinary entry remains `/models/maz543a-blender.glb?v=rear-box-frame-20260930`, SHA-256 `4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698`.
- Candidate entry selects `/models/review/maz543a-tyre-v2.glb?v=a97860806ba1ff70`, byte-identical to the delivered portable v2, SHA-256 `a97860806ba1ff70b61cd7a01ac173f0f461c380704ab06246cd9352660ac422`.
- The selected candidate has a visible unaccepted-review notice. Exported poses carry an explicit candidate filename and root metadata.
- Unknown/repeated candidate names, production builds, `render-worker=1` and `worker-build=1` select the production asset with an explanatory notice. This prevents the older compiled worker fixture from being presented under a candidate label.
- Paths are an exact whitelist, not arbitrary URL or filesystem inputs. The other six native module URLs are unchanged.

`node scripts/verify-review-asset-selection.mjs` passed 15 pure-selection cases, verified both real GLB file hashes and equality of the public review copy to the portable candidate. It also compared the actual 17,208-character mechanical presentation block and eight mechanical source files against commit `aa04cfd6a30c7ca47f8c5004a9c8adde2b4bbe15`, all unchanged. TypeScript and the full build passed.

These are configuration/file/source checks. The new banner, actual model loading, picking, motion, pose export, GPU output and performance **have not been validated in a browser**, because this environment's preview access remains blocked. No alternate access route or network change was attempted. Do not treat this entry or the successful build as browser acceptance. All 16 whole-vehicle gates remain OPEN.

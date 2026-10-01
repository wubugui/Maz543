# Actual coexistence of legacy platforms and lower native steps

A read-only native4.5.13 check of source8e962d6… confirms all four historical
platform boxes remain as exact oriented triangles in `cab_0062`. The two later
lower-step curves and40 tread bars also exist in that same master. This closes
the earlier source-only uncertainty about actual coexistence; it does not prove
intentional supersession or factory-valid assembly.

## Identity chain

1. `lookup-legacy-step-platforms.py` reads only the pinned original seed LFS
   entity and compiled Git blob5fc94089…, without executing the generator
2. Exact source-derived Float32 box corners,8 unique corners,24 indexed vertices,
   12 outward triangles and closed two-incidence topology identify four components
   in seed `cab_0062`, material batch `dark`, extras fixedDetailCount9
3. Components0/1/6/7 use original vertex ranges0–23,24–47,933–956,957–980 and
   triangle ranges0–11,12–23,1080–1091,1092–1103, all zero-based and inclusive
4. `inspect-native-step-assembly.py` matches each of48 actual source-oriented
   triangles exactly once in current native `cab_0062`; cyclic corner ordering
   is allowed, reversal and a100µm single-corner corruption both reject

The limited48-triangle payload is identity-test evidence from an already
published source, not a new model or an encoded substitute for LFS publication.
No geometry is created from the report.

Front-platform bounds: X[-5.15,-4.12]m; rear X[-3.95,-2.95]m, to shown rounding.
Both lie at native Z[1.2025,1.2575]m and span Y[1.35,1.56] or[-1.56,-1.35]m.
The report retains exact Float32-derived coordinates and native triangle indices.
The semantic label follows the old generator construction; it is not a factory
part/dimension/material certification.

## Actual current assembly snapshot

- Two legacy material batches, two named side skins, two lower-step curves,
  forty tread bars and four closed door shells were inventoried:50 objects,
  no expected named object missing
- Both later `BL_Cab_{side}_step` objects retain their native Curve structure,
  spline control points, bevel settings, parent and actual evaluated bounds
- Original platform-vs-skin surface candidates number110/64 on one side and
  102/60 on the other. No old-platform-vs-door or lower-step/tread overlap was
  reported in this limited50-object scope
- Surface intersections do not classify intended attachment, mere touching or
  volumetric penetration. They are not a blanket collision failure/pass
- Both original batches also contain other source components. In particular,
  `cab_0063` holds eight seat-back links as well as eight platform-support links;
  do not move/delete either batch wholesale

Actual native run16.913s, exit0, peak1917980KiB, one thread; not an isolated
performance benchmark. Source SHA is unchanged. Nothing is moved, reparented,
hidden, separated, deleted or saved. This is a rest-pose installation inventory,
not continuous movement, web or whole-vehicle acceptance. All16 gates OPEN.

## Reproduce

The decoder deliberately writes to an explicit directory outside the repository;
copy its evidence into the stated folder only after successful exit0. It reads
the already materialized standard `.git/lfs/objects/5c/58/<sha>` source object.

    python scripts/lookup-legacy-step-platforms.py --repo /absolute/repo \
      --out /absolute/outside-repo/step-lookup

Then supply the decoder's unchanged result/payload under this evidence folder's
`seed-lookup/` and execute the native script with the pinned source present:

    blender --background --factory-startup --disable-autoexec --threads 1 \
      --python-exit-code 1 --python /absolute/path/testcar/scripts/inspect-native-step-assembly.py

An initial unsupported `--seed` argument was rejected before decoding. Its usage
output is retained. The old shell wrapper's overall0 came from a trailing `tail`,
not successful decoding; no payload from it was accepted. The corrected run
records the decoder subprocess's actual exit0 and completed SHA-checked outputs.

# Cloud development continuation, through 2026-10-01

The original full migration remains commit
`4f28bd4618ca7e272f6049b9f615821b8e0bb8f1` on
`migration/maz543a-20260930`. Subsequent cloud work is on the separate local
branch `development/cloud-maz543a-20260930`. These local development commits
have **not been confirmed pushed**. Keep the original migration history and
all failed candidates. All 16 whole-vehicle acceptance gates remain OPEN.

## Production still unchanged

The unique production version remains `rear-box-frame-20260930`, with the
three SHA-256 values in `CLOUD_HANDOFF.md`. No cloud candidate below is a
replacement for the production masters or production GLB.

## Current reviewable work

- Three-cover r3: `testcar/outputs/cloud-cover-service-r3-20260930/README.md`.
  Two editable portable vehicle candidates. The closed front lip/cover overlap
  was removed, but latch release still interferes and the lower lip intersects
  the grille. Discrete service states, fitted mechanism; overall FAIL.
- Tyre lettering: `testcar/docs/CLOUD_TYRE_LETTERING_20260930.md` and
  `CLOUD_REVIEW_ENTRY_20260930.md`. The portable v2 export reproduces exactly;
  its development-only review selector retains the normal production default.
  This is not actual cloud browser acceptance.
- Reference calibration: `testcar/docs/CLOUD_REFERENCE_CALIBRATION_20260930.md`.
  Original 1977 table establishes 543A length11500±25 mm; current two native
  envelopes are11269.1 mm. Published front/rear unloaded group loads differ
  from the equal-load numerical initialization. No global scale or physical
  constants were changed just to match one number.
- FG16 study: `testcar/outputs/cloud-fg16-study-20260930/README.md`.
  Independent editable hollow-shell/optical/glass structure, actual Cycles
  exterior and section. The shareable blend omits newly obtained manual scan
  pixels. Optical element/base still has617 rigid triangle intersections;
  connectivity, dimensions and installation remain OPEN. The local packed
  research copy and iterations are not on the public-ready whitelist.
- Door angle intervals: `testcar/docs/CLOUD_DOOR_INTERVALS_20260930.md` and
  `testcar/outputs/cloud-door-intervals-20260930/REVIEW.md`. Actual four doors,
  44 moving parts against34 added front parts:1496 sufficient swept-box
  separation results over the complete0–99° interval. Explicit static/rigid
  dependency checks, independent pose comparisons and between-sample collision
  negative control are retained. This excludes original cab/frame/interior,
  other vehicle interactions and real browser operation; it is not whole-car
  continuous clearance acceptance or formal machine-arithmetic certification.
- Equipment and suspension sources: `testcar/docs/CLOUD_EQUIPMENT_REFERENCE_20260930.md`
  and `SUSPENSION_REFERENCE_REGISTER.md`. Original variant/revision distinctions
  and remaining hardpoint/stop/installation unknowns must be preserved.
- Torsion installation datum: `testcar/docs/CLOUD_SUSPENSION_INSTALLATION_20261001.md`.
  Original p320 resolves136–141mm as the lower-arm head-centre vertical difference
  during installation, not wheel travel. Existing unadjusted support bolts are
  separated from the arms in24 actual diagnostic states. Four isolated editable
  reference scenes and the original module archive are saved;680 object-pose
  comparisons preserve all evaluated vertices/topology. This does not repair
  stop support, adjustment or preload.
- Battery structure: `testcar/outputs/cloud-12st70-structure-20261001/README.md`.
  Original1977/1983 sources support wood case, two steel bands and three actual
  four-chamber ebonite tanks. The independent73-part candidate retains12 real
  cavities and source curves; all73parts closed after native seam welding.
  Cell plate packs, terminal hood, overall cover, exact carrying hardware and
  four-unit vehicle installation remain missing. The70/70M figure/text variant
  distinction and incomplete fitted envelope remain explicit.
- Complete current-production front/rear views:
  `testcar/outputs/cloud-whole-production-20261001/render-manifest.json`.
  Fresh actual Cycles renders fit all measured vehicle-envelope corners in the
  image and use the unchanged production Master. They do not depict the cloud
  component candidates as installed.
- Battery enclosure forms: `testcar/outputs/cloud-12st70-enclosure-20261001/README.md`.
  The original73 parts are retained exactly; two native fitted forms add the
  documented pressed-wood overall lid and terminal hood. Generic1983 fig4 does
  not identify a production variant or provide fastener locations. Initial
  lid/hood intersection was retained and corrected in this independent study.
  Current147 new-part pairs have whole-box separation or empty native Boolean
  intersections; this excludes fasteners, retention and actual removal motion.
  The two display offsets are not a factory service mechanism. All16 remain OPEN.
- Photo-observed hood grips: `testcar/outputs/cloud-cover-grips-20261001/README.md`.
  Four actual photographer-sourced MAZ543A-labelled views distinguish the two
  transverse top grips from the separate narrow front-edge fasteners. The
  independent two-vehicle candidate adds only the missing grips. Original8712/
  6932 geometry-object snapshots match; grip topology and four attachment
  diagnostic poses were read back. Oldr3 interference and all16 gates remain
  OPEN. Same-camera before/after plus a whole-candidate native view are saved.
  The source register has URLs/attribution/limits, without newly obtained photo
  pixels. Continue photo-guided broad cover contours; do not invent latch axes.
- Photo-guided continuous hood relief:
  `testcar/outputs/cloud-cover-contour-20261001/README.md`. Two editable vehicle
  candidates use native local-position Geometry Nodes before the original
  Solidify to add broad lands and grip troughs. The45mm fit is not an OEM
  dimension. The28mm shallow-cosine first iteration is retained because its
  actual images expressed the source shape too weakly. Both new files reopen;
  zero amplitude recovers the input panel vertices/indices exactly. Five
  discrete diagnostic states show at most2.173um local vertex-set variation;
  existing lock/lip failures and all16 gates remain OPEN. Current detail/whole
  native images were completed and source-SHA-checked; no repeated rendering
  is needed on continuation. Sources remain the normally obtained A-labelled
  Flickr/Fototruck photographs, without photo pixels in new public assets.

## Verified environment and remaining access limits

Official Blender4.5.13 LTS, build `daeeeca98fb0`, is used with four threads.
After the former shared tools directory became unavailable, the same official
archive was downloaded and verified at a MAZ-specific tools location outside
this repository. Archive SHA-256:
`da4e69b06b75b9e642d106496c50e7e240218b411d2f6e18271c1d1d819cef91`.
Locate the installed binary in the active environment; do not assume the old
`/workspace/shared` path exists or install tools into the source tree.

Node dependencies and actual TypeScript/build checks previously passed in
this cloud workspace. Native Cycles images are genuine model renders, not
webpage screenshots. The cloud browser returned `net::ERR_BLOCKED_BY_CLIENT`
for the local preview, so browser checks remain blocked pending a supported
preview route. Do not change network/security settings or use a different
browser to bypass that denial.

Normal cloud Git write authentication is unavailable. A verified original
`ed97cf3` transfer and a later incremental bundle provide an authorized transfer
route, but no local bundle proves remote delivery. Keep exact snapshot heads
and prerequisites; don't rewrite bundles under an existing filename or claim
later commits are included. The incremental bundle through `613c1cb` requires
both `ed97cf3` and the complete migration `4f28bd4`. Later documentation and
door-review hardening commits need a subsequent transfer. No credentials,
private communication receipts or signed upload links belong in this repository.

## Next concrete work

Obtain or verify variant-specific seat/lock/mount construction before removing
the remaining lamp, hood-lock and equipment installation failures. Targeted
source-backed geometry and mechanical work can continue while browser and Git
handoff limitations remain open. Preserve the distinction between published
dimensions, fitted geometry, conditional checks, failures and untested states.

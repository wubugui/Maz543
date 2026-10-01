# Cloud development continuation, through 2026-10-01

2026-10-01 correction: the `b9fb590` cab-panel fit trials used a defective
vertex-only Separate selection and inadvertently archived all four seat bases.
The saved second trial has 0 remaining seat-base vertices and 5,400 archived
vertices instead of the intended 1,800. Its complete-cabin preservation claim
is withdrawn; its images/contact counts cannot establish an assembly improvement.
Original production and the independent panel study are unaffected. Preserve the
old files/backup; corrected trials require per-seat identity, geometry/UV and
actual render-path checks. See the corrected fit-study README and saved
`separation-inspection.json`.

The original full migration remains commit
`4f28bd4618ca7e272f6049b9f615821b8e0bb8f1` on
`migration/maz543a-20260930`. Subsequent cloud work is on the separate local
branch `development/cloud-maz543a-20260930`. Development commits through `63fe135bf1b1c9237c6158519fb77203a9f9a6be`
have now been published by normal Git/LFS push and independently verified. Keep the original migration history and
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

- Hood/tyre composite: `testcar/outputs/cloud-hood-tyre-composite-20261001/README.md`.
  Integrates the second continuous hood candidate with 144 native wheel glyphs.
  Both saved masters pass scoped glyph geometry checks; 8570 Master and 6926
  Textured unrelated objects preserve evaluated geometry, authored UVs, modifier
  inputs, transforms/parents and material slot names. Strict evaluated-UV
  bitwise preservation remains FAIL (3170/2277 objects); repeated evaluation of
  the unchanged input also shows small UV variation. No threshold exemption,
  production promotion. A real combined whole-vehicle native image and two raw
  GLB exports are retained. v1 hood quantization fails; v2 raises position
  precision and passes limited decoded hood/glyph transport. Neither is
  browser-tested. A separate packed candidate preserves414 unrelated mesh
  nodes, with16 new/changed primitive streams checked. Development-only
  `asset-review=hood-tyre-v1` entry and build checks pass; actual browser remains
  untested. See its STATE.

- Left-driver side candidate: `testcar/outputs/cloud-left-driver-side-20261001/README.md`.
  Original1977 source confirms the inherited steering/pedals were in the right
  cabin. Seven retained controls (788 vertices) and the steering group move by
  the existing fitted cabin spacing to the left. Native separation and fresh
  paired-file preservation checks pass; exact shapes/positions remain fitted.
  Actual viewport binding-statement tests address the legacy per-frame pose
  reset without renumbering pivots. Source rig and production remain unchanged.
  Check this candidate's STATE before rendering or continuing; no browser pass.

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

Normal cloud Git write authentication is unavailable. The original `ed97cf3` transfer and later incremental bundle remain historical
archives. Current authorized workflow is dot-cloud development, complete incremental
backup through Library, synchronization to the designated non-C Windows drive,
then push from that already authorized desktop. The parent task coordinates
that executor; do not create overlapping desktop tasks or develop there.
Never place project files, archives or temporary recovery copies on C:. No local bundle proves remote delivery. Keep exact snapshot heads
and prerequisites; don't rewrite bundles under an existing filename or claim
later commits are included. The incremental bundle through `613c1cb` requires
both `ed97cf3` and the complete migration `4f28bd4`. Later documentation and
door-review hardening commits need a subsequent transfer. No credentials,
private communication receipts or signed upload links belong in this repository.

## External recovery checkpoint

The complete incremental backup through `01097c9c0ccf50497214bac421b569621f36e533`
was externally saved and officially downloaded/reassembled for SHA verification.
Recovery chain: original migration `4f28bd4` -> backed-up cloud `01097c9`.
Its77 new LFS objects contain actual model/image bytes, alongside the Git bundle.
This does not mean the development branch was pushed to GitHub. Subsequent
verified milestones should back up only the increment after this checkpoint,
including every newly reachable LFS object, without resending the old archive.
Private storage receipts are kept outside the public repository.

## Next concrete work

Obtain or verify variant-specific seat/lock/mount construction before removing
the remaining lamp, hood-lock and equipment installation failures. Targeted
source-backed geometry and mechanical work can continue while browser and Git
handoff limitations remain open. Preserve the distinction between published
dimensions, fitted geometry, conditional checks, failures and untested states.

## Independent cab-panel study, 2026-10-01

`testcar/outputs/cloud-cab-panel-study-20261001/` retains an editable standalone
study of the distinct Fig101 left and Fig102 right panels. Fresh native readback
checks 247 closed finite positive-volume solids and 57 real through-holes with
positive/negative controls. Three actual Cycles views were inspected; appearance,
factory dimensions, conflicting source captions and cabin installation remain
OPEN. No vehicle master or browser asset was changed. All 16 vehicle gates stay
OPEN. This stage follows externally backed-up checkpoint `01097c9`; its next
complete increment must include the new blend and all image LFS entities.

The subsequent panel-study checkpoint `f619cb66959533f13ddee5aba53739ebbab98d5c`
was also externally saved and officially read back, with its full archive hash
and all four new LFS payload hashes verified. Current recovery chain is
`4f28bd4 -> 01097c9 -> f619cb6`. Later increments start after `f619cb6`.
Desktop synchronization and remote publication remain separately unconfirmed.

## Cab-panel fit trials, 2026-10-01

Two independent Master installation trials are retained in
`testcar/outputs/cloud-cab-panel-fit-20261001/`. Both keep the new study size
and inherit a legacy dashboard proxy anchor, never a factory datum. The first
centre-plane trial has 2 panel-to-existing rest surface intersection pairs. The
second driver-facing-plane trial has 15, including steering-wheel interference.
Both preserve 247 closed solids / 57 through-holes in fresh readback; that does
not accept either installation. The second reader exits 2 on surface contacts.
Old dashboard/gauge proxies are retained in hidden editable objects; unrelated
mesh geometry, authored UVs and transforms remain unchanged. Source metadata
and the fit trials remain unaccepted. No browser asset or production was changed.
The old steering-column/seat intersections are separately retained in
`cloud-left-driver-rest-audit-20261001`, not solved by a new instrument layout.


Third panel trial restores the exact four seat bases and adds independent
saved-file identity and ViewLayer/camera eligibility checks (7,708 original
meshes, 362 study descendants, 248 eligible objects, zero scoped failures).
Panel installation still has 15 rest surface-intersection pairs. Two actual same-camera seat-base comparison images are now complete and
inspected. They show the restored front-left base, including the still-failing
legacy steering-rod intersection. The earlier exit137/no-PNG attempt is retained;
its cause is not established. No whole-vehicle gate passes.


Corrective checkpoint `8cb82c90245f92c9d0fdb9ad7da3053aa77f0d18`
was externally saved with all three new LFS entities. All archive payload hashes,
four official read-back parts and the reassembled archive SHA-256 passed. Current
complete incremental recovery chain is `4f28bd4 -> 01097c9 -> f619cb6 -> b9fb590
-> 8cb82c9`. The defective b9 trials remain as withdrawn historical evidence.
External storage does not confirm desktop synchronization or GitHub publication.


The independent `cloud-steering-photo-hypothesis-20261001` native candidate
follows the photograph-supported upper-rearward column direction and makes the
whole wheel/column coaxial. It preserves the old wheel centre, angle magnitude
and column bottom Z as FITTED; bottom X and length are refitted, not factory
mounts. Fresh readback retains all10,405 objects and four seat bases in the stated
identity scope. One column/cushion and two unchanged panel/wall object pairs
remain failed; reader exits2. Two actual native Master inspection images (matched footwell and left-cab overview)
have been rendered and inspected; blank gauges and prototype materials remain
unaccepted. No production or
browser changes. All16 gates remain OPEN.


Checkpoint `63fe135bf1b1c9237c6158519fb77203a9f9a6be` and its complete
increment after8cb82c9 are externally saved. The official single-archive route
and whole-file readback succeeded, including all3 new LFS payload SHA checks.
Recovery chain now ends `... -> b9fb590 -> 8cb82c9 -> 63fe135`. Begin future
increments after63fe135. Desktop sync/GitHub push remain unconfirmed.


In-progress independent VA180 front study: `cloud-va180-face-study-20261001`.
Original1977 operation paragraph plus three inspected firsthand product photos
support a curved upper display, opaque lower cover, correction screw and
independent pushbutton. Unknown manufacturer/batch dimensions, font, button
stroke and minor/voltage markings are not claimed calibrated. Root trial and
iteration02 retain backing/control and backing/case contact failures. Iteration03
has10 closed study solids,3 actual openings,45 scoped rest pairs with no unexpected
intersections, and sampled independent button return. Its two native images were
inspected; side-face shading is being refined in iteration04. No vehicle/panel
installation or production change, all16 OPEN. Latest externally saved checkpoint
remains63fe135 until this new study has been committed and fully archived.


## Verified GitHub publication, 2026-10-01

Normal non-force push published `63fe135bf1b1c9237c6158519fb77203a9f9a6be` to
`development/cloud-maz543a-20260930`. Independent remote ref and GitHub commit/tree
reads match root tree `7255a6709fa28f2c58c59340cb200a64caf0317e`; migration remains
`4f28bd4618ca7e272f6049b9f615821b8e0bb8f1`. All91 newly reachable LFS objects
(1,838,047,263 bytes) completed standard Git LFS upload/existence confirmation.
Four representative production/candidate Master and GLB entities were freshly
downloaded by official Git LFS into an initially empty separate store; all four
byte counts and SHA256 values matched (171,551,481 bytes). The remaining87 were
not individually re-downloaded. The first scan failure is retained; normal Git
metadata refetch resolved it before successful remote retrieval.

The user's latest workflow is cloud development -> normal GitHub push -> stage
Slack report. Desktop synchronization is cancelled. Historical Library backups
remain retained. No production asset was promoted, and all16 gates remain OPEN.

## Subsequent verified checkpoint and wheel-alignment diagnosis

VA180 partial study iteration04 is committed and normally pushed at
`504c1d5093b1c7f16a1879f41cba44a1ef111633`. Remote ref and root tree
`558038801839fcae1b86f5aae54dce5887cd0feb` match. All9 new LFS entities
(15,203,039 bytes) were freshly downloaded by official Git LFS into an empty
verification store and passed byte/SHA checks. Both actual native study images
were delivered to the dedicated progress channel. It is still an independent,
partially referenced device study; not installed or factory-dimension validated.

Original 1977 manual pp24/316–317 now establish a nominal steered-wheel camber
magnitude1° and positive toe ranges at1040mm reference diameter. The new read-only
`cloud-wheel-alignment-20261001` diagnosis measures actual production front tyre
profiles at neutral pose: camber approximately0°, simultaneous static sidewall
rear-minus-front separations approximately0mm on both front axles. This exposes a
nominal geometry gap, not a load/pressure/rolling-qualified alignment test. Source
SHA is unchanged. No adjustment is made until native carrier/hub/suspension
semantics and measurement conventions are resolved. All16 gates remain OPEN.

The next independent `cloud-va180-panel-fit-20261001/MAZ543A_Master.blend`
appends the retained partial VA180 study at the existing B4 fitted hole. All10,405
old objects are retained; exactly8 B4 proxies are hidden and preserved. Fresh
readback retains all four seat-base regions and reports no scoped identity
failures. All28 appended objects match their source identities and expected
uniformly scaled world transforms. New-vs-existing static surface contacts are0
across20 broad-phase pairs;192 actual plate-opening rays pass with a192-hit
disabled-Boolean negative control. These are scoped checks, not assembly
acceptance. Existing column/cushion and two panel/wall failures, caption64 conflict,
fitted dimensions and incomplete calibration marks remain unresolved. Two actual
same-camera native close-up images and one current-candidate whole-vehicle image
have been rendered and inspected. The whole view retains the complete vehicle
envelope in frame; its small internal instrument is not visible at that scale.
Production remains unchanged and all16 gates remain OPEN.

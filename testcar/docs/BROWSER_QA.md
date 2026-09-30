# Live browser observations — 2026-09-05

Latest planetary core: [source/native/browser scope](PLANETARY_CORE_20260908.md).
The new asset loaded in the full vehicle; first/second/third gear selection,
slow motion, gear-only inspection and pause were exercised. This does not validate
clutch contact, full assembly clearance or final photorealism.

Latest transmission increment, 2026-09-08: see [transmission notes](TRANSMISSION_REFERENCE_NOTES.md).
The live browser checked R + low (-24.0860), R + high (-13.0194), neutral coast,
and cleared the false starting-neutral warning after the engine was already running.
Two 1280x720 captures are in `E:/Maz543/restoration/transmission-ratios-20260908/screenshots/`.
No transmission geometry or photoreal acceptance is claimed by these UI checks.

Latest, 2026-09-08: [round-wire spring QA and screenshots](CONTINUATION_20260908.md).
Full-coil inspection, independent left release, slow motion and pause were checked
against `spring-round-wire-20260908`. Older observations below retain their own scope.

Actual local application at http://localhost:3000/, inspected through the App's
browser. These are partial observations, not completion of docs/ACCEPTANCE.md.

- Standard rendering: mirrored black patches on doors/inspection lid disappeared
  after Blender winding repair and AO rebake. Debug no-baked-ao is not required.
- Door controls: four separate buttons, continuous actual angle display. One door
  reached 99 degrees while the other three remained at zero; real open aperture
  exposed the seat instead of a solid body panel. Blender separately checked eight
  rays through four openings and two wall samples outside the openings.
- New engine module is visibly loaded, with camshafts, nested springs, forged
  main/articulated rods, pistons, manifolds and actual accessory outer geometry.
  It replaces the old colored generic engine. Count shown by the interface is now
  3,968 geometric instances across the vehicle and new engine module.
- Independent engine observation controls were used: assembled exterior,
  open cam covers, internals, longitudinal section. The last section observation
  exposed real hollow mesh geometry and the crank/rod assemblies.
- Pause held at 550 degrees across control actions; after a development reload it
  reset to zero and remained paused. Resume changed the crank angle again. Native
  Blender separately checked 61 frames of actual mesh/joint contact; JavaScript
  checked 2,881 geometric samples. See outputs/d12-native-verification.json and
  outputs/d12-verification.json. These do not prove physical combustion/startup.
- Two browser issues were caught and repaired: the narrow 791-pixel App window
  cropped the focused engine; camera fit now uses viewport aspect and available
  area. Asynchronous reload could ignore a selected open-cover state; the material
  and visibility pass now reapplies after asset loading.
- Live GPU identity: ANGLE / NVIDIA GeForce RTX 4070 SUPER / D3D11. In the small
  longitudinal-section engine view, observed snapshots ranged from 36 to 53 FPS.
  A GPU timer snapshot was 5.86 ms; 734 draws and 1,245,259 submitted triangles
  include rendering passes. The host had other workloads during this observation.
  This is not a controlled benchmark or proof of stable full-vehicle performance.
- Opaque assembled views now cull hidden piston/rod/valve/spring groups while
  continuing the joint calculation. Section/x-ray reveal them again. Full-vehicle
  FPS, large viewport performance and sustained GPU timings still need review.

Build and glTF correctness do not establish photorealism. Cast surface texture,
paint wear, glass, photo silhouette overlays and complete vehicle functions remain
open. No final photorealistic product demonstration acceptance is claimed.

## Suspension pass, 2026-09-05

- Loaded the separate Blender suspension alongside the updated body and D12 in
  the actual in-app browser. The current asset contains 1,716 authored parts and
  80 semantic transforms; the exported GLB has zero validation errors/warnings.
- Selected front-left wheel station, removed the protective tubes/damper shells
  and observed the exposed torsion bars, rod, piston and lower fork connection.
- Paused at -25 mm. A subsequent accessibility snapshot after independent work
  kept the same -25 mm, 18.9 kN support load and -33 mm body-heave readings.
- Stopping test excitation unpaused the mechanism and set excitation to zero.
  A later live snapshot returned 0 mm relative travel, 0 mm body heave,
  approximately zero roll and 25.2 kN static wheel support force.
- Single-station inspection now hides the redundant selection card and fits the
  complete assembly. The former selection wire box wrongly included hidden
  stations; it now uses visible geometry and is suppressed in isolation.
- At 791 px app width the original whole-vehicle camera cropped the nose.
  Full-vehicle framing now uses the same projected-bounds fit as component views,
  recalculating after load, isolation changes and resize.
  A subsequent actual screenshot at the same width showed the complete front
  bumper, both cabs and rear frame within the viewport.
- Current narrow-view snapshots on RTX 4070 SUPER ranged around 21–29 FPS while
  the host was busy. An open single-station snapshot submitted 450,745 triangles
  across 208 draws. These are observations, not a controlled performance result;
  full-vehicle draw cost remains substantial and performance acceptance is open.

## Electric start and motor-detail pass, 2026-09-05

- Current four-module vehicle loaded in the normal local App browser, without
  disabling baked AO. The displayed count is 5,633 geometric instances.
- Guided start showed zero crank RPM while the electric pump built pressure,
  then settled at approximately 550 RPM with starter current zero and pinion
  shift zero. Fuel cut showed a nonzero coasting speed before stopping.
- Manual controls were operated through the visible UI. With ground disconnected,
  a held starter button produced no starter current or crank rotation. After
  connecting ground, preoil pressure rose while crank RPM stayed zero.
- A later manual start showed 194 RPM, 32.5 mm shift and a positive starter current
  during engagement. Holding the auxiliary button beyond the procedure limit
  visibly raised the five-second warning; manual mode did not pretend an original
  automatic cutoff existed. Both buttons were then released. The starter current
  returned to zero, the pinion withdrew to zero, and the engine settled at 550 RPM.
- That test exposed a partial-engagement clamp defect in an earlier revision.
  The corrected solver permits withdrawal below the first-contact axial gap;
  the subsequent live manual test and numerical regression both verified exit.
- Disconnecting battery ground with fuel still enabled left the diesel running
  at about 550 RPM and showed zero bus voltage. Fuel cut then showed 542 RPM while
  coasting. This tests the reduced simulation, not a calibrated real-engine map.
- Pause held the starting/engine state across subsequent UI reads; stop resumed
  the simulation before cutting fuel. Pump RPM and total gallery-flow labels are
  now component-specific. The pump tab links to fig.24 instead of the C5 section.
- The MN-1 stator inspection button removes the explicitly unmeasured armature
  envelope and exposes the photo-fitted pole shoes, insulated bundles and eyelets.
  Its source link and incomplete-armature/brush status are visible in the UI.
- Component inspection uses a compact title and larger viewing area. The scale
  bar derives from the perspective projection at the observation centre; observed
  labels changed between 50, 100 and 200 mm as the framing changed. The C5 housing
  view hides the separate flywheel ring; mechanism view fits both parts together.
- Single starting-component snapshots reached about 50–60 FPS on the RTX 4070
  SUPER. A stator snapshot used 108 draws and 225,129 submitted triangles; a full
  vehicle snapshot used 3,137 draws and 11,657,611 triangles at 36 FPS. These are
  live observations under shared host load, not a controlled benchmark. Full
  vehicle rendering performance and photoreal acceptance remain open.


## Cam-bank inspection (2026-09-05, localhost, clean reload)

- Loaded the cam-1 engine module with 5,765 total geometry instances shown by
  the UI. No asset-load failure was visible. The prior HMR-only stopped/paused
  state was discarded with a clean reload before final interaction verification.
- Engine shortcut progressed through preoil to 550 RPM; selecting cam inspection
  isolated its meshes. Left, right and both-bank modes were visibly distinct.
- Pause held the displayed crank angle at 303 degrees across bank switches and
  later reads. Resume advanced to 314 degrees and subsequent values; the actual
  gear/lobe poses changed in the screenshots. The ×0.035 switch was active.
- Gear-end framing showed the two gears and retainers together; the displayed
  perspective scale changed from 100/200 mm at bank view to 20 mm at the end.
- The isolated cam view hides the chassis floor/grid and fits the directional
  shadow camera and bias to the small assembly. AO radius is 15 mm in this view;
  body settings are restored outside it. Ground-steel materials and sharp
  machined shoulders no longer shade as a uniformly glossy rounded surface.
- One-bank observations used 37 draws / 1,255,725 submitted triangles. Sampled
  FPS varied roughly 28–46 under shared host load. These are observations, not
  a controlled performance benchmark or a photoreal acceptance result.
- Browser left at normal localhost URL, left-bank gear close-up, running at
  reduced display speed, unpaused. The temporary manual tab was closed.


### Timing train — 2026-09-05

Clean-loaded localhost:3000 after the 9,330,608-byte engine export. The page
reported 5,838 geometry instances. Engine quick action entered prelubrication
then self-running 550 RPM. The timing mode displays all 25 gear identities;
crank-takeoff and lower pump-train buttons frame the respective gear groups.
Enabled shared slow motion (x0.035). Paused at displayed 113 degrees; that angle
held across pump and crank close-up changes, then resumed. Native geometry and
exported shaft transforms have separate reports in outputs/timing-*-verification.json.

Observed timing overview: 261 draws / 2,974,293 submitted triangles. The closer
crank framing culled to 201 draws / 1,445,081 submitted triangles. Samples were
roughly 23–31 FPS with concurrent workstation workloads; these are observations,
not an isolated performance benchmark or final visual acceptance. Full-vehicle
rendering remains much heavier. Housing accuracy, measured dimensions, worn
surface references and physical accessory operation are still unresolved.

### Circulating water pump — 2026-09-05

Clean-loaded localhost:3000 with the 9,996,500-byte engine module. The browser
reported 5,963 geometry instances. Engine quick action completed guided startup:
550 crank RPM and 825 water-pump RPM. The pump view shows the native cast shell,
bearing rolling elements, spring, face-seal stack and curved impeller blades.
Both shell halves close into an opaque housing. The near fixed bearing race
halves also return when the housing is closed.

Paused at displayed 230 degrees, then switched between the impeller underside,
seal detail and whole pump: the angle stayed 230. Resumed in x0.035 slow motion
and observed the displayed angle advance to 246 degrees. A discovered camera
restriction previously clamped underside inspection at the horizon; isolated
assemblies now allow the full underside orbit. The corrected impeller view was
visually checked, as were seal close-up and complete casing.

Pump section observations were about 55–60 FPS, 185 draws and 325,345 submitted
triangles; full casing about 197 draws / 381,293 triangles. These are display
samples, not an isolated benchmark. Full-vehicle observations during concurrent
work ranged roughly 16–45 FPS and remain an open performance concern. Native
Cycles section is `outputs/d12-water-pump-section.png`. Model geometry checks,
web transform checks, all 169 native start-sequence bindings, TypeScript and
production build passed. No fluid/thermal or full-vehicle realism acceptance is
implied. Browser left in the open pump view, running with shared slow motion.

### Twin cooling fans and thermal circuit — 2026-09-05

Loaded the separate 1,162,748-byte cooling GLB and corrected body in localhost:3000.
Browser reports 6,674 authored geometry instances across the combined assets.
New cooling controls operate two electromagnetic clutches, manual shutters,
heater branches and environment temperature. Both fan readouts were about 549
RPM at idle; left switch-off produced an observed 147 RPM on the left while the
right stayed 549 RPM. Coil readouts were 0.00 / 3.15 A and axial engagement
0.00 / 1.50 mm. These are fitted simulation outputs, not original specifications.

Used the visible slider to close shutters from 100 to 0, opened the left heater
branch, and returned shutters to 100. The displayed loop flow changed from
about 92.4 to 94.0 L/min with the added branch. Paused at simulated 56.5 s, moved
between assembly and clutch detail and toggled the mobile panel: time, 147/549
fan RPM and 71.4/71.2°C head/outlet readings remained unchanged. Near inspection
hides the adjacent fan and blades so the left slip ring, coil, armature, spring,
needle bearings and brushes can be inspected.

Checked both 1280-wide and 461-wide page layouts. Fixed an observed mobile bug:
sliders mounted inside the hidden inspector retained hidden thumbs when opened.
Remounting the inspector on its open/closed transition lets the component measure
its visible track; keyboard Home/End then successfully reached 0/100. Adjusted
camera framing to put closeups below the title and action controls. At narrow
width the panel can be closed to inspect the model and reopened with retained
simulation state.

Also fixed a stale development-server module (confirmed by reading its served
source before restart) and excluded migrated native auxiliaries from obsolete
seed-mesh bindings. The latter had moved batteries into the isolated cooling
view. Final isolation was visually checked. Detail observations ranged about
48–60 FPS, 249 draws / 86,101 submitted triangles; full vehicle about 21–30 FPS
in the narrow window under concurrent work. These are local observations, not
performance acceptance. Full vehicle photorealism and installation clearances
remain open, as do the detailed fan gear drive and complete coolant passages.
Final browser handoff: left clutch detail, housing open, both fan switches on,
shared motion resumed at x0.035, shutters 100%, left heater branch open. The
mobile control panel is closed with its visible reopen button available.
# 2026-09-06 — lower cooling drive increment

Local browser `http://localhost:3000/`, 461 px wide; cooling GLB cache revision
`lower-2`. The visible UI was used to enter Cooling → Inspect lower gearbox,
toggle the housing, start the engine with the existing guided start, and enable
0.035× slow motion. Separate bevel gears, bearing cages/balls and pump gears
were visible in the native exported module. Steady UI readouts: engine/fans
about 549 RPM, both coils 3.15 A, fitted engagement travel 1.50 mm.

The isolated open lower-drive view reported 59–60 FPS after background builds
finished (RTX 4070 SUPER; not a cross-device performance guarantee). During
concurrent Blender/build work the full vehicle reported 8 FPS and the local
inspection 19–44 FPS. Full-vehicle performance acceptance remains open.

Pause retained the complete cooling panel readout at 435.9 s while assembled
and open layers were switched. Returning through the complete cooling assembly
and back to the lower drive restored the fitted inspection camera. Manual zoom
works, but the narrow window and overlaid controls limit close-up usable space;
camera framing and the full-size visual acceptance still need further work.

Native checks: 178 cooling poses over 21 frames; 354 combined engine/start/cooling
poses in both vehicle masters. Lower gear/casting and pump pair/body surface
intersection checks passed 49 samples. Six actual bearing meshes match nominal
310/307 envelopes within 0.0001 mm numerical tolerance. This does not validate
their fitted rolling internals, manufacturing fits or loaded behavior. Cooling
GLB validation: zero errors/warnings. TypeScript, model checks and build passed.
Source and remaining reconstruction limits: `COOLING_REFERENCE_NOTES.md`.
# 2026-09-06 — upper cooling gearbox increment

Local URL `http://localhost:3000/`, cooling cache revision `upper-1`, 461 px
viewport. Used the actual controls to inspect the left upper gearbox, switch
assembled/open views, execute guided engine start, and enable 0.035× slow motion.
The exported bevel pair, four bearing assemblies, input flange, stepped output
shaft and rear brush holder were visible. Both fan readouts settled near 549 RPM
with 3.15 A coil current and fitted 1.50 mm engagement.

Pause retained the entire cooling readout at 327.3 s while opening/closing the
housing and remounting the mobile panel. Restored slow motion and left the page
on the open upper gearbox. Observed 17–26 FPS in this session, including during
and after background work; no full-vehicle performance acceptance is claimed.
The narrow inspection framing still leaves limited close-up screen area.

Cooling GLB: 14,009,768 bytes, 254 pose bindings, no validator errors/warnings.
Native module: 1,237 mesh/curve pieces, including 298 upper-drive meshes.
The local upper pairs/cases passed 49 angular samples each; all eight nominal
bearing envelopes matched. Shared 21-frame inspection compared all 430 engine,
starting and cooling joints in both whole-vehicle masters: zero position error,
maximum angular error 0.000061 radians. TypeScript, model checks and build passed.
Cardan flange pattern and installed drive closure remain unresolved; see the
source notes. These results do not accept physical or original-vehicle fidelity.

## 2026-09-06 four-hole interface correction

Browser asset query `interface-4`: cooling GLB 14,224,176 bytes, 254 bindings,
zero validator errors/warnings. Native ray checks passed all four flange bodies:
36 clear bolt-hole rays, 32 surrounding solid rays and zero non-manifold edges
per flange. Upper gear/case and bearing checks passed again; both vehicle masters
retained all 430 shared poses across 21 frames with max angle error 0.000061 rad.
The body validator, TypeScript and production build passed.

The previous workerd preview returned HTTP 500 `fetch failed`. Restart attempts
failed on internal 127.0.0.1 connections, including with the Worker inspector
disabled. A process-local Node preview (`MAZ_NODE_PREVIEW=1`) restored the page;
the Sites plugin remains active and production builds still use Cloudflare.
This recovery is not Worker runtime validation or hosted deployment acceptance.

At 461 px viewport width, inspected both assembled gearboxes, the new round
four-hole lower flanges, upper internals and the new original-catalog link.
Guided starting reached 549 RPM on both fan readouts, 3.15 A coil current and
1.50 mm engagement. Restored slow motion and left the page on open left upper
gearbox. Observed approximately 8-19 FPS during the session, partly concurrent
with build work; the final open view showed 14 FPS. Narrow framing and performance
remain unaccepted. Hole spacing, mating dimensions, Cardan placement and complete
shaft velocity closure remain fitted or incomplete.

## 2026-09-06 independent Cardan mechanism

`cardan-2` GLB: 907,380 bytes, 213 authored meshes and 190 pose bindings,
zero validator errors/warnings. Native checks sampled 200 angle/stroke states
without opposing-fork, fork/cross or sliding-spline surface intersections.
Four actual cap-pair envelopes match the chosen 28 x 73 mm 408-family envelope.
776 mathematical states passed orthogonality, end-phase and ideal rolling
contact checks. The initial inner-spline end-cap mesh failed and was corrected
before this result. TypeScript, body validation and production build passed.

The previous temporary browser tab had been cleaned up. Created in-app tab 4
for QA, using the existing Node development server. At 1280 x 720, selected
Cooling -> Inspect Cardan, switched assembled/internal views and exercised
the two sliders through both endpoints. At 30 degrees and 40 mm extension,
the UI showed 25.0 mm spline engagement. Guided starting produced approximately
879 RPM at both ends and a phase-dependent intermediate rate (804 RPM in one
observed sample). At zero angle and zero extension all three readouts matched
879 RPM and engagement was 65.0 mm. Pause and slow-motion controls operate the
same accumulated crank signal used for the other inspection modules.

The assembled stopped view showed 59 FPS after the camera transition; an
internal running/slow view showed 30 FPS. These are spot observations, not
whole-vehicle performance acceptance. The component is visibly labeled as an
independent inspection. It is hidden in ordinary vehicle views and has not
been substituted for the unresolved installed Cardan placeholders.

Follow-up: hidden torsion tube vertex deformation is skipped during isolated
non-suspension inspection; suspension physics still steps and visible tube
deformation is recomputed from its base geometry. TypeScript and the production
build passed after this change. On the actual in-app page, guided starting in
Cardan view again reached 879 / 802 / 879 RPM at 30 degrees and 40 mm stroke.
Switching to suspension restored the moving first-left station; opened its
torsion/damper internals and observed changing travel (-13 then -19 mm) and
support force. Returned to Cardan and restored slow motion. The suspension
internal view showed 59-60 FPS at 1280 x 720. These spot readings do not establish
a controlled before/after performance gain or full-vehicle rendering acceptance.

The Cardan native master now includes per-mesh evidence properties and a packed
reference collection. Saving/reopening the file retained all source image packs,
all 213 part annotations and an unchanged digest of mechanism vertices,
transforms and animation tracks. This metadata-only update does not alter the
browser GLB or claim newly measured dimensions.

## 2026-09-06 cab profile and enclosed cooling geometry

The rebaked body asset `cab-profile-1` is 20,332,232 bytes with 360 nodes and
214 mesh definitions; glTF validation reports zero errors and warnings.
Export triangulation supplies normal-map tangents without changing the editable
authoring master's topology. TypeScript and the production build passed after
the front camera and conservative enclosed-cooling visibility changes.

In-app tab 2 at 1280 x 720 loaded the corrected front profile. The front preset
now fits the nose projection; one closer scroll keeps the front shell in view.
Cab dimensions and material fidelity remain unaccepted. Whole-vehicle spot
readings remained roughly 16-23 FPS; isolated-component results must not be
reported as whole-vehicle performance.

Cooling -> lower gearbox was inspected closed and open. The closed view retains
the casting, cups, flanges and external hardware. Opening the housing restores
the bevel gears and bearing rolling elements hidden by the closed-view
optimization. Guided starting reached 549 RPM, then slow motion was enabled;
visible gear/flange poses changed. Observed settled spot readings were 60 FPS
closed and 56-60 FPS open/running, not a controlled performance benchmark.
The source-linked panel still discloses fitted tooth counts and unresolved
installed Cardan closure. This check does not validate loaded tooth contact,
original ratios or the complete installed cooling transmission.
# 2026-09-08 local restoration check

See RESTORE_20260908.md for the current GTX 970 observations, screenshots,
clutch-contact export version and remaining acceptance limits. The current web
cooling asset is 14,495,320 bytes with cache version clutch-contact-20260908.
Earlier entries above are historical and do not describe current machine results.

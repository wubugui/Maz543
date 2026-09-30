# Front cab and cooling clearance study

Source: [Vladimir Zinin, MAZ-543A museum front photograph](https://commons.wikimedia.org/wiki/File:MAZ-543_special_purpose_truck,_Strategic_Missile_Forces_Museum.JPG),
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Unmodified original
downloaded and inspected at 1415 x 1130 pixels, locally
`work/reference-docs/MAZ543A-museum-front.jpg`. The caption identifies the 543A
chassis; the photograph is not a calibrated orthographic survey.

The lower central opening is visibly wider than the roof-level cab gap. Approximate
image landmarks are x=570..880 at the lower opening, x=610..820 at the upper gap,
and x=410..1040 for the cab front's overall width. Perspective, rounding, occlusion
and picking uncertainty prevent treating these as millimetre measurements. They
give a lower-opening/overall-width ratio around 0.49, while the old model's straight
inner walls give 1.11/3.05, around 0.36. This is a shape discrepancy, not a fan
diameter measurement.

`inspect-cab-front.py` renders the actual whole-vehicle master with an orthographic
front camera for shape inspection. Workbench shading deliberately exposes geometry;
it is not photoreal rendering acceptance. The image also shows unresolved windshield,
nose-height, grille and engine-enclosure proportion differences.

`prepare-cab-profile.py` builds a constrained triangulation around the original
window opening, split at the front's slope break. It verifies area coverage and
two-face edge incidence before writing the mesh input. `cab_front_profile.py`
reconstructs both facade panels, fits the lower inner-wall relief and widens the
front grille by 10 percent in a separate native study. Its lower gap is about
1.49 m; the 1.92-2.18 m relief transition and hidden longitudinal continuation
are fitted. They are not established by the visible photograph.

The initial deformation-only facade study produced inappropriate creases. It was
replaced by the explicit planar construction; do not promote the initial warped
panel to the main model. The editable trial is `outputs/MAZ543A_CabFit_Study.blend`.
The rebuilt facades passed evaluated closed-mesh checks (zero non-manifold edges,
positive volume) and eight aperture/solid/relief rays. The corrected native study
was promoted to `outputs/MAZ543A_Master.blend`. Matching texture atlases were
rebaked and the browser asset was exported as `cab-profile-1` (20,332,232 bytes,
360 nodes, 214 mesh definitions, zero glTF errors or warnings). Export-only
triangulation of n-gons preserves UVs and provides explicit normal-map tangents;
the editable authoring master retains its original construction topology.
The actual browser front view was inspected at 1280 x 720, including a closer
zoom. Its camera now frames the front projection at the nose instead of fitting
the full chassis depth. This verifies visibility of the corrected profile, not
calibrated photo agreement or final material quality.

The existing fan shroud collision cannot by itself establish which original
dimension is wrong. Check the trial's actual mesh clearance separately, retain
the original audit as evidence, and continue seeking opened-cab/installed cooling
photos. Fan diameter, gearbox axes, Cardan installation and all full-vehicle
acceptance gates remain unresolved. The corrected study and promoted native master
both clear the two shroud/wall surface tests at frame zero. This replaces the
earlier 32 crossing triangle pairs per side, but does not prove original mounting
dimensions, all installed clearances or dynamic clearance through cab movement.

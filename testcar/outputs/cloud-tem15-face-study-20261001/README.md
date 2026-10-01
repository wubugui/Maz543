# Partial TEM15 face study from a dated product photograph

The 1977 vehicle manual identifies TEM15 pressure instruments. The newly inspected
original seller photograph shows an instrument next to its passport dated1978,
with 0/5/10/15 numerals and КГ over СМ² units. A separate image on the same page
uses MPa×0.1 and is not merged into this older face. Provenance and SHA values are
in `reference/tem15-face-source-20261001.json`. Original watermarked photographs
are kept only for local reference review, not packed in or redistributed with
these models.

This study represents only a black front casing envelope, separate clear disc,
dial, fitted pointer, four major marks and six editable text items. All dimensions,
depth, glass section, font, positions and angles remain fitted from an oblique
view. Minor ticks are omitted because their full count and locations are not yet
resolved. No manufacturer-scale calibration is claimed. It is not installed in
the vehicle and does not add a sensor, hose, rear connector, clamp or internal
mechanism from insufficient evidence. A1978 specimen is not proof of the exact
1977 vehicle installation batch.

The first native Curve-extruded pointer had duplicate cap vertices and failed the
closed-solid gate; its blend and failed readback remain at this directory root.
`iteration-02` uses native conversion and a0.1-micrometre Weld modifier, retaining
the hidden editable Curve. The distinct pointer vertex coordinate set is exactly
unchanged. Fresh readback passes9 closed positive-volume study solids (including5 painted
mark solids, not an original manufacturer component count),36 physical-pair
static surface checks, the open-cavity ray test and a disabled-Boolean negative
control. The six observed text objects retain packed fonts. No source photographs
are loaded in Blender. This is a scoped structural check, not a full containment,
installation, metrology or electrical acceptance result.

Build with `scripts/build-tem15-face-study.py`, retain the failed first readback,
then run `repair-tem15-pointer-caps.py` and fresh
`verify-tem15-face-study.py --directory outputs/cloud-tem15-face-study-20261001/iteration-02`.
`render-tem15-face-study.py` produces actual Cycles source views. The editable
native objects use Blender primitives, Curve, Boolean and Weld operations.
All16 whole-vehicle gates remain OPEN. The production vehicle is unchanged.

The initial two-view96sample render run reached its explicit180-second timeout
after saving the first front image. That image and original script are retained;
the missing oblique image was not treated as complete. Its glass noise and bright
rim reflection were rejected for presentation. A separate64sample/720px Cycles
view uses0.15-times review light power and native denoising. It changes no model
geometry or materials. This yields readable observed labels, while minor ticks,
font matching and precise proportions remain unaccepted. Use `--view front` or
`--view oblique` and `--lighting02` for the latter view settings. Each view writes
its own record, allowing recovery without rerendering a completed image.

The first lighting02 oblique image is also retained as a rejected visibility
attempt: a softbox reflection obscured the scale. The lighting03 view moves only
the review lights outside the camera reflection direction, leaving geometry and
materials unchanged. The resulting front/oblique pair was inspected as actual
pixels; it is a readable partial form study, not an exact restoration.

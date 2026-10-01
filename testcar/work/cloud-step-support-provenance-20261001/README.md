# Retained step-support source chain and repair boundary

The four cylinder-shaped closed-door contacts match **fixed under-door platform
support links** in the retained authoring code. That functional name is inferred
from creation beside platforms and fixed cab parenting; it is not an individual
stored part name or a manufacturer hardware identification. They were not created
as door hinges. Dimensions and 24-sided tessellation are generator choices.

## Exact retained source, not current regeneration

The decisive retained file is `testcar/work/compiled/maz543.mjs`, Git blob
`5fc9408952de9549eb3d513071f6706d6df882aa`, SHA256
`bbdc06ed7bee43d6ac2a1f38170b9761e34a0e149a1f7486dd895ee9785aab06`.
It arrived in snapshot `d14c34641ee2ed5c2b1ab93e138727c2b607a83a`; the snapshot
date is not proof of its original authoring/export date.

- Lines124–125: side coordinate gives outer lateral plane ±1.455m
- Lines154–175: door intervals [-5.19,-4.08] and [-3.99,-2.91]
- Line173: one fixed platform per door, dimensions[length-.08,.055,.21],
  center[(start+end)/2,1.23,outer], parented directly to cab
- Lines174–175: two fixed links per platform at start+.1/end-.1, from height1.45
  to1.23, radius.025. Four per side at X−5.09,−4.18,−3.89,−3.01m
- Lines53–68: native Three cylinder/link construction uses24 segments; it does
  not specify a real 24-faceted physical section
- Lines155–172 put moving door components under dg; its hinge-like primitives
  have different radius.032/length.13 parameters at line169
- Lines503–530 merge compatible fixed siblings by material; lines537–545 assign
  sequential names. `cab_0063` identifies a batch, not one physical part

Current `lib/maz543.ts:92,100–101` uses different intervals
[-4.91,-4.03]/[-3.96,-3.01]. It would generate supports at
−4.81,−4.13,−3.86,−3.11m, shifting some by280mm. Other retained verify/animation
copies also differ. **Do not regenerate the original seed from those files.**
This investigation matches parameters, component positions/order and published
exact native-to-seed identity; it does not claim whole-seed byte regeneration.

## Original seed and retained batch

Original `mechanical-seed.glb`:8588120 bytes, SHA256
`5c5849b68a5fa62e903b46b5554b8eb942495eabb3a12cb26caf24742cd9681c`.
Node76 is cab_0063, mesh41, material steel, extras fixedDetailCount17. Its cab/root
ancestors have no transforms. Root accuracy explicitly describes estimated
reference geometry, not factory CAD. The material label is not material testing.

Independent binary decoding found17 exact-coordinate components, each148 indexed
vertices/96 triangles. Source order is four step links + four seat-back links +
one control stalk on the first side, then four step links + four seat-back links
on the second. Current cab_0063 retains16: all eight step and eight seat-back
links. Seed group8 is absent only from this batch; no vehicle-loss claim follows.

Published exact oriented-triangle matching is in
`work/cloud-closed-door-contact-components-20261001/component-report.json`.
The attached role map adds semantic inference only; it does not alter that data.
The four contacting groups map as follows:

| Current | Seed | Native X,Y,vertical Z (m) |
|---|---|---|
|1|1|−4.18,+1.455,1.23–1.45|
|2|2|−3.89,+1.455,1.23–1.45|
|9|10|−4.18,−1.455,1.23–1.45|
|10|11|−3.89,−1.455,1.23–1.45|

Three.js/seed coordinates are X longitudinal/Y up/Z lateral.
`blender-model.py:19–20` maps C(x,y,z)=(x,−z,y); do not confuse source side sign
with native Y. The linked manifest rechecks all cited source bytes against the
then-current published checkpoint without executing either generator or Blender.

## Coexisting authoring schemes, not proven supersession

`prepare-blender.mjs:12–19` records the generator→seed/manifest route.
`blender-model.py:153–158` removes only shell/door/body subtree contents, leaving
direct cab siblings such as this material batch. Lines239–240 separately create
a bent `BL_Cab_{side}_step` at0.90–1.13m height and20 tread bars per side.
This explains how old supports and a later lower-step scheme can coexist. It does
not yet prove each original platform box remains in the current master or that
the old assembly was intentionally superseded. Next, identify the actual four
platform boxes and full current step assembly before revising it.

## Real-vehicle constraint

Both primary photo pixels were inspected: Michael Benolkin's Duxford MAZ-543
[right cab](https://www.cybermodeler.com/armor/scud/pages/iwm_scud_07.shtml) and
[left cab](https://www.cybermodeler.com/armor/scud/pages/iwm_scud_12.shtml).
They show a continuous lower step with three visible below-sill hanging members
per cab, unlike the generator's two short platforms/four straight links per side.
No visible hanger extends upward across the closed door face. See the previously
published `reference/cab-sill-step-rivet-source-20261001.json` for exact hashes,
observations and limits; no source photo pixels are republished here.

These two views of one museum vehicle do not establish the target1977/MAZ-543A
batch, metric dimensions, material, hidden attachment or flexible-member stiffness.
A future native structure study must label fitted geometry and retain original
parts/source. Reparenting supports to doors or moving/deleting cab_0063 wholesale
would contradict the known source structure and endanger its seat-back links.
The present item modifies no model, pose, visibility or runtime. All16 gates OPEN.

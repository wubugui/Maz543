# C5 starter / MZN-2 prelubrication reconstruction

The original user objective remains open. This module is a source-guided
mechanical and reduced dynamical reconstruction, not factory CAD or a validated
electrical, hydraulic or combustion model. Source images are packed in the
editable Blender master for local inspection, not republished in the website.

## Sources by component

| ID | Evidence and use | Limits |
|---|---|---|
| C5-F122 | 1973 MAZ technical description fig.122: inertia drive, helical shaft, buffer spring, cups, friction washers, bushes, stop disk, tail shaft, key and half rings | Sizes, spline starts/lead, stack count and friction law fitted |
| C5-2S-PHOTO | dzmd.ru C5-2S photograph: casing, bands, end ribs, terminal, eye | Later suffix; not an original C5 dimensional reference |
| C5-MOTOR-ENVELOPE | C5 series DC motor architecture from original manual | Armature represented only by an envelope and shaft; detailed winding, brush and commutator layout remains unbuilt |
| MZN-F24 | 1973 MAZ fig.24: gear pair, spline coupling, seal, body, lid, separate coolant heating jacket | Gear teeth and dimensions fitted; no unverified bypass valve imported from another vehicle |
| MZN-PHOTO | MZN-2 + MN-1 product archive photograph, TU23.108-199-92 | Later same-name assembly; early casting differences unresolved |
| MN1-MOTOR-ENVELOPE | MN-1 electric motor, manual specifies 24V / 500W | Armature remains an envelope; rotor winding and brush topology unresolved |
| MN1-DISASSEMBLY-2022 | ARNELLIT Studio, boatclub.ru posts149/157, 2022-03-17: four curved pole shoes, two recesses per shoe, wrapped field coils, leads and eyelets | User-identified MN-1 specimen without visible nameplate; dimensions, concealed field core and installed wiring routes fitted |
| MZN-MOUNT-FIT | Manual installation: ahead/below engine, inside right frame rail | Mounting pose and bracket holes not measured |

[Original C5 section and specification table](https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/022.htm).
[Original MZN section](https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/006.htm).
[1977 MAZ technical description](https://djvu.online/file/zjMdLY3MFjmTL).
Full local image provenance: D:/maz543-references/starting/STARTING_REFERENCES.md.

## Verified specification versus fitting parameters

C5: 24V, 15hp, 1100rpm at maximum power, 11 pinion teeth, clockwise viewed
from drive end. The table's 24 ±1.5mm pinion projection has an incompletely
established datum and is not used as total shift. The reconstructed ring has
132 teeth, 4.7mm module and 20-degree pressure angle; NONE of these three are
confirmed factory values. Centre distance follows the reconstructed pitch
circles. Helical lead72mm is fitted; axial stroke32.5mm is derived from the fitted gear widths and a3.5mm axial rest gap.

Four original 12-ST-70 batteries are each24V/70Ah, parallel (280Ah).
The present electrical model uses their aggregate capacity; individual cells,
plates, ventilation, contactor mechanics and physical cab buttons are still open.

Preoil required pressure≥2.5kgf/cm²; pump maximum continuous1min; starter≤5s;
retry interval25–30s. These are OPERATOR PROCEDURES, not established electronic
interlocks. Guided mode performs that procedure, including waiting for neutral.
Manual mode supplies power directly from the separate ground/pump/starter
controls and reports procedural violations without inventing oil/neutral switches.
Manual buttons are momentary and release on pointer cancellation or keyboard release.

## Dynamics and exact limits

1200Hz integration: battery internal drop/capacity, series motor field/back EMF,
shaft inertias, inertia screw displacement, inelastic engagement impulse,
starter torque reflected through the reconstructed ratio, overrun from negative
drive reaction, and fuel-cut coastdown. The screw sleeve follows the helix
exactly; relative pinion rotation is taken by the friction stack. Tooth phase is
projected on engagement; tooth collision/contact compliance is not solved.

MZN: lumped motor, gear displacement flow, gallery compliance/leakage and a
system pressure-relief approximation; inactive pump paths do not receive reverse
flow. This does not place an invented relief valve inside the MZN casting.
The MN-1 torque/current curve, oil viscosity/temperature and clearances need
measurement. Flow path geometry through all engine galleries remains incomplete.

Engine firing uses a reduced governor/average torque with a12-cylinder ripple,
requiring starter-driven revolutions and enabled fuel. It does not solve cylinder
thermodynamics, actual injection calibration, cold starting or the pneumatic
backup. The initial bench assumes a warm, fuel-primed engine. None of those
remaining functions have been declared complete.

Slow inspection scales the entire engine/start/pump simulation clock together;
displayed RPM is its simulated physical RPM. Door/suspension clocks remain independent.

1977 original manual p339 specifies an axial rest gap1.5–4.5mm (up to5.2mm
when the flywheel is turned); the1973 edition specifies3–4.5mm. The authored
3.5mm gap satisfies both. Both editions specify a0.5–1.45mm tooth side gap.
Fitted C5 flanks are thinned250micrometres each; nominal total circumferential
backlash is1mm before pressure-angle projection. This is a dimensional fit,
not measured factory involute data. The inertia drive first meshes at the
rest-gap distance, then slides to full overlap before the seated constraint acts.
Root relief is generated by the conjugate gear sweep. Constrained triangulation
preserves the real concave tooth root and annular bores.

## Electric motor photo detail

[MN-1 owner disassembly](https://boatclub.ru/threads/kto-tut-elektrik-u-nas.93/page-8) supports the visible stator detail added in revision4. The four pole shoes are curved meshes with actual radial fastener recesses. Cloth-covered bundles follow the pole cores; a20mm repeatable woven normal map is generated and embedded for both Blender and glTF. This map is a synthetic material, not an altered source photo. No conductor turn count or original brush count is inferred.

The2020 BMP-2 textbook C5-2S full cutaway is retained as a clearly different suffix reference; it has not been used to assert early C5 armature slot or commutator segment counts. Full source evidence and limitations: D:/maz543-references/starting/MOTOR_INTERNAL_REFERENCES.md.

Default manual buttons are momentary. The optional browser auxiliary hold mode is explicitly an accessibility aid, not an original vehicle latching circuit.

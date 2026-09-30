# Circulating water pump — open reconstruction

The primary source is the MAZ-543 1973 operating manual, chapter 007, figure 28:
https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/007.htm
The original scan was obtained and visually inspected on 2026-09-05, at
`work/reference-docs/MAZ1973-F28.jpg`. Its numbered components are:

| Figure | Authored component |
|---|---|
| 1 | Cast housing, centering boss and square mounting flange; two bank outlets |
| 2 | Two ball bearings, separately authored races, cages and balls |
| 3–6 | Retaining ring, bearing spacer, oil thrower and spring washer |
| 7–10 | Drive dog, washer, castellated nut and cotter |
| 11 | Oil-side rubber lip seal |
| 12–13 | Stationary corrugated water seal and axial loading spring |
| 14–15 | Four-tab non-rotating seal washer with rubber buffers |
| 16–17 | Rotating wear sleeve; shaft and riveted six-blade stainless impeller |
| A | Inspection/telltale bore between seal chambers |

The manual identifies the blade count, stainless stamped impeller, two bearings,
four washer tabs, volute, suction bell, drain and exact seal arrangement. It
does not provide the local dimensions used here. The 166 mm impeller diameter,
shaft diameters, ball diameter/count, blade sweep, scroll shape, coupling splines,
thread details, flange holes and all installation coordinates are reconstruction
parameters, not factory measurements or proven production revisions. The source
requires shaft and impeller balancing together; balance has not been certified.

A seller listing explicitly names 1D12A-525A / Сб1211-00-55-01:
https://flagma.ua/nasos-vodyanoy-1d12a-525a-sb1211-00-55-01-o14732500.html
Its downloaded photograph (`work/reference-docs/pump-supplier-525a.jpg`) is only
156 × 117 pixels and shows an assortment of complete pumps. It is a weak external
shape lead, not an accepted photograph of each internal component or a legible
variant marking. Do not claim that every component has individual photo coverage.

Native geometry lives in `scripts/d12-water-detail.py`. The coordinate frame is
coaxial with the lower timing shaft: origin (-0.665,-0.221,0) m, axis (0,-1,0).
The original 27/18 drive gives 1.5 times crank speed. Input and output dogs are
separate meshes parented to their respective shafts. Ball/cage motion assumes
ideal no-slip radial contact with a fixed outer race; load, skidding, bearing
clearance deformation, axial compliance and seal wear are not solved.

The housing and suction bell have actual wet voids and bored connections. Their
near halves can be removed for inspection; the complete assembly retains both
halves. This is a display section, not a claim that the original casting splits
along that plane. The two fixed outer races likewise have display section halves.

The next cooling work must follow figure 27: both cylinder jackets, heads, cooled
exhaust manifolds, three-pass radiator and return to the pump; branches serve the
compressor, heaters and preheater. The original regulates temperature with fan
electromagnetic clutches and manual shutters. Do not insert a generic thermostat.
Two twelve-blade fans and their separate Cardan/gearbox drives remain to be
rebuilt. Pump flow/head/torque, heat exchange, pressure relief and the complete
coolant circuit are not yet accepted.

Rebuild sequence: `node scripts/prepare-d12.mjs`,
`node scripts/prepare-starting.mjs`, Blender `scripts/update-d12-water.py`,
`scripts/verify-water-native.py`, and `scripts/update-starting-assets.py`.
After rebuilding timing mounts, rebuild the water pump before export to restore
its input coupling. `scripts/blender-d12.py` calls both in the correct order.

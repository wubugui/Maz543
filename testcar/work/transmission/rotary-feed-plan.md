# Active implementation plan - source topology, fitted geometry

No vehicle gate is complete. Build/verify direct booster and rotary supply without moving packs or reducing stroke.

- Replace second radial spring anchors with extended guide rods fixed into front case47 web; keep springs and seats at same coordinates. Remove second outer support hoop, which becomes obsolete.
- Body46 rotation = ring18. Sleeve ID .102, OD .105, x -.235 .. -.144; pusher windows x -.180 .. -.171. Direct reaction drum front counterbore to r .099 only x<-.1753.
- Direct pressure flange x=-.186 +/- .0015, ID .0955, OD .1015; 4.5 mm existing stroke. Skirt OD .0985 connects existing pressure plate. Back wall x[-.1925,-.1905], r[.093,.105]. Inner guide OD .095, fixed seal x=-.181. Outer moving seal at flange centre. No interference with second end-seat shoulder ending -.19335.
- Fixed support50 journal x[-.239,-.222], ID .090, OD .1015. Feed seals x=-.233 / -.226, ID .1008, OD .102, axial width .0016 with actual stepped split. Cast ring end gap .00004, step angle .02 rad, middle axial slit .00004.
- Fixed inlet angle pi/8, r .096; axial bore to x=-.2295 then radial into annular feed groove. Body46 radial bore there, axial gallery at r .1035 to x=-.1915, radial down to r .099 then axial outlet through booster back wall.
- Bearing between body46 OD .105 and fixed outer mount: x=-.2195, ball pitch .109, ball radius .0015. Four radial supports outside .113, avoiding reverse gallery at22.5deg. Groove radii reconstructed. 14 balls inferred; cage angular speed .5*(.109-.0015)/.109 * ring18 speed, ball local spin -cage*(.109/.0015+1).
- Source shape/ports/dimensions/casting are not factory CAD. Pressure, leakage, friction dynamics remain OPEN even if this geometry passes.

Check actual native solids, all-angle rotary supply continuity, 5-state body BVH, fixed/moving seals, existing first/2/R ports, pressure contacts and spring roundness. Then install native masters, GLB validator, type/build and actual browser QA.

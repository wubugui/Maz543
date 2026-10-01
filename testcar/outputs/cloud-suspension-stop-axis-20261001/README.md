# Support-bolt adjustment-axis diagnosis

The retained suspension currently cannot satisfy the original installation
instruction by simply turning its existing vertical support bolts upwards at the
three tested settings. No suspension geometry or production asset is modified.
All 16 whole-vehicle acceptance gates remain OPEN.

The original 1977 manual, printed page 320, requires a 136–141 mm vertical
difference between lower-arm head centres for MAZ-543/543A torsion installation,
with support bolts screwed against the upper arms and locked. This is not a
wheel-travel or unladen-height requirement. Fig.98 on printed pp164–165 depicts
the numbered support hardware; the inspected section does not supply its full
3D installation coordinates or calibrated axis angle.

The earlier 25.44 mm AABB separation was only a lower bound between broad geometry
extents. It was never a verified screw-out distance. New actual cap rays at
station 0 find no upper-arm surface within 0.6 m above any of 193 sample points
at each of 136, 138.5 and 141 mm installation settings.

The stronger check projects the **entire evaluated bolt** into the XY plane and
takes its convex hull, which conservatively encloses its footprint. It compares
that hull with every evaluated upper-arm triangle projection, including
degenerate line/point projections. The minimum gaps are:

| Lower-arm vertical difference | Minimum horizontal gap |
|---|---:|
| 136 mm | 4.048765 mm |
| 138.5 mm | 4.032969 mm |
| 141 mm | 4.020214 mm |

The complete eight-station readback returns those gaps at all 24 tested
station/setting combinations. Each retained bolt's principal axis is independently
checked to be vertical. Translating a bolt along that axis leaves its XY
projection unchanged, so it cannot touch the checked upper-arm triangles at
those poses. This is a sufficient geometric condition using floating-point
polygon calculations and a 20 micrometre guard, not formal interval arithmetic.
It does not prove the entire continuous suspension-setting interval, actual
thread travel, other component clearances, strength or factory accuracy.

Seven synthetic polygon controls cover separation, containment, edge crossing,
touching, vertical-face projection, a point projection and collinear separation;
each also checks operand symmetry and a rigid transformation.

The original module SHA remains
`1332163b7c99da0bf3b11d3e9c250b451ceba3430b8935bde919ae4a55b6a51d`.
The current simple shaft/locknut representation and its fitted mounting must be
reviewed against actual support hardware. Neither moving unrelated body geometry
nor silently extending a bolt is a supported correction. The drawing's projected
inclination must not be turned into an invented exact 3D angle.

The two native views isolate the actual retained upper-arm, shaft and nut at the
138.5 mm diagnostic setting. Orange is a temporary inspection material. The first
oblique view has a cropped edge and is retained as a framing failure; the framed
version is the intended delivered oblique view. Source poses are checked after
rendering and no native file is saved. The separate projection chart is a
scientific plot of actual native vertices, not a screenshot or a photograph.

Additional public searches by component description and `543-2901075` did not
yield a qualified original part photograph. Later 2005/2008 catalogue snippets and
unrelated MAZ-truck bolt images are not adopted as 1977 MAZ-543A dimensions.
Previously blocked catalogue routes were not reopened.

Evidence: `axis-probe.json`, `projection-probe.json` (station 0),
`projection-all-stations.json` (all eight stations), native render provenance,
and `projection-plot-provenance.json`. Source: the
[1977 original manual](https://djvu.online/file/zjMdLY3MFjmTL).

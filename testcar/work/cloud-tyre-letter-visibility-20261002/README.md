# Native tyre lettering visibility readout

One read-only official Blender 4.5.13 process finished in 18.854556 seconds, exit 0, CPU1. It opened the unchanged 8e962d6 Master at frame 0 and queried the original geometry. No Apply, wheel rotation, rendering, model save or promotion occurred. All 16 whole-vehicle gates remain OPEN.

The 65 original text records are preserved byte-for-byte using readable source/log files and five ordinary JSON value/reference table shards. The original FREEZE-MANIFEST.json is also preserved separately. No binary assets, private delivery destinations or receipts are included.

## Findings and limits

- All 18 actual MESH glyphs have camera/display flags enabled. Their SOURCE FONT objects remain hidden authoring references. Solidify is enabled in both viewport and render, thickness 0.0008500000112690032 m, offset 1.
- The 37 visibility records cover 18 glyphs, 18 source fonts and the tyre. The 36 geometry files separately record original-object and VIEWPORT evaluated queries; the hidden FONT solids are not interchangeable with the rendered glyphs.
- Actual evaluated glyph boxes measure 4.0567–11.7486 pixels wide and 2.93594–12.69610 pixels high in the existing 1100×1000 view. The authored 40 mm FONT size is an em parameter, not measured character height. The actual tyre projection agrees with the saved native-camera reference to 0.000154484 pixels, below the explicit 0.001 pixel formula-consistency gate.
- For 2592 evaluated glyph vertices, signed nearest-tyre distances span −0.050204 to +0.813057 mm. For 5140 triangle centroids, the range is −0.050206 to +0.807023 mm. All queried nearest tyre normals already point toward +Y; original winding signs are retained. Base/back surfaces are included, so these ranges are not a whole-glyph visibility or containment certificate.
- Eight of nine finite VIEWPORT rays first hit their target glyph. One sample on glyph_19, triangle 126, first hits cab_0062, 45.317778 mm before the glyph sample. This is local geometric obstruction at that point, not evidence that the entire glyph or all lettering is hidden. The rays do not certify Cycles visibility, transparency, shader displacement or readable pixels.
- All 10434 original object matrices and identities remain unchanged, with maximum matrix-element difference 0. Selected flags/modifier fields, source SHA and camera-record SHA remain unchanged.

The two existing images still do not show clearly readable lettering. This readout rules out universal disabled flags and complete burial/occlusion for the sampled exposed points; it does not isolate the rendering cause. Lighting, resolution, contrast, denoising and render-depsgraph effects remain unisolated. Typography, dimensions and historical fit remain authored reconstruction values, not factory certification. The 40 radial vent rods are separate geometry and are not the 18 glyph legend.

## Exact restoration

Run in a separate process with a destination that does not exist:

    python -B restore-records.py --package . --out /tmp/maz-letter-probe-restored-UNUSED

The restored tree contains all 65 original records plus the exact original freeze manifest. Every original path, byte count and SHA is checked before any files are written. Python sources remain directly readable under `raw/`. JSON records are structured only where indent 2 / ASCII-escaped JSON plus LF reproduces the exact bytes; other text remains direct. The existing pinned codec SHA is 2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d. No compression/binary-string encoding or image payload is used.

SUMMARY.json is restored with the source records and separates raw/evaluated, vertex/centroid and finite-ray conclusions. Original script, runner, argv, native preflight, all per-object/ray files and final source/matrix protection remain available; package-index.json maps every record to its storage.

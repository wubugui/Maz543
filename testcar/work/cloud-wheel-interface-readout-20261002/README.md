# Native front-wheel interfaces and fixed-link reachability

This read-only checkpoint does not repair the known nominal camber defect and does not select an alignment pose. The actual VA180 Master was read with official Blender 4.5.13 LTS/build daeeeca98fb0, one CPU, script auto-execution disabled, and a 120-second process limit. The complete marker/report and exit 0 confirm this run; its original runner did not set --python-exit-code and is retained exactly. Future runners must add it.

The four real native sets reproduce the fixed-link analytic obstruction: for positive wheel-plane camber (upper edge outward) of one degree, the two closure circles miss internally by 2.4437733–2.4437736 mm. The reachable negative-one-degree nearest branch shifts the wheel centre down about71.59 mm and places its upper arm at about−14.645 degrees. Neither is an accepted static setting. The unmodified published specification, with its upper arm exactly horizontal, gives only +0.2477269-degree camber; no tolerance for “near horizontal” is inferred.

The probe confirms separately animated wheel carriers, suspension supports, brakes and shaft groups. Native outer Cardan flange and wheel axes differ by about6.207 degrees. The original source distinguishes that Cardan, the supported outer halfshaft and the CV inside the knuckle, so this angle alone does not prove which interface should be replaced or reoriented. The proposed mechanical correction remains subject to strict dependency and interface qualification.

Each drum candidate is a retained 148-vertex cylinder with 670 mm radial bounding diameter and130 mm axial width. Its vertex mean is biased by mesh sampling; using that mean as the cylindrical axis centre would be wrong. The native circular-axis fit and source-matched drum/spin attachment belong to the next candidate, not this checkpoint.

72 direct SHRINKWRAP target observations stay within the wheel scopes. These are observations, not permission to whitelist dependencies or a complete Blender dependency proof.

`interfaces-table/` stores the full ordinary JSON report as four readable JSON
value/reference tables, totalling379766 bytes. It contains no model or image
asset and no compressed/binary text payload. Run:

```
python pack-wheel-interface-evidence.py restore --input interfaces-table --out /an/unused/path/interfaces.json
```

The table manifest and decoder verify each shard and recover the exact original
2410990 bytes, SHAfea41bf0e145d707cc8f21089c7a20320c60de236b94c8285230fc40a225477a.
The parent restored these independently in a separate process and compared the
bytes with the real native output. `source-files.json` identifies unchanged
execution/report inputs; only this publication paragraph was edited. The two
ordinary-JSON packing tools in the initial transfer package are not the
publication format and are superseded by this readable table codec.


No native source was changed. No blend/GLB was saved or exported. The next replay script is outside this package and has never run. All16 whole-vehicle gates remain OPEN.

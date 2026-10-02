# Replay contract

Use the exact66,069,335-byte VA180 Master with SHA-2568e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70 and official Blender4.5.13/build daeeeca98fb0. The source repository must contain the pinned dependency guard and lib/maz543.ts checked by executed-script.py.

The runner preserves the exact command used and the single-CPU/120second bound. For another workspace, invoke executed-script.py with explicit --base, --sha, --repository and --output paths after the Blender -- delimiter, retaining --background --factory-startup --disable-autoexec --threads1 --python-exit-code1. Use the standard spaced CLI option forms shown in launch.json; the output directory is for ordinary JSON only. No model save/export call is present.

Only frozen native frame0 and the two documented spin samples are checked. The output is an in-memory candidate plus evidence, not a saved replacement Master. To inspect it interactively later, replay the same source/operations in a separate authorized session; that inspection and any save/export require their own completed workflow.

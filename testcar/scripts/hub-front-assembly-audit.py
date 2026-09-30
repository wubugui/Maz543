import bpy,json,os
from pathlib import Path
OUT=Path(os.environ['HUB_OUTPUT_DIR'])
report={}
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()))
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    rows=[]
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        ps=[o.matrix_world@v.co for v in o.data.vertices]
        if not ps:continue
        lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)]
        b={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]}
        if filename.endswith('Master.blend') or b['min'][0]<-3.0:
            rows.append({'name':o.name,'parent':o.parent.name if o.parent else None,'vertices':len(ps),'bounds':b,'materials':[m.name if m else None for m in o.data.materials]})
    report[filename]=rows
(OUT/'front-assembly-audit.json').write_text(json.dumps(report,indent=2))

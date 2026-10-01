"""Read-only inputs for transporting the current cab candidate to the textured sibling."""
import bpy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/cloud-va180-web-20261001';OUT.mkdir(parents=True,exist_ok=True)
sources=[('textured_baseline',ROOT/'outputs/cloud-left-driver-side-20261001/MAZ543A_Textured.blend','171e7696421227fca28b8be3c555065381cbc6ca2a4b43ca94d18b83b5a167c7'),
         ('current_master',ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend','8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70')]
report={}
for label,path,expected in sources:
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    records={}
    for name in ['cab','cab_0064','cab_0066','cab_0067','cab_0068','cab_pivot_004','cab_0029','cab_0030','cab_0031','BL_Left_driver_steering_column_retained']:
        o=bpy.data.objects.get(name)
        if o is None:records[name]=None;continue
        records[name]={'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,
                       'faces':len(o.data.polygons) if o.type=='MESH' else None,
                       'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],
                       'world':[list(r) for r in o.matrix_world],'hide_render':o.hide_render,
                       'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection]}
    modules={}
    for name in ['LEFT DISPLAY ROOT — not vehicle datum','RIGHT DISPLAY ROOT — not vehicle datum']:
        root=bpy.data.objects.get(name)
        if root:
            module=[root]+list(root.children_recursive)
            modules[name]={'objects':[o.name for o in module],'collections':sorted({c.name for o in module for c in o.users_collection}),'world':[list(r) for r in root.matrix_world]}
    report[label]={'source_sha256':expected,'object_count':len(bpy.data.objects),'mesh_count':sum(o.type=='MESH' for o in bpy.data.objects),'selected_objects':records,'modules':modules}
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
(OUT/'input-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('TEXTURED_CAB_INPUTS',json.dumps({k:{'objects':v['object_count'],'cab_0064':v['selected_objects']['cab_0064'],'module_counts':{n:len(m['objects']) for n,m in v['modules'].items()}} for k,v in report.items()}))

import bpy,json,hashlib,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
results=[]
for filename in ['MAZ543A_Transmission.blend','MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/filename))
    root=bpy.data.objects['S543_TRANSMISSION'];objects=[root]+list(root.children_recursive)
    h=hashlib.sha256()
    for o in sorted(objects,key=lambda x:x.name):
        h.update(o.name.encode());h.update(o.type.encode())
        if o.type=='MESH':
            for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
            for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
            if o.data.shape_keys:
                for key in o.data.shape_keys.key_blocks:
                    h.update(key.name.encode())
                    for v in key.data:h.update(struct.pack('<3f',*v.co))
                if filename!='MAZ543A_Transmission.blend':
                    assert not (o.data.shape_keys.animation_data and o.data.shape_keys.animation_data.action)
                    assert all(key.value==0 for key in o.data.shape_keys.key_blocks)
    if filename!='MAZ543A_Transmission.blend':
        assert root.parent.name=='drive'
        for name in ['drive_0002','drive_pivot_002','drive_pivot_007','drive_pivot_012']:assert name not in bpy.data.objects
        assert not any(o.animation_data and o.animation_data.action for o in objects),'do not impose the independent inspection timeline on the vehicle'
    results.append({'file':filename,'nodes':len(objects),'geometrySha256':h.hexdigest()})
assert len({r['geometrySha256'] for r in results})==1
(ROOT/'outputs/transmission-asset-parity.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))

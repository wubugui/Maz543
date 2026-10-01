"""Read original connected components before planning selective panel replacement."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-left-driver-side-20261001/MAZ543A_Master.blend'
OUT=ROOT/'outputs/cloud-left-driver-rest-audit-20261001/component-inventory.json'
assert not OUT.exists()
h=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
records=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith('cab_'):continue
    m=o.data;parent=list(range(len(m.vertices)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for e in m.edges:
        a,b=(root(i) for i in e.vertices);parent[a]=b
    groups={}
    for v in m.vertices:groups.setdefault(root(v.index),[]).append(v.index)
    for ids in groups.values():
        p=[o.matrix_world@m.vertices[i].co for i in ids]
        lo=[min(v[k] for v in p) for k in range(3)];hi=[max(v[k] for v in p) for k in range(3)]
        if hi[0]<-5.4 or lo[0]>-3.9 or hi[2]<1.4 or lo[2]>2.5:continue
        records.append({'object':o.name,'first_vertex':min(ids),'vertices':len(ids),'bounds':[lo,hi],'materials':[s.material.name if s.material else None for s in o.material_slots],'parent':o.parent.name if o.parent else None})
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==h
OUT.write_text(json.dumps({'source_sha256':h,'raw_connected_components':records,'limits':'Raw authored connectivity only. Coincident split vertices/UV seams may split triangles/caps; not a physical-part count, evaluated geometry or semantic certification.'},indent=2)+'\n')
print('CAB_COMPONENTS',len(records),flush=True)

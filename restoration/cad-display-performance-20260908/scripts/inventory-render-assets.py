"""Read GLB accessor counts without decoding or modifying the shipped geometry."""
from pathlib import Path
import struct,json
ROOT=Path(__file__).resolve().parents[1]
names=['maz543a-blender','d12a525a-engine','maz543a-suspension','maz543a-starting','maz543a-cooling','maz543a-cardan','maz543a-transmission']
assets=[]
for name in names:
    path=ROOT/'public/models'/f'{name}.glb';b=path.read_bytes();length,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a;d=json.loads(b[20:20+length])
    rows=[]
    for node in d.get('nodes',[]):
        if 'mesh' not in node:continue
        mesh=d['meshes'][node['mesh']];triangles=0;vertices=0
        for p in mesh['primitives']:
            vertices+=d['accessors'][p['attributes']['POSITION']]['count']
            if p.get('mode',4)==4:triangles+=d['accessors'][p['indices']]['count']//3 if 'indices' in p else d['accessors'][p['attributes']['POSITION']]['count']//3
        rows.append({'node':node.get('name'),'mesh':node['mesh'],'triangles':triangles,'vertices':vertices})
    assets.append({'name':name,'bytes':len(b),'meshNodes':len(rows),'uniqueMeshes':len(d['meshes']),'instanceTriangles':sum(r['triangles'] for r in rows),'topMeshes':sorted(rows,key=lambda r:r['triangles'],reverse=True)[:20]})
report={'assets':assets,'limits':'Counts before runtime removal, visibility and render passes. Shared meshes count once per scene node; no detail was removed.'}
(ROOT/'outputs/render-asset-inventory.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps([{k:v for k,v in a.items() if k!='topMeshes'} for a in assets],indent=2))

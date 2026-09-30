"""Verify shared catalogue geometry in the saved native file, not just labels.
Plate placement is removed; opposite-facing large pistons are compared in their
own actuation direction. 0.1 micrometre quantization only absorbs native floats.
"""
import bpy,json,sys,hashlib
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];temporary='--geometry-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('work/transmission/rotary-geometry.blend' if temporary else 'outputs/MAZ543A_Transmission.blend')))
D=json.loads((ROOT/'work/transmission/poses.json').read_text());bpy.context.scene.frame_set(0)
groups=defaultdict(list)
def canonical(ob,vertices):
    if 'annular_piston' in ob.name:
        pack=D['clutches']['first' if '_first_' in ob.name else 'reverse'];direction=pack['direction'];origin=pack['start']-direction*.005
    else:direction=1;origin=(min(v.co.x for v in vertices)+max(v.co.x for v in vertices))/2
    points=[tuple(round(v*1e7) for v in ((p.co.x-origin)*direction,p.co.y,p.co.z)) for p in vertices]
    faces=sorted(tuple(sorted(points[i] for i in face.vertices)) for face in ob.data.polygons)
    return hashlib.sha256(repr((sorted(points),faces)).encode()).hexdigest()
for ob in bpy.data.objects:
    part=ob.get('cataloguePart')
    if not part:continue
    assert ob.type=='MESH' and max(abs(x-1) for x in ob.scale)<1e-8,ob.name
    signatures={'Basis':canonical(ob,ob.data.vertices)}
    if ob.data.shape_keys:
        signatures.update({key.name:canonical(ob,key.data) for key in ob.data.shape_keys.key_blocks})
    groups[part].append({'name':ob.name,'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'signatures':signatures})
expected={'535A-1511232':16,'535A-1511236':14,'535A-1511044':11,'535A-1511046':9,'535A-1511246':60,'535A-1511058':16,'535A-1511264':16,'535A-1511244-01':60,'535A-1511248-10':60,'535A-1511252':120,'535A-1511254':60,'535A-1511180-A':2}
assert set(groups)==set(expected),(set(groups),set(expected))
for part,count in expected.items():
    entries=groups[part];assert len(entries)==count,(part,len(entries),count)
    assert len({json.dumps(e['signatures'],sort_keys=True) for e in entries})==1,(part,entries)
report={'groups':dict(groups),'sharedInstances':sum(expected.values()),'catalogueGroups':len(expected),
        'limits':'Shared shapes, morph targets and no object scaling verified at 0.1 micrometre coordinate quantization. Dimensions remain fitted, not factory metrology.'}
out=ROOT/('work/transmission/shared-clutch-parts-checks.json' if temporary else 'outputs/shared-clutch-parts-checks.json')
out.write_text(json.dumps(report,indent=2));print(json.dumps({'sharedInstances':report['sharedInstances'],'groups':{k:len(v) for k,v in groups.items()}},indent=2),flush=True)

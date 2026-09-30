"""Verify saved cooling surfaces, morph bases and provenance in all native files."""
import bpy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
expected={row['name'] for row in json.loads((ROOT/'outputs/cooling-reference-register.json').read_text())}
baseline=None;reports=[]
for filename in ['MAZ543A_Cooling_Master.blend','MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/filename));bpy.context.scene.frame_set(0)
    parts=sorted((o for o in bpy.data.objects['S543_COOLING'].children_recursive if o.type in ['MESH','CURVE']),key=lambda o:o.name)
    assert {o.name for o in parts}==expected
    rows=[];morphs=0
    for ob in parts:
        assert ob.get('sourceSupports') and ob.get('individualPhotoStatus')
        geom=[list(v.co) for v in ob.data.vertices] if ob.type=='MESH' else [[list(p.co) for p in s.points] for s in ob.data.splines]
        topology=[list(p.vertices) for p in ob.data.polygons] if ob.type=='MESH' else []
        keys=[]
        if ob.type=='MESH' and ob.data.shape_keys:
            keys=[[k.name,[list(v.co) for v in k.data]] for k in ob.data.shape_keys.key_blocks];morphs+=1
        rows.append([ob.name,ob.parent.name,ob.type,geom,topology,keys,ob.get('sourceSupports'),ob.get('referenceURLs')])
    assert morphs==2
    digest=hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    if baseline is None:baseline=digest
    assert digest==baseline,(filename,'Cooling native surfaces or morph bases differ')
    missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and im.filepath and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
    assert not missing,(filename,missing)
    reports.append(dict(file=filename,parts=len(parts),parametricSpringMeshes=morphs,geometryTopologyMorphProvenanceSha256=digest,missingUnpackedImages=missing))
report={'assemblies':reports,'passed':True,'scope':'Saved cooling mesh/curve points, mesh faces, morph bases and source provenance parity. Animation checks are separate; no factory dimensional acceptance.'}
(ROOT/'outputs/cooling-asset-parity.json').write_text(json.dumps(report,indent=2))
print('COOLING_ASSET_PARITY',json.dumps(report),flush=True)

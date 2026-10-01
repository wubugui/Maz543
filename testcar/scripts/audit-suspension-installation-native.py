"""Read-only installation-datum diagnosis on the retained native suspension.

Transforms are applied in memory to the actual existing rig. Only rigid joint
datums and upper-arm/stop bounds are checked; torsion strain, preload and whole
assembly geometry are not validated or saved at these diagnostic poses.
"""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-suspension-installation-20261001'
mapping=json.loads((OUT/'reference-mapping.json').read_text())
SOURCE=ROOT/'outputs/MAZ543A_Suspension_Master.blend'
expected='1332163b7c99da0bf3b11d3e9c250b451ceba3430b8935bde919ae4a55b6a51d'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==expected
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
def C(p):return Vector((p[0],-p[2],p[1]))
def descendants(o):
    for child in o.children:
        yield child
        yield from descendants(child)
def vertices(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    pts=[ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear()
    assert pts,o.name
    return pts
def bounds(pts):return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}
rows=[]
for measurement in mapping['measurements']:
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    for name,pose in measurement['pose'].items():
        assert name in bpy.data.objects,name
        o=bpy.data.objects[name];o.location=C(pose['p']);o.rotation_euler.x=pose['rx']
    bpy.context.view_layer.update()
    for i in range(8):
        name=f'S543_{i}';lower=bpy.data.objects[name+'_lower'];upright=bpy.data.objects[name+'_upright'];upper=bpy.data.objects[name+'_upper']
        dg=bpy.context.evaluated_depsgraph_get()
        inner=lower.evaluated_get(dg).matrix_world.translation;outer=upright.evaluated_get(dg).matrix_world.translation
        achieved=inner.z-outer.z;target=measurement['requestedVerticalDropM']
        assert abs(achieved-target)<2e-6,(name,achieved,target)
        parts=[o for o in descendants(upper) if o.type in {'MESH','CURVE'}]
        assert parts,name
        up=bounds([p for o in parts for p in vertices(o)])
        bolt=bpy.data.objects[name+'_droop_limit_bolt'];bb=bounds(vertices(bolt))
        gaps=[max(up['min'][k]-bb['max'][k],bb['min'][k]-up['max'][k]) for k in range(3)]
        gap=max(gaps)
        rows.append({'station':i,'requestedVerticalDropM':target,'actualRigHeadDatumDropM':achieved,'datumErrorM':achieved-target,
                     'lowerHeadDatumWorldXYZ':list(inner),'outerHeadDatumWorldXYZ':list(outer),
                     'upperArmGeometryParts':[o.name for o in parts],'upperArmBounds':up,'droopBolt':bolt.name,'droopBoltBounds':bb,
                     'aabbSeparationLowerBoundM':gap,'separationAxis':gaps.index(gap),
                     'stopContactStatus':'PROVABLY_NOT_IN_CONTACT_AT_THIS_DIAGNOSTIC_POSE' if gap>2e-5 else 'BOUNDS_OVERLAP_CONTACT_UNRESOLVED'})
report={'status':'REFERENCE_DATUM_DIAGNOSIS_NOT_ASSEMBLY_ACCEPTANCE','source_file':SOURCE.name,'source_sha256':expected,
        'input_mapping':'reference-mapping.json','rows':rows,
        'scope':'Actual retained rig joint origins; actual evaluated upper-arm descendants versus actual retained droop limit bolt. Does not establish casting-hole center measurement, torsion strain/preload, proper stop adjustment, static equilibrium, continuous clearance or entire module acceptance.',
        'condition':'Original p320 calls for the support bolts to touch the upper arms during the torsion-installation setting. Existing stop geometry has not been adjusted in this diagnosis.',
        'source_sha256_after':sha(SOURCE),'saved_blend':False,'wholeVehicleAcceptance':'16 OPEN'}
assert report['source_sha256_after']==expected
(OUT/'native-datum-and-stop-report.json').write_text(json.dumps(report,indent=2))
print('NATIVE_INSTALLATION_DIAGNOSIS',json.dumps({'states':len(rows),'maxDatumErrorM':max(abs(x['datumErrorM']) for x in rows),'noncontactStates':sum(x['stopContactStatus'].startswith('PROVABLY') for x in rows),'minimumSeparationLowerBoundM':min(x['aabbSeparationLowerBoundM'] for x in rows)}))

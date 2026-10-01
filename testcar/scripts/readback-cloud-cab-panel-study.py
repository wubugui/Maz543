"""Fresh native readback of the isolated cab panel study; does not render."""
import bpy, bmesh, json, math, sys, argparse, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--input',type=Path,default=ROOT/'testcar/outputs/cloud-cab-panel-study-20261001/study.blend')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
path=a.input.resolve(); out=path.parent
bpy.ops.wm.open_mainfile(filepath=str(path))
manifest=json.loads((out/'build-manifest.json').read_text())
registry=json.loads((out/'source-registry.json').read_text())
dg=bpy.context.evaluated_depsgraph_get()
failures=[]; rows=[]; bvhs={}
for name in manifest['claimed_closed_solids']:
    o=bpy.data.objects.get(name)
    if o is None:
        failures.append({'object':name,'failure':'missing'});continue
    ev=o.evaluated_get(dg); me=ev.to_mesh()
    bm=bmesh.new();bm.from_mesh(me)
    finite=all(math.isfinite(c) for v in me.vertices for c in v.co)
    boundary=sum(e.is_boundary for e in bm.edges)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    loose=sum(e.is_wire for e in bm.edges)
    volume=bm.calc_volume(signed=True)
    row={'name':name,'vertices':len(me.vertices),'edges':len(me.edges),'faces':len(me.polygons),
         'finite':finite,'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'wire_edges':loose,
         'signed_volume_m3':volume,'euler_characteristic':len(me.vertices)-len(me.edges)+len(me.polygons),
         'native_modifiers':[m.type for m in o.modifiers]}
    remaining=set(bm.verts);components=0
    while remaining:
        components+=1; queue=[remaining.pop()]
        while queue:
            v=queue.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in remaining:
                    remaining.remove(other);queue.append(other)
    row['connected_components']=components
    row['closed_finite_positive_volume']=finite and len(me.polygons)>0 and nonmanifold==0 and volume>0
    if not row['closed_finite_positive_volume']:failures.append({'object':name,'failure':'closed finite positive-volume assertion','detail':row})
    rows.append(row)
    if name in manifest['panel_objects']+manifest['auxiliary_plate_objects']:
        bvhs[name]=BVHTree.FromBMesh(bm)
    bm.free();ev.to_mesh_clear()

# Through-hole checks inspect evaluated plate geometry only, with actual Boolean
# modifiers on. Separate proxy bodies are not counted as obstructing the plate.
hole_results=[]
for h in manifest['through_holes']:
    o=bpy.data.objects[h['plate']]; bvh=bvhs[h['plate']]
    x,y=h['center_local_m'];r=h['radius_m']
    # Auxiliary strip's base object has a local +Z display offset; its XY matches.
    rays=[]
    samples=[(0,0)]+[(math.cos(t*math.pi/4)*r*.68,math.sin(t*math.pi/4)*r*.68) for t in range(8)]
    for dx,dy in samples:
        hit=bvh.ray_cast(Vector((x+dx,y+dy,.1)),Vector((0,0,-1)),.2)[0]
        rays.append(hit is None)
    row={'id':h['id'],'plate':h['plate'],'test':'9 normal rays through source-fitted opening, plate only','all_rays_open':all(rays),'rays_open':sum(rays)}
    hole_results.append(row)
    if not all(rays):failures.append({'object':h['plate'],'failure':'blocked claimed through-hole','detail':row})

# Positive controls catch empty/evaluated-away plates instead of treating empty
# meshes as proof of successful holes. Locations lie inside visible source webs.
LS=.88/(1148-282);RS=.335/(632-261)
webs=[(manifest['panel_objects'][0],(310-715)*LS,(1183-1045)*LS),
      (manifest['panel_objects'][0],(1040-715)*LS,(1183-1338)*LS),
      (manifest['panel_objects'][1],(280-447)*RS,(344-175)*RS)]
web_results=[]
for name,x,y in webs:
    hit=bvhs[name].ray_cast(Vector((x,y,.1)),Vector((0,0,-1)),.2)[0]
    web_results.append({'plate':name,'local_xy':[x,y],'material_hit':hit is not None})
    if hit is None:failures.append({'object':name,'failure':'positive web-control ray missed'})

# A Boolean-disabled negative control must block at least the 14 main openings.
negative=[]
left=bpy.data.objects[manifest['panel_objects'][0]]
booleans=[m for m in left.modifiers if m.type=='BOOLEAN']
for m in booleans:m.show_viewport=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
ev=left.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bv=BVHTree.FromBMesh(bm)
for instrument in registry['physical_instruments']:
    x,y=instrument['center_local_m']
    hit=bv.ray_cast(Vector((x,y,.1)),Vector((0,0,-1)),.2)[0]
    negative.append({'slot':instrument['slot_id'],'blocked_when_boolean_disabled':hit is not None})
bm.free();ev.to_mesh_clear()
for m in booleans:m.show_viewport=True
if not all(x['blocked_when_boolean_disabled'] for x in negative):failures.append({'failure':'Boolean-disabled negative control did not block every instrument hole'})

# These silhouette diagnostics are independent of the opening centre tests.
# A U notch must be empty while its lower connecting web is present, and the
# asymmetric right extension must exist below the diagonal but not above it.
silhouette=[]
for key,px,py,expected in [('U notch interior',697,1043,False),('web below U notch',697,1116,True),
                           ('right extension interior',1100,1334,True),('outside right diagonal',1100,1210,False)]:
    x=(px-715)*LS;y=(1183-py)*LS
    hit=bvhs[manifest['panel_objects'][0]].ray_cast(Vector((x,y,.1)),Vector((0,0,-1)),.2)[0]
    actual=hit is not None
    silhouette.append({'test':key,'expected_plate_material':expected,'actual_plate_material':actual,'pass':actual==expected})
    if actual!=expected:failures.append({'failure':'left fitted source silhouette control','test':key})

panel_topology=[]
for name in manifest['panel_objects']+manifest['auxiliary_plate_objects']:
    hcount=sum(h['plate']==name for h in manifest['through_holes'])
    row=next(r for r in rows if r['name']==name)
    expected=2-2*hcount
    passed=row['euler_characteristic']==expected and row['connected_components']==1
    panel_topology.append({'plate':name,'declared_through_holes':hcount,'expected_euler':expected,
                           'actual_euler':row['euler_characteristic'],'connected_components':row['connected_components'],'pass':passed})
    if not passed:failures.append({'failure':'plate connectedness/Euler hole-count consistency','plate':name})

image_files=[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE' or im.packed_file]
if image_files:failures.append({'failure':'unexpected file-backed or packed image','detail':image_files})
if len(manifest['instrument_roots'])!=14:failures.append({'failure':'left instrument count is not14'})
if len(registry['conflicts'])!=4:failures.append({'failure':'four caption/drawing conflicts not retained'})
report={'blender':bpy.app.version_string,'build_hash':bpy.app.build_hash.decode(),
        'fresh_open':str(path.relative_to(ROOT)),'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'status':'PASS — scoped native structure only' if not failures else 'FAIL',
        'production_opened_or_modified':False,'rendered':False,'all_16_whole_vehicle_gates':'OPEN',
        'counts':{'objects':len(bpy.data.objects),'claimed_closed_solids':len(rows),'closed_finite_positive_volume':sum(r['closed_finite_positive_volume'] for r in rows),
        'left_major_instruments':len(manifest['instrument_roots']),'through_holes':len(hole_results),'open_through_holes':sum(h['all_rays_open'] for h in hole_results),
        'right_physical_positions':manifest['right_physical_control_lamp_count'],'source_curves':len(manifest['source_curves']),
        'file_or_packed_images':len(image_files)},
        'solids':rows,'through_holes':hole_results,'positive_web_controls':web_results,
        'source_silhouette_controls':silhouette,'panel_hole_topology':panel_topology,
        'boolean_disabled_negative_controls':negative,'failures':failures,
        'limits':['No factory dimension claim','No vehicle installation or clearance test','No internal-mechanism or electrical-function validation',
                  'No calibration or original factory face printing','No visual render/acceptance in this readback','Closed topology is not physical authenticity'],
        'unresolved_caption_mapping':registry['conflicts']}
(out/'native-readback.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('CAB_PANEL_READBACK',json.dumps({'status':report['status'],'counts':report['counts'],'failures':failures}))
if failures:raise SystemExit(1)

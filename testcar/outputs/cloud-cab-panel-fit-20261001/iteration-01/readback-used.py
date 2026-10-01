"""Fresh readback of fitted panels: topology, holes, retained proxies, rest contacts."""
import argparse,bpy,bmesh,hashlib,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--input',required=True)
a=p.parse_args(__import__('sys').argv[__import__('sys').argv.index('--')+1:])
path=Path(a.input).resolve();build=json.loads(path.with_suffix('.build.json').read_text())
assert hashlib.sha256(path.read_bytes()).hexdigest()==build['candidate_sha256']
manifest=json.loads((ROOT/'outputs/cloud-cab-panel-study-20261001/build-manifest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();solids={};local_bvh={};rows=[];fail=[]
def bounds(vs):return [[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]
def near(a,b):return all(a[k][0]<=b[k][1] and b[k][0]<=a[k][1] for k in range(3))
def mesh(o):
 e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles()
 return e,m
for name in manifest['claimed_closed_solids']:
 o=bpy.data.objects[name];e,m=mesh(o);bm=bmesh.new();bm.from_mesh(m)
 volume=bm.calc_volume(signed=True);closed=all(ed.is_manifold for ed in bm.edges)
 finite=all(math.isfinite(c) for v in m.vertices for c in v.co)
 if not(closed and finite and volume>0):fail.append({'object':name,'failure':'closed finite positive volume'})
 if name in manifest['panel_objects']+manifest['auxiliary_plate_objects']:
  n=sum(x['plate']==name for x in manifest['through_holes']);euler=len(bm.verts)-len(bm.edges)+len(bm.faces)
  if euler!=2-2*n:fail.append({'object':name,'failure':'Euler hole count','actual':euler})
  local_bvh[name]=BVHTree.FromBMesh(bm)
 vs=[e.matrix_world@v.co for v in m.vertices];tri=[tuple(t.vertices) for t in m.loop_triangles]
 solids[name]=(BVHTree.FromPolygons(vs,tri,all_triangles=True),bounds(vs))
 rows.append({'name':name,'vertices':len(m.vertices),'triangles':len(tri),'closed':closed,'finite':finite,'signed_volume':volume})
 bm.free();e.to_mesh_clear()
holes=[]
for h in manifest['through_holes']:
 x,y=h['center_local_m'];r=h['radius_m'];bvh=local_bvh[h['plate']]
 positions=[(0,0)]+[(math.cos(i*math.pi/4)*r*.68,math.sin(i*math.pi/4)*r*.68) for i in range(8)]
 clear=all(bvh.ray_cast(Vector((x+dx,y+dy,.1)),Vector((0,0,-1)),.2)[0] is None for dx,dy in positions)
 holes.append({'id':h['id'],'nine_plate_rays_open':clear})
 if not clear:fail.append({'opening':h['id'],'failure':'blocked plate rays'})
hidden=[]
for name in build['archived_originals']:
 o=bpy.data.objects[name];hidden.append({'name':name,'exists':True,'hide_render':o.hide_render})
 if not o.hide_render:fail.append({'object':name,'failure':'superseded proxy still rendered'})
all_imported=set()
for name in ['LEFT DISPLAY ROOT — not vehicle datum','RIGHT DISPLAY ROOT — not vehicle datum']:
 root=bpy.data.objects[name];all_imported.add(root.name);all_imported.update(x.name for x in root.children_recursive)
overlaps=[];pairs=0;fixed_count=0
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.hide_render or o.name in all_imported:continue
 e=o.evaluated_get(dg);box=bounds([e.matrix_world@Vector(v) for v in e.bound_box]);candidates=[name for name,(_,b) in solids.items() if near(box,b)]
 if not candidates:continue
 fixed_count+=1;e,m=mesh(o);vs=[e.matrix_world@v.co for v in m.vertices];tri=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
 if not vs or not tri:continue
 fixed=BVHTree.FromPolygons(vs,tri,all_triangles=True)
 for name in candidates:
  pairs+=1;hits=solids[name][0].overlap(fixed)
  if hits:overlaps.append({'panel_part':name,'existing_part':o.name,'triangle_pairs':len(hits),'sample_pairs':hits[:5]})
assert hashlib.sha256(path.read_bytes()).hexdigest()==build['candidate_sha256']
r={'candidate_sha256':build['candidate_sha256'],'fresh_open':True,'native_structure_failures':fail,'new_solids':rows,'plate_holes':holes,'retained_superseded_proxies':hidden,'panel_to_existing_object_flag_visible_rest_surface_pairs_checked':pairs,'fixed_objects_in_narrow_phase':fixed_count,'panel_to_existing_rest_surface_intersections':overlaps,'status':'STRUCTURE_FAIL' if fail else ('REST_SURFACE_INTERFERENCE_OPEN' if overlaps else 'SCOPED_STRUCTURE_PASS_REST_SURFACE_TEST_NO_HITS'),'limits':['Fitted placement and dimensions, no source hardpoint calibration','No full-containment or continuous swept-volume test','Old steering/seat interference remains unresolved','Not full visual or vehicle acceptance'],'all16VehicleGates':'OPEN'}
path.with_suffix('.readback.json').write_text(json.dumps(r,indent=2)+'\n')
print('PANEL_FIT_READBACK',len(rows),len(holes),'structure_failures',len(fail),'rest_surface_interference_pairs',len(overlaps),flush=True)
if fail:raise SystemExit(1)

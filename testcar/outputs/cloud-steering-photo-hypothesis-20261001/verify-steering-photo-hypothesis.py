"""Fresh saved-file check of the independent steering pose hypothesis."""
import bpy,json,hashlib,argparse,sys,numpy as np,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--input',required=True,type=Path)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);path=args.input.resolve();out=path.with_suffix('.readback.json');assert not out.exists()
record=json.loads(path.with_suffix('.build.json').read_text());sha=hashlib.sha256(path.read_bytes()).hexdigest();assert sha==record['candidate_sha256']
bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();fail=[]
def authored(o):
 h=hashlib.sha256();m=o.data
 for seq,prop,n,dtype in [(m.vertices,'co',3,np.float32),(m.loops,'vertex_index',1,np.int32),(m.polygons,'loop_start',1,np.int32),(m.polygons,'loop_total',1,np.int32),(m.polygons,'material_index',1,np.int32)]:
  a=np.empty(len(seq)*n,dtype=dtype);seq.foreach_get(prop,a);h.update(a.tobytes())
 for uv in m.uv_layers:
  h.update(uv.name.encode());a=np.empty(len(uv.uv)*2,dtype=np.float32);uv.uv.foreach_get('vector',a);h.update(a.tobytes())
 return h.hexdigest()
assert set(record['objects'])==set(bpy.data.objects.keys())
max_matrix_error=0
for name,s in record['objects'].items():
 o=bpy.data.objects[name];now={'type':o.type,'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'collections':sorted(c.name for c in o.users_collection),'mesh_uv':authored(o) if o.type=='MESH' else None,'material_slots':[x.material.name if x.material else None for x in o.material_slots]}
 for k,v in now.items():
  if v!=s[k]:fail.append({'name':name,'field':k})
 err=float(np.max(np.abs(np.array(o.matrix_world)-np.array(s['world']))));max_matrix_error=max(max_matrix_error,err)
 if err>1e-6:fail.append({'name':name,'field':'saved world matrix','max_error':err})
assert len(bpy.data.objects['cab_0064'].data.vertices)==3600
dg=bpy.context.evaluated_depsgraph_get()
def geometry(o):
 e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();vs=[e.matrix_world@v.co for v in m.vertices];tris=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return vs,tris
ring,_=geometry(bpy.data.objects['cab_0029']);tube,_=geometry(bpy.data.objects['BL_Left_driver_steering_column_retained'])
r=np.array(ring);c=np.array(tube);_,rv=np.linalg.eigh(np.cov(r.T));_,cv=np.linalg.eigh(np.cov(c.T));ra=rv[:,0];ca=cv[:,-1];ra*=1 if ra[2]>0 else -1;ca*=1 if ca[2]>0 else -1
angle=math.degrees(math.atan2(np.linalg.norm(np.cross(ra,ca)),np.dot(ra,ca)));offset=(c.min(axis=0)+c.max(axis=0)-r.min(axis=0)-r.max(axis=0))/2;axis_gap=float(np.linalg.norm(offset-ra*np.dot(offset,ra)))
if angle>=1e-4 or axis_gap>=1e-6 or ra[0]<=0:fail.append({'field':'photo-hypothesis axis implementation','angle_degrees':angle,'axis_gap_m':axis_gap,'axis':ra.tolist()})
def box(v):return [(min(x[k] for x in v),max(x[k] for x in v)) for k in range(3)]
def near(a,b):return all(a[k][0]<=b[k][1] and b[k][0]<=a[k][1] for k in range(3))
wheel=bpy.data.objects['cab_pivot_004'];moving=[bpy.data.objects['BL_Left_driver_steering_column_retained']]+[o for o in wheel.children_recursive if o.type=='MESH'];names={o.name for o in moving};trees={}
for o in moving:
 vs,tris=geometry(o);trees[o.name]=(BVHTree.FromPolygons(vs,tris,all_triangles=True),box(vs))
hits=[];tested=0
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.hide_render or o.name in names:continue
 e=o.evaluated_get(dg);bounds=box([e.matrix_world@Vector(v) for v in e.bound_box]);candidates=[n for n,(_,b) in trees.items() if near(bounds,b)]
 if not candidates:continue
 vs,tris=geometry(o);fixed=BVHTree.FromPolygons(vs,tris,all_triangles=True)
 for name in candidates:
  tested+=1;pairs=trees[name][0].overlap(fixed)
  if pairs:hits.append({'moving':name,'fixed':o.name,'triangle_pairs':len(pairs)})
# The one steering hit is not the whole installation count. Recheck the two
# known, unchanged panel/wall failures separately in the saved candidate.
panel_wall=[]
wall_vs,wall_tri=geometry(bpy.data.objects['BL_Cab_1_inner_wall']);wall_tree=BVHTree.FromPolygons(wall_vs,wall_tri,all_triangles=True)
for panel_name in ['LEFT PANEL — real openings / fitted silhouette','L C22 front base']:
 vs,tris=geometry(bpy.data.objects[panel_name]);pairs=BVHTree.FromPolygons(vs,tris,all_triangles=True).overlap(wall_tree)
 panel_wall.append({'panel':panel_name,'fixed':'BL_Cab_1_inner_wall','triangle_pairs':len(pairs)})
 if not pairs:fail.append({'field':'expected unchanged panel/wall failure disappeared','panel':panel_name})
expected=record['pose']['surface_intersections']
if sorted(hits,key=str)!=sorted(expected,key=str):fail.append({'field':'fresh rest-intersection result differs from retained hypothesis'})
assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
report={'candidate_sha256':sha,'fresh_open':True,'saved_objects_checked':len(record['objects']),'max_world_matrix_error':max_matrix_error,'saved_identity_failures':fail,'actual_upward_ring_axis':ra.tolist(),'actual_upward_column_axis':ca.tolist(),'coaxial_angle_error_degrees':angle,'coaxial_line_error_m':axis_gap,'remaining_seat_vertices':3600,'narrow_phase_pairs':tested,'rest_surface_intersections':hits,'additional_known_panel_wall_intersections':panel_wall,'status':'IDENTITY_OR_IMPLEMENTATION_FAIL' if fail else 'SCOPED_IDENTITY_PASS_INSTALLATION_STILL_FAILED','limits':record['limits']+['Rest surface test is not containment or continuous sweep; object hide_render filtering only','PCA axis sign does not certify wheel front/back or gearbox input connection'],'all16VehicleGates':'OPEN'}
out.write_text(json.dumps(report,indent=2)+'\n');print('STEERING_HYPOTHESIS_READBACK',len(record['objects']),len(fail),len(hits),flush=True)
if fail:raise SystemExit(1)
if hits:raise SystemExit(2)

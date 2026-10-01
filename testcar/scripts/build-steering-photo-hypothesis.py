"""Save a photo-consistent pose hypothesis; never a calibrated installation."""
import bpy, json, hashlib, argparse, sys, numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.output.resolve();assert not out.exists()
source=ROOT/'outputs/cloud-cab-panel-fit-20261001/iteration-03/MAZ543A_Master.blend'
probe=json.loads((ROOT/'outputs/cloud-steering-axis-probe-corrected-20261001/axis-probe.json').read_text())
source_sha=hashlib.sha256(source.read_bytes()).hexdigest();assert source_sha==probe['source_sha256']
identity=json.loads(source.with_suffix('.identity.json').read_text());assert identity['status']=='PASS_SCOPED_IDENTITY_AND_ELIGIBILITY' and identity['source_sha256'][str(source)]==source_sha
pose=next(r for r in probe['poses'] if r['pose']=='coaxial_opposite_lean')
assert len(pose['surface_intersections'])==1
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
def authored(o):
 h=hashlib.sha256();m=o.data
 for seq,prop,n,dtype in [(m.vertices,'co',3,np.float32),(m.loops,'vertex_index',1,np.int32),(m.polygons,'loop_start',1,np.int32),(m.polygons,'loop_total',1,np.int32),(m.polygons,'material_index',1,np.int32)]:
  a=np.empty(len(seq)*n,dtype=dtype);seq.foreach_get(prop,a);h.update(a.tobytes())
 for uv in m.uv_layers:
  h.update(uv.name.encode());a=np.empty(len(uv.uv)*2,dtype=np.float32);uv.uv.foreach_get('vector',a);h.update(a.tobytes())
 return h.hexdigest()
def snapshot():
 return {o.name:{'type':o.type,'world':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'collections':sorted(c.name for c in o.users_collection),'mesh_uv':authored(o) if o.type=='MESH' else None,'material_slots':[s.material.name if s.material else None for s in o.material_slots]} for o in bpy.data.objects}
before=snapshot();wheel=bpy.data.objects['cab_pivot_004'];column=bpy.data.objects['BL_Left_driver_steering_column_retained']
allowed={wheel.name,column.name}|{o.name for o in wheel.children_recursive};assert len(allowed)==5
wheel.matrix_world=Matrix(pose['wheel_matrix']);column.matrix_world=Matrix(pose['column_matrix']);bpy.context.view_layer.update()
after=snapshot();assert before.keys()==after.keys()
for name,s in before.items():
 for k,v in s.items():
  if k=='world' and name in allowed:continue
  assert after[name][k]==v,(name,k)
assert len(bpy.data.objects['cab_0064'].data.vertices)==3600
for o in [wheel,column]:
 o['steering_pose_status']='PHOTO_CONSISTENT_HYPOTHESIS_NOT_CALIBRATED'
 o['steering_mount_status']='OPEN: bottom X and column length refitted, no known reducer hardpoint'
bpy.context.scene['steering_hypothesis']='Opposite legacy lean; full wheel group rotated, all seats/walls retained; one column/cushion surface intersection remains'
out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
record={'source_sha256':source_sha,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_identity_report_status':identity['status'],'objects':after,'allowed_world_matrix_changes':sorted(allowed),'pose':pose,'all_source_object_names_retained':True,'authored_mesh_uv_parent_material_slots_render_flags_preserved':True,'limits':['World transforms changed only for full wheel hierarchy and column','Angle magnitude and wheel centre inherit uncalibrated legacy geometry','Bottom Z retained, bottom X and column length refitted for coaxiality','No measured reducer mount or input connection established','Material-node content/custom normals are outside this signature scope','One column/cushion surface intersection remains in the four-steering-mesh scope; unchanged panel/wall contacts are additional and not removed','No full clearance/sweep acceptance'],'all16VehicleGates':'OPEN','production_promoted':False}
out.with_suffix('.build.json').write_text(json.dumps(record,indent=2)+'\n');print('STEERING_PHOTO_HYPOTHESIS_SAVED',out.name,len(before),flush=True)

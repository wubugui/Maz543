"""Bounded read-only inspection of existing front suspension/wheel interfaces."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
import numpy as np

p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--sha',required=True);p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);base=Path(a.base);out=Path(a.output)
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert bpy.app.version==(4,5,13),bpy.app.version
assert bpy.app.build_hash==b'daeeeca98fb0',bpy.app.build_hash
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert sha(base)==a.sha
bpy.ops.wm.open_mainfile(filepath=str(base));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
def matrix(m):return [list(r) for r in m]
def points(o):
 e=o.evaluated_get(dg);m=e.to_mesh();xyz=np.array([tuple(e.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear();return xyz
def desc(o,geom=False):
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'world':matrix(o.matrix_world),'basis':matrix(o.matrix_basis),'parent_inverse':matrix(o.matrix_parent_inverse),'rotation_mode':o.rotation_mode,'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'constraints':[{'type':c.type,'name':c.name} for c in o.constraints],'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers],'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in o.animation_data.drivers] if o.animation_data else []}
 if geom and o.type in {'MESH','CURVE'}:
  xyz=points(o);mean=xyz.mean(axis=0);eig,vec=np.linalg.eigh(np.cov(xyz-mean,rowvar=False));d['geometry']={'n':len(xyz),'centroid':mean.tolist(),'bounds':[xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],'pca_values':eig.tolist(),'pca_axes':vec.T.tolist(),'raw_vertices':len(o.data.vertices) if o.type=='MESH' else None}
 return d
rows=[];scope=set()
for i in range(4):
 n=f'S543_{i}_';roots=[bpy.data.objects[n+k] for k in ('lower','upper','upright','damper_body','damper_rod','wheel','shaft_inner','shaft_outer','lower_spline','upper_spline')]
 roots += [bpy.data.objects[f'wheels_pivot_{1+7*i:03d}'],bpy.data.objects[f'brakes_pivot_{1+i:03d}']]
 allobs=set(roots)
 for o in roots:allobs.update(o.children_recursive)
 scope.update(allobs)
 names=[n+k for k in ('lower_axis_sleeve','upper_axis_sleeve','lower_outer_bush_-1','lower_outer_bush_1','upper_outer_bush_-1','upper_outer_bush_1','upright_pin_0','upright_pin_0.397','steering_kingpin','lower_damper_pin','upper_damper_pin','shaft_inner_flange','shaft_outer_flange','shaft_inner_cross_x','shaft_outer_cross_x','halfshaft_male','halfshaft_female')]
 names += [f'BL_Tyre_{i}_VI203_profile',f'BL_Rim_{i}_bead_lock',f'BL_Rim_{i}_pressed_dish',f'BL_Hub_{i}_cover',f'BL_Hub_{i}_planetary_case']
 brake=bpy.data.objects[f'brakes_pivot_{1+i:03d}'];names += [o.name for o in brake.children_recursive if o.type=='MESH']
 rows.append({'station':i,'roots':[desc(o) for o in roots],'interfaces':[desc(bpy.data.objects[n],True) for n in names],'affected_objects':sorted(o.name for o in allobs),'dependency_observations':[desc(o) for o in sorted(allobs,key=lambda o:o.name) if o.constraints or o.modifiers or o.animation_data or (o.type=='MESH' and o.data.shape_keys)]})
# Direct object-pointer / driver-target observations only. This is not a full
# dependency proof: nested node groups, collection instances and all RNA owners
# need the repository's strict dependency qualification before a moving candidate.
reverse=[]
for o in bpy.data.objects:
 for kind,items in [('modifier',o.modifiers),('constraint',o.constraints)]:
  for item in items:
   for prop in item.bl_rna.properties:
    if prop.type=='POINTER' and prop.identifier!='rna_type':
     try:v=getattr(item,prop.identifier)
     except Exception:continue
     if isinstance(v,bpy.types.Object) and v in scope:reverse.append({'owner':o.name,'kind':kind,'item':item.name,'property':prop.identifier,'target':v.name,'owner_in_scope':o in scope})
 for f in o.animation_data.drivers if o.animation_data else []:
  for var in f.driver.variables:
   for t in var.targets:
    if isinstance(t.id,bpy.types.Object) and t.id in scope:reverse.append({'owner':o.name,'kind':'driver','path':f.data_path,'target':t.id.name,'owner_in_scope':o in scope})
assert sha(base)==a.sha
result={'status':'SCOPED_NATIVE_INTERFACE_READ_ONLY','source':str(base),'source_sha256':a.sha,'source_sha256_after':sha(base),'saved_blend':False,'blender_version':bpy.app.version_string,'blender_build_hash':bpy.app.build_hash.decode(),'autoexec':bpy.context.preferences.filepaths.use_scripts_auto_execute,'frame':0,'rows':rows,'direct_object_pointer_driver_target_observations':reverse,'dependency_scope_limit':'Direct observations only; not complete reverse dependencies or permission for moving geometry.','all16VehicleGates':'OPEN'}
out.mkdir(parents=True,exist_ok=True);(out/'interfaces.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'scope_objects':len(scope),'interfaces':sum(len(r['interfaces']) for r in rows),'reverse_dependencies':len(reverse)}),flush=True)

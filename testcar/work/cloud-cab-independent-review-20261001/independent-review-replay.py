import bpy,json,hashlib,math,ast,collections,sys
from pathlib import Path
import numpy as np
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
BEFORE=sha(SOURCE)
assert BEFORE=='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert bpy.app.version[:3]==(4,5,13)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
inv=json.loads((ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json').read_text())
rep=json.loads((ROOT/'work/cloud-cab-static-dependencies-20261001/dependency-report.json').read_text())
names=set(x['object'] for x in rep['dependency_checks'].values())|set(d['hinge'] for d in inv['doors'])
def pointers(x):
 if x is None:return {}
 out={}
 for p in x.bl_rna.properties:
  if p.type=='POINTER':
   v=getattr(x,p.identifier,None)
   if isinstance(v,bpy.types.Object):out[p.identifier]=v.name
 return out
rows=[]
for n in sorted(names):
 o=bpy.data.objects[n]
 rows.append({'name':n,'type':o.type,'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'parent_bone':o.parent_bone,'parent_vertices':list(o.parent_vertices),'object_pointers':pointers(o),'data_object_pointers':pointers(o.data),'modifier_object_pointers':[{'name':m.name,'type':m.type,'refs':pointers(m)} for m in o.modifiers if pointers(m)],'rigid_body':bool(o.rigid_body),'rigid_body_constraint':bool(o.rigid_body_constraint),'pose':bool(o.pose),'instance_type':o.instance_type,'library':bool(o.library),'data_library':bool(o.data and o.data.library)})
dg=bpy.context.evaluated_depsgraph_get()
def points(o):
 e=o.evaluated_get(dg);m=e.to_mesh()
 try:
  v=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',v);v=v.reshape(-1,3);w=np.array(e.matrix_world,dtype=float);return v@w[:3,:3].T+w[:3,3]
 finally:e.to_mesh_clear()
# Alternate independent closed-interval extremum enumeration. This does not import door_interval_bounds.
def bounds(A,B,C,lo,hi,pad):
 vals=[C+A*math.cos(t)+B*math.sin(t) for t in [lo,hi]]
 lower=np.minimum(*vals);upper=np.maximum(*vals)
 phase=np.arctan2(B,A)
 for k in range(-3,4):
  t=phase+k*math.pi
  take=(t>=lo)&(t<=hi)
  val=C+A*np.cos(t)+B*np.sin(t)
  lower=np.where(take,np.minimum(lower,val),lower);upper=np.where(take,np.maximum(upper,val),upper)
 return lower.min(0)-pad,upper.max(0)+pad
pad=2e-5
fixed=[points(bpy.data.objects[x['name']]) for x in inv['fixed_geometry']]
boxes=[(v.min(0)-pad,v.max(0)+pad) for v in fixed]
comparisons=[];hinges=[]
for door,side in zip(inv['doors'],[-1,-1,1,1]):
 h=bpy.data.objects[door['hinge']];W=np.array(h.matrix_world);IW=np.linalg.inv(W);lo,hi=sorted((0,-side*math.radians(99)))
 hinges.append({'name':h.name,'matrix_basis':list(map(list,h.matrix_basis)),'matrix_world':list(map(list,h.matrix_world)),'matrix_parent_inverse':list(map(list,h.matrix_parent_inverse)),'parent_type':h.parent_type,'rotation_mode':h.rotation_mode,'scale':list(h.scale),'delta_scale':list(h.delta_scale),'gram_matrix':(W[:3,:3].T@W[:3,:3]).tolist()})
 details=json.loads((ROOT/f"work/cloud-cab-frozen-intervals-20261001/{h.name}.json").read_text());lookup={(x[0],x[1]):x for x in details['rows']}
 assert set(lookup)=={(i,j) for i in range(len(door['parts'])) for j in range(len(boxes))}
 for i,item in enumerate(door['parts']):
  V=points(bpy.data.objects[item['name']]);P=V@IW[:3,:3].T+IW[:3,3];z=np.zeros(len(P));A=np.column_stack((P[:,0],P[:,1],z))@W[:3,:3].T;B=np.column_stack((-P[:,1],P[:,0],z))@W[:3,:3].T;C=np.column_stack((z,z,P[:,2]))@W[:3,:3].T+W[:3,3]
  low,high=bounds(A,B,C,lo,hi,pad)
  for j,(fmin,fmax) in enumerate(boxes):
   gaps=np.maximum(fmin-high,low-fmax);axis=int(np.argmax(gaps));gap=float(gaps[axis]);saved=lookup[i,j]
   comparisons.append({'hinge':h.name,'moving':item['name'],'fixed':inv['fixed_geometry'][j]['name'],'axis':axis,'gap':gap,'saved_gap':saved[4],'error':abs(gap-saved[4]),'passes':gap>0})
res={'source_sha':BEFORE,'blender':bpy.app.version_string,'properties':rows,'hinges':hinges,'pairs':len(comparisons),'all_positive':all(x['passes'] for x in comparisons),'minimum_pair':min(comparisons,key=lambda x:x['gap']),'maximum_report_difference':max(x['error'] for x in comparisons),'parent_type_counts':dict(collections.Counter(x['parent_type'] for x in rows)),'data_object_pointers':[x for x in rows if x['data_object_pointers']],'unexpected':[x for x in rows if x['parent_type']!='OBJECT' or x['rigid_body'] or x['rigid_body_constraint'] or x['pose'] or x['instance_type']!='NONE' or x['library'] or x['data_library']]}
print('ACTUAL_REVIEW',json.dumps({k:v for k,v in res.items() if k not in ['properties','hinges']},ensure_ascii=False),flush=True)
# Independent fixture only, after clearing the loaded model; never save any blend.
bpy.ops.wm.read_factory_settings(use_empty=True)
code=ast.parse((ROOT/'work/cloud-cab-independent-review-20261001/auditor-before-fix.py').read_text())
selected=[n for n in code.body if isinstance(n,ast.FunctionDef) and n.name in ['held_button_driver','audit']]
ctx={'bpy':bpy,'BUTTON':'VA180 B4 / BUTTON PRESS REVIEW — travel is fitted','moving':set(),'checks':{},'cache':{},'exceptions':[]}
exec(compile(ast.Module(body=selected,type_ignores=[]),'<audited original functions>','exec'),ctx)
h=bpy.data.objects.new('__REVIEW_HINGE',None);bpy.context.scene.collection.objects.link(h);ctx['moving'].add(h.name)
c=bpy.data.curves.new('__REVIEW_EXTERNAL_CURVE','CURVE');c.dimensions='3D';sp=c.splines.new('POLY');sp.points.add(4)
for p,co in zip(sp.points,[(0,0,0,1),(1,0,0,1),(2,0,0,1),(3,0,0,1),(4,0,0,1)]):p.co=co
co=bpy.data.objects.new('__REVIEW_EXTERNAL_CURVE',c);bpy.context.scene.collection.objects.link(co)
f=c.driver_add('splines[0].points[0].co',1);f.driver.type='SCRIPTED';v=f.driver.variables.new();v.name='p';v.type='SINGLE_PROP';v.targets[0].id=h;v.targets[0].data_path='rotation_euler[2]';f.driver.expression='p*4'
font=bpy.data.curves.new('__REVIEW_FONT','FONT');font.body='MAZ';font.size=.5;font.follow_curve=co
text=bpy.data.objects.new('__REVIEW_FONT',font);bpy.context.scene.collection.objects.link(text)
bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
a=points(text);issues=ctx['audit'](text)
h.matrix_basis=Matrix.Rotation(.7,4,'Z');bpy.context.view_layer.update();b=points(text)
res['follow_curve_fixture']={'reported_issues':issues,'accepted':not issues,'initial_vertices':len(a),'rotated_vertices':len(b),'max_vertex_delta_m':float(np.max(np.linalg.norm(a-b,axis=1))) if a.shape==b.shape else None,'curve_data_driver':c.animation_data.drivers[0].driver.expression,'actual_driven_curve_point':list(sp.points[0].co),'parent_hinge_angle':h.rotation_euler.z,'frame':bpy.context.scene.frame_current,'source_saved':False}
res['source_sha_after']=sha(SOURCE);assert res['source_sha_after']==BEFORE
(ROOT/'work/cloud-cab-independent-review-20261001/independent-review-replay.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print('FIXTURE_REVIEW',json.dumps(res['follow_curve_fixture']),flush=True)
print('SOURCE_UNCHANGED',res['source_sha_after'],flush=True)

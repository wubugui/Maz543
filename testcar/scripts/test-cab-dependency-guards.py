"""Small Blender regression fixtures; never loads or saves a project blend."""
import bpy,ast,json,hashlib,math,copy
from pathlib import Path
import numpy as np
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/cloud-cab-independent-review-20261001'
NEW=ROOT/'scripts/audit-candidate-cab-static-dependencies.py'
OLD=OUT/'auditor-before-fix.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert bpy.app.version[:3]==(4,5,13)
assert sha(OLD)=='cd5bc72f30e60663668611798e5d7c9e384d969f3e60b63588940d561d1ccc8c'
def functions(path):
 code=ast.parse(path.read_text());names={'held_button_driver','structural_transform_issues','audit','validate_evidence'}
 nodes=[n for n in code.body if isinstance(n,ast.FunctionDef) and n.name in names]
 ctx={'bpy':bpy,'math':math,'BUTTON':'VA180 B4 / BUTTON PRESS REVIEW — travel is fitted','moving':set(),'checks':{},'cache':{},'exceptions':[]}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ctx);return ctx
old,new=functions(OLD),functions(NEW)
bpy.ops.wm.read_factory_settings(use_empty=True)
h=bpy.data.objects.new('__GUARD_HINGE',None);bpy.context.scene.collection.objects.link(h)
for ctx in [old,new]:ctx['moving'].add(h.name)
c=bpy.data.curves.new('__GUARD_CURVE','CURVE');c.dimensions='3D';sp=c.splines.new('POLY');sp.points.add(4)
for p,co in zip(sp.points,[(0,0,0,1),(1,0,0,1),(2,0,0,1),(3,0,0,1),(4,0,0,1)]):p.co=co
co=bpy.data.objects.new('__GUARD_CURVE',c);bpy.context.scene.collection.objects.link(co)
f=c.driver_add('splines[0].points[0].co',1);f.driver.type='SCRIPTED';v=f.driver.variables.new();v.name='p';v.type='SINGLE_PROP';v.targets[0].id=h;v.targets[0].data_path='rotation_euler[2]';f.driver.expression='p*4'
font=bpy.data.curves.new('__GUARD_FONT','FONT');font.body='MAZ';font.size=.5;font.follow_curve=co
text=bpy.data.objects.new('__GUARD_FONT',font);bpy.context.scene.collection.objects.link(text)
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
def points(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:
  v=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',v);v=v.reshape(-1,3);w=np.asarray(e.matrix_world,dtype=np.float64);return v@w[:3,:3].T+w[:3,3]
 finally:e.to_mesh_clear()
a=points(text);before=old['audit'](text);after=new['audit'](text)
h.matrix_basis=Matrix.Rotation(.7,4,'Z');bpy.context.view_layer.update();b=points(text);delta=float(np.max(np.linalg.norm(a-b,axis=1)))
assert not before and any('follow_curve' in x for x in after) and a.shape==b.shape and delta>1
controls={'evaluated_follow_curve':{'old_issues':before,'new_issues':after,'vertices':len(a),'vertex_delta_m':delta,'frame':bpy.context.scene.frame_current,'hinge_angle_radians':h.rotation_euler.z}}
font.follow_curve=None;new['cache'].clear();assert not new['audit'](text);controls['static_text_without_external_curve']=True
parent_mesh=bpy.data.meshes.new('__GUARD_PARENT');parent_mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
parent=bpy.data.objects.new('__GUARD_PARENT',parent_mesh);bpy.context.scene.collection.objects.link(parent);h.parent=parent;h.parent_type='VERTEX'
issues=new['structural_transform_issues'](h);assert issues;controls['vertex_parent_hinge_rejected']=issues
h.parent=None;h.parent_type='OBJECT';assert not new['structural_transform_issues'](h);controls['ordinary_empty_hinge_accepted']=True
armature=bpy.data.objects.new('__GUARD_ARMATURE',bpy.data.armatures.new('__GUARD_ARMATURE'));issues=new['structural_transform_issues'](armature);assert issues;controls['armature_rejected']=issues
bpy.ops.mesh.primitive_cube_add();cube=bpy.context.object;bpy.ops.rigidbody.object_add();issues=new['structural_transform_issues'](cube);assert issues;controls['rigid_body_rejected']=issues
paths={'inventory':ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json','poses':ROOT/'work/cloud-cab-door-poses-20261001/pose-report.json','intervals':ROOT/'work/cloud-cab-frozen-intervals-20261001/interval-report.json'}
data={k:json.loads(p.read_text()) for k,p in paths.items()};details={d['hinge']:json.loads((paths['intervals'].parent/d['detail_file']).read_text()) for d in data['intervals']['doors']}
structure=new['validate_evidence'](data,details);checks=[]
for case in ['missing_pair','duplicate_pair','name_order','wrong_angle','changed_fixed','released_button_changed']:
 d=copy.deepcopy(data);t=copy.deepcopy(details);first=t['cab_pivot_002']
 if case=='missing_pair':first['rows'].pop()
 if case=='duplicate_pair':first['rows'][1]=first['rows'][0]
 if case=='name_order':first['fixed_names'][0],first['fixed_names'][1]=first['fixed_names'][1],first['fixed_names'][0]
 if case=='wrong_angle':first['angle_radians'][1]=1.0
 if case=='changed_fixed':d['poses']['poses'][0]['changed_fixed']=[{'name':'must not be ignored'}]
 if case=='released_button_changed':d['poses']['poses'][0]['button_held_exact']=False
 rejected=False
 try:new['validate_evidence'](d,t)
 except AssertionError:rejected=True
 assert rejected,case
 checks.append({'case':case,'rejected':rejected})
report={'status':'GUARD_REGRESSIONS_PASS','blender_version':bpy.app.version_string,'old_auditor_sha256':sha(OLD),'new_auditor_sha256':sha(NEW),'native_fixtures':controls,'published_evidence_structure':structure,'evidence_corruption_controls':checks,'project_blend_loaded':False,'blend_saved':False,'limits':['Fixture rejection hardens the general checker; it does not replace the separately recorded independent exact-model audit','No new full-scene motion or interval checks were rerun']}
(OUT/'guard-regression.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('GUARD_REGRESSIONS_PASS',delta,len(checks),flush=True)

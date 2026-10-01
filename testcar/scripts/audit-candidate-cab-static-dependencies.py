"""Strict dependency eligibility for the published finite-pose/interval scope.

This is a bounded scene-structure audit at frame zero, not a formal proof of
Blender implementation, a renderer validation, or a whole-vehicle certificate.
"""
import bpy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
INPUTS={
 'inventory':ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json',
 'poses':ROOT/'work/cloud-cab-door-poses-20261001/pose-report.json',
 'intervals':ROOT/'work/cloud-cab-frozen-intervals-20261001/interval-report.json'}
OUT=ROOT/'work/cloud-cab-static-dependencies-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
data={k:json.loads(p.read_text()) for k,p in INPUTS.items()}
assert all(v['source_sha256']==EXPECTED for v in data.values())
assert data['poses']['inventory_sha256']==sha(INPUTS['inventory'])
assert data['intervals']['inventory_sha256']==sha(INPUTS['inventory'])
assert data['intervals']['pose_report_sha256']==sha(INPUTS['poses'])
assert data['poses']['status']=='SAMPLED_NATIVE_POSE_REGRESSION_PASS'
assert data['intervals']['unresolved_pairs']==0
for d in data['intervals']['doors']:assert sha(INPUTS['intervals'].parent/d['detail_file'])==d['detail_sha256']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
BUTTON='VA180 B4 / BUTTON PRESS REVIEW — travel is fitted'
moving={o.name for d in data['inventory']['doors'] for o in [bpy.data.objects[d['hinge']],*bpy.data.objects[d['hinge']].children_recursive]}
checks={};cache={};exceptions=[]
def held_button_driver(o):
 ad=o.animation_data
 if o.name!=BUTTON or o.get('press_mm')!=0 or not ad or ad.action or len(ad.nla_tracks) or len(ad.drivers)!=1:return False
 f=ad.drivers[0];d=f.driver
 if f.data_path!='location' or f.array_index!=2 or f.mute or len(f.keyframe_points) or len(f.sampled_points):return False
 if d.type!='SCRIPTED' or d.expression!='-p/1000.0' or len(d.variables)!=1:return False
 v=d.variables[0]
 if v.name!='p' or v.type!='SINGLE_PROP' or len(v.targets)!=1:return False
 t=v.targets[0]
 if t.id!=o or t.data_path!='["press_mm"]':return False
 if len(f.modifiers)!=1:return False
 m=f.modifiers[0]
 if m.type!='GENERATOR' or m.mute or m.mode!='POLYNOMIAL' or m.poly_order!=1 or list(m.coefficients)!=[0.,1.] or m.use_additive or m.use_restricted_range or m.use_influence:return False
 exceptions.append({'object':o.name,'reason':'Exact single self-property driver; released press_mm held at zero; identity polynomial FCurve; no action/NLA/keys/samples'})
 return True

def audit(o,hinge=None,trail=()):
 key=(o.name,hinge.name if hinge else None)
 if key in cache:return cache[key]
 if o.name in trail:return [o.name+': dependency cycle']
 trail=(*trail,o.name);issues=[];refs=[];mods=[]
 if hinge is None and o.name in moving:issues.append(o.name+': fixed dependency enters moving hierarchy')
 if o.constraints:issues.append(o.name+': constraints not eligible')
 if o.animation_data and not held_button_driver(o):issues.append(o.name+': animation not eligible')
 if o.data and getattr(o.data,'animation_data',None):issues.append(o.name+': data animation')
 if o.data and getattr(o.data,'shape_keys',None):issues.append(o.name+': shape keys')
 for attr in ['bevel_object','taper_object']:
  if o.data and getattr(o.data,attr,None):issues.append(o.name+': external curve '+attr)
 if o.instance_type!='NONE':issues.append(o.name+': instancing not eligible')
 for m in o.modifiers:
  row={'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render};mods.append(row)
  if not m.show_viewport:continue
  if m.type in {'BEVEL','SOLIDIFY','WEIGHTED_NORMAL'}:continue
  if m.type=='BOOLEAN' and hinge is None:
   operands=([m.object] if m.operand_type=='OBJECT' and m.object else list(m.collection.all_objects) if m.operand_type=='COLLECTION' and m.collection else [])
   if not operands:issues.append(o.name+': empty Boolean operand')
   row.update({'operand_type':m.operand_type,'operands':[x.name for x in operands]})
   for operand in operands:
    refs.append(operand.name);issues.extend(audit(operand,None,trail))
  else:issues.append(o.name+': unsupported active modifier '+m.type)
 # For moving geometry, the imposed hinge transform is the motion parameter;
 # its saved ancestors are audited separately as stationary frame inputs.
 if o.parent and o.parent!=hinge:
  refs.append(o.parent.name);issues.extend(audit(o.parent,hinge,trail))
 checks[str(key)]={'object':o.name,'motion_hinge':hinge.name if hinge else None,'parent':o.parent.name if o.parent else None,'references':refs,'modifiers':mods,'issues':sorted(set(issues))}
 cache[key]=sorted(set(issues));return cache[key]
fixed_results=[{'name':x['name'],'issues':audit(bpy.data.objects[x['name']])} for x in data['inventory']['fixed_geometry']]
doors=[]
for d in data['inventory']['doors']:
 h=bpy.data.objects[d['hinge']]
 # The hinge belongs to moving hierarchy, so do not apply fixed-membership
 # rejection to itself; still audit all its actual animation/constraint inputs.
 hinge_issues=[]
 if h.animation_data or h.constraints or h.modifiers:hinge_issues.append(h.name+': hinge dynamic inputs')
 if h.parent:hinge_issues.extend(audit(h.parent))
 parts=[{'name':x['name'],'issues':audit(bpy.data.objects[x['name']],h)} for x in d['parts']]
 doors.append({'hinge':h.name,'hinge_issues':hinge_issues,'parts':parts})
all_issues=sorted(set(i for x in fixed_results for i in x['issues'])|set(i for d in doors for i in d['hinge_issues'])|set(i for d in doors for p in d['parts'] for i in p['issues']))
# Real Blender fixtures exercise rejection paths without changing source objects.
# Every fixture is unlinked and removed before the source hash check.
fixture_checks=[];created=[];actual_checks=dict(checks)
def fixture(name,curve=False):
 data=bpy.data.curves.new(name,'CURVE') if curve else bpy.data.meshes.new(name)
 o=bpy.data.objects.new(name,data);created.append((o,data));return o
try:
 baseline=fixture('__CAB_AUDIT_CONTROL_baseline')
 assert not audit(baseline)
 fixture_checks.append({'case':'static_baseline','rejected':False})
 constrained=fixture('__CAB_AUDIT_CONTROL_constraint');constrained.constraints.new('LIMIT_LOCATION')
 animated=fixture('__CAB_AUDIT_CONTROL_driver');animated.driver_add('location',0).driver.expression='frame'
 boolean=fixture('__CAB_AUDIT_CONTROL_moving_operand');mod=boolean.modifiers.new('moving operand','BOOLEAN');mod.object=bpy.data.objects['BL_Door_1_0_pressed_shell']
 curve=fixture('__CAB_AUDIT_CONTROL_curve',True);curve.data.bevel_object=fixture('__CAB_AUDIT_CONTROL_external_profile',True)
 nodes=fixture('__CAB_AUDIT_CONTROL_nodes');nodes.modifiers.new('unsupported dependency','NODES')
 for label,obj in [('constraint',constrained),('animated_driver',animated),('moving_boolean_operand',boolean),('external_curve_profile',curve),('unsupported_nodes',nodes)]:
  rejected=audit(obj);assert rejected,label
  fixture_checks.append({'case':label,'rejected':True,'issues':rejected})
finally:
 for obj,block in reversed(created):
  bpy.data.objects.remove(obj,do_unlink=True)
  if isinstance(block,bpy.types.Mesh):bpy.data.meshes.remove(block)
  else:bpy.data.curves.remove(block)
# Fixture records are kept separately, never counted as actual candidate inputs.
checks=actual_checks
report={'status':'SCOPED_NATIVE_RIGID_DEPENDENCY_ELIGIBLE' if not all_issues else 'SCOPED_NATIVE_RIGID_DEPENDENCY_FAIL','source_sha256':EXPECTED,'source_sha256_after':sha(SOURCE),'input_sha256':{k:sha(p) for k,p in INPUTS.items()},'frame':0,'button_domain':'released press_mm=0 held; no button travel','fixed':fixed_results,'doors':doors,'dependency_checks':checks,'held_driver_exceptions':exceptions,'rejection_controls':fixture_checks,'issues':all_issues,'source_saved':False,'whole_vehicle_acceptance':'16 OPEN','limits':['Only the exact source, selected 261 fixed objects and 44 moving door parts at frame zero','Combines conservative frozen-snapshot interval separation with strict supported scene-structure eligibility and separate sampled native regression; not formal verification of Blender floating-point internals','Viewport evaluated meshes only; no renderer displacement, material, web or camera validation','Does not include other vehicle surfaces or independent concurrent controls','No factory dimensions or assembled cab-interference acceptance; three known static cab contacts remain unresolved']}
assert report['source_sha256_after']==EXPECTED
(OUT/'dependency-report.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
print('DEPENDENCY_GATE',report['status'],'checks',len(checks),'issues',all_issues,flush=True)

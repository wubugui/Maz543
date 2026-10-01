"""Read-only complete406-fixed/44-door native dependency eligibility audit.

Only exact reviewed local node/subdivision profiles extend the pinned guard.
All prior object, Boolean, ancestry and held-button rules remain in force.
"""
import bpy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import cab_reviewed_dependency_context as composition
import cab_static_local_modifier_guard as local_guard

SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
DOORS=ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json'
ADDED=ROOT/'work/cloud-original-cab-contact-location-20261001/location-report.json'
INTERVAL=ROOT/'work/cloud-barrel-axis-frozen-intervals-20261001/interval-report.json'
TRIAL=ROOT/'work/cloud-door-barrel-motion-trial-20261001/trial-report.json'
OUT=ROOT/'work/cloud-static-local-cab-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=local_guard.SOURCE_SHA256
assert sha(SOURCE)==expected and bpy.app.version[:3]==(4,5,13)
data={k:json.loads(p.read_text()) for k,p in [('doors',DOORS),('added',ADDED),('intervals',INTERVAL),('trial',TRIAL)]}
assert all(v['source_sha256']==expected for v in data.values())
assert data['intervals']['input_sha256']['trial']==sha(TRIAL)
assert data['intervals']['input_sha256']['doors']==sha(DOORS)
assert data['intervals']['input_sha256']['original']==sha(ADDED)
names=[x['name'] for x in data['doors']['fixed_geometry']]+data['added']['fixed_names']
assert len(names)==len(set(names))==406 and names==data['intervals']['fixed_names']
assert data['intervals']['pairs']==17864 and data['intervals']['unresolved_pairs']==52
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();assert dg.mode=='VIEWPORT'
moving={o.name for d in data['doors']['doors'] for o in [bpy.data.objects[d['hinge']],*bpy.data.objects[d['hinge']].children_recursive]}
ctx=composition.make_context(moving)
fixed=[{'name':n,'issues':ctx['audit'](bpy.data.objects[n])} for n in names]
doors=[]
for d in data['doors']['doors']:
    h=bpy.data.objects[d['hinge']]
    issues=ctx['structural_transform_issues'](h)
    if h.animation_data or h.constraints or h.modifiers:issues.append(h.name+': hinge dynamic inputs')
    if h.parent:issues.extend(ctx['audit'](h.parent))
    parts=[{'name':x['name'],'issues':ctx['audit'](bpy.data.objects[x['name']],h)} for x in d['parts']]
    doors.append({'hinge':h.name,'hinge_issues':issues,'parts':parts})
issues=sorted({i for f in fixed for i in f['issues']}|{i for d in doors for i in d['hinge_issues']}|{i for d in doors for p in d['parts'] for i in p['issues']})
extensions=ctx['local_modifier_checks']
report={'status':'SCOPED_406_FIXED_44_DOOR_DEPENDENCY_ELIGIBLE' if not issues else 'SCOPED_406_FIXED_44_DOOR_DEPENDENCY_FAIL',
        'source_sha256':expected,'source_sha256_after':sha(SOURCE),
        'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [DOORS,ADDED,INTERVAL,TRIAL]},
        'guard_module_sha256':sha(ROOT/'scripts/cab_static_local_modifier_guard.py'),
        'composition_sha256':sha(ROOT/'scripts/cab_reviewed_dependency_context.py'),
        'base_guard_sha256':composition.BASE_SHA256,'profiles_sha256':local_guard.PROFILE_SHA256,
        'blender_version':bpy.app.version_string,'blender_build_hash':bpy.app.build_hash.decode(),
        'frame':0,'view_layer':bpy.context.view_layer.name,'depsgraph_mode':dg.mode,
        'fixed':fixed,'doors':doors,'dependency_checks':ctx['checks'],'local_modifier_checks':extensions,
        'held_driver_exceptions':ctx['exceptions'],'issues':issues,'source_saved':False,'geometry_modified':False,
        'whole_vehicle_acceptance':'16 OPEN','limits':[
            'Only the exact source at frame0 with released VA180 button and all other controls held',
            'Exact local modifier clause is not a generic NODES or SUBSURF whitelist, and applies only to stationary viewport evaluation',
            'Dependency eligibility does not resolve the52 overlapping frozen pairs or6 closed-pose surface candidates',
            'No proof of Blender floating-point internals, render displacement, web transport or factory installation',
            'Hidden and outside-root geometry, other moving doors and independent controls remain outside scope',
        ]}
assert report['source_sha256_after']==expected
(OUT/'native-dependency-report.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
print('COMPLETE_CAB_DEPENDENCY',report['status'],'fixed',len(fixed),'checks',len(ctx['checks']),'local_modifiers',len(extensions),'issues',issues,flush=True)
if not issues:assert len(extensions)==10 and all(not r['issues'] for r in extensions)

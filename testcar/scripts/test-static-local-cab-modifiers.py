"""Tiny empty-scene tests only. Never opens a vehicle file or renders/saves it."""
from pathlib import Path
import hashlib,json,sys,tempfile
import bpy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import cab_static_local_modifier_guard as guard
assert bpy.app.version[:3] == (4,5,13)
bpy.ops.wm.read_factory_settings(use_empty=True)
profiles=guard.read_profiles()
rows=[]

def build(profile):
    bpy.ops.mesh.primitive_cube_add(size=.1)
    obj=bpy.context.object;obj.name=profile['object']
    mod=obj.modifiers.new(profile['modifier'],profile['modifier_type'])
    for k,v in profile['settings'].items():
        prop=mod.bl_rna.properties[k]
        if not prop.is_readonly and k not in {'type','is_active'}:
            setattr(mod,k,v)
    if mod.type=='NODES':
        exp=profiles['node_trees'][profile['node_tree']]
        tree=bpy.data.node_groups.new(exp['name'],'GeometryNodeTree');mod.node_group=tree
        tree.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
        tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        for row in exp['nodes']:
            node=tree.nodes.new(row['type']);node.name=row['name']
            for key in ['operation','use_clamp','is_active_output']:
                if key in row['properties']:setattr(node,key,row['properties'][key])
            for direction in ['inputs','outputs']:
                for socket,expected in zip(getattr(node,direction),row[direction]):
                    if expected['default_value'] is not None:
                        socket.default_value=expected['default_value']
        for row in exp['links']:
            a=next(s for s in tree.nodes[row['from_node']].outputs if s.identifier==row['from_socket'])
            b=next(s for s in tree.nodes[row['to_node']].inputs if s.identifier==row['to_socket'])
            tree.links.new(a,b)
    bpy.context.view_layer.update()
    return obj,mod

def cleanup():
    # Only this factory-empty fixture's in-memory datablocks are touched.
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    for g in list(bpy.data.node_groups):bpy.data.node_groups.remove(g,do_unlink=True)
    for m in list(bpy.data.meshes):
        if not m.users:bpy.data.meshes.remove(m)
    bpy.context.scene.animation_data_clear()
    bpy.context.scene.render.use_simplify=False
    for name in ['frame_change_pre','frame_change_post','depsgraph_update_pre','depsgraph_update_post']:
        getattr(bpy.app.handlers,name).clear()

def run(label,profile,mutate=None,expect_reject=True,kwargs=None):
    obj,mod=build(profile)
    if mutate:mutate(obj,mod)
    issues=guard.modifier_issues(obj,mod,fixed_context=True,**(kwargs or {}))
    rows.append({'case':label,'expected_reject':expect_reject,'rejected':bool(issues),'issues':issues})
    print(label,issues or 'ELIGIBLE',flush=True)
    assert bool(issues)==expect_reject, (label,issues)
    cleanup()

for p in profiles['modifiers']:
    run('positive_'+p['object'],p,expect_reject=False)
nodep=next(p for p in profiles['modifiers'] if p['modifier_type']=='NODES')
subp=next(p for p in profiles['modifiers'] if p['modifier_type']=='SUBSURF')
def n(mod,name):return mod.node_group.nodes[name]
def add_node(kind):return lambda o,m:m.node_group.nodes.new(kind)
def setv(target,key,value):setattr(target,key,value)
def remove_input_link(o,m):m.node_group.links.remove(next(l for l in m.node_group.links if l.to_node.name=='Set Position' and l.to_socket.name=='Geometry'))
def cycle(o,m):m.node_group.links.new(n(m,'Math.004').outputs[0],n(m,'Math').inputs[0])
def extra_link(o,m):m.node_group.links.new(n(m,'Math').outputs[0],n(m,'Math.001').inputs[0],verify_limits=False)
def add_group(o,m):
    child=bpy.data.node_groups.new('Nested','GeometryNodeTree')
    m.node_group.nodes.new('GeometryNodeGroup').node_tree=child

def obj_driver(o,m):m.driver_add('show_viewport').driver.expression='1'
def socket_driver(o,m):n(m,'Math').inputs[2].driver_add('default_value').driver.expression='frame'
def mesh_shape(o,m):o.shape_key_add(name='Basis')
def external_custom(o,m):m['external']=o

tests=[
 ('wrong_object_name',lambda o,m:setattr(o,'name','Other')),
 ('missing_group',lambda o,m:setattr(m,'node_group',None)),
 ('scene_time_disconnected',add_node('GeometryNodeInputSceneTime')),
 ('object_info_disconnected',add_node('GeometryNodeObjectInfo')),
 ('collection_info_disconnected',add_node('GeometryNodeCollectionInfo')),
 ('named_attribute_disconnected',add_node('GeometryNodeInputNamedAttribute')),
 ('nested_group_disconnected',add_group),
 ('second_group_output',add_node('NodeGroupOutput')),
 ('extra_parameter',lambda o,m:m.node_group.interface.new_socket(name='Scale',in_out='INPUT',socket_type='NodeSocketFloat')),
 ('modifier_attribute_input',lambda o,m:m.__setitem__('Socket_0_use_attribute',1)),
 ('modifier_id_custom_input',external_custom),
 ('tree_custom_property',lambda o,m:m.node_group.__setitem__('unknown',1)),
 ('node_custom_property',lambda o,m:n(m,'Math').__setitem__('unknown',1)),
 ('socket_custom_property',lambda o,m:n(m,'Math').inputs[0].__setitem__('unknown',1)),
 ('empty_tree_animation',lambda o,m:m.node_group.animation_data_create()),
 ('tree_action',lambda o,m:setattr(m.node_group.animation_data_create(),'action',bpy.data.actions.new('Fixture Action'))),
 ('tree_nla_track',lambda o,m:m.node_group.animation_data_create().nla_tracks.new()),
 ('modifier_bake_target',lambda o,m:setattr(m,'bake_target','DISK')),
 ('output_muted',lambda o,m:setattr(n(m,'Group Output'),'mute',True)),
 ('unused_socket_driver',socket_driver),
 ('constant_modifier_driver',obj_driver),
 ('mesh_animation',lambda o,m:o.data.animation_data_create()),
 ('mesh_shape_keys',mesh_shape),
 ('muted_math',lambda o,m:setattr(n(m,'Math'),'mute',True)),
 ('different_allowed_math_op',lambda o,m:setattr(n(m,'Math'),'operation','ADD')),
 ('unsupported_math_op',lambda o,m:setattr(n(m,'Math'),'operation','SINE')),
 ('math_clamp',lambda o,m:setattr(n(m,'Math'),'use_clamp',True)),
 ('constant_changed',lambda o,m:setattr(n(m,'Math').inputs[1],'default_value',2.0)),
 ('nonfinite_constant',lambda o,m:setattr(n(m,'Math').inputs[1],'default_value',float('nan'))),
 ('set_position_offset',lambda o,m:setattr(n(m,'Set Position').inputs['Offset'],'default_value',(1,0,0))),
 ('set_position_selection',lambda o,m:setattr(n(m,'Set Position').inputs['Selection'],'default_value',False)),
 ('geometry_path_removed',remove_input_link),
 ('field_cycle',cycle),
 ('duplicate_link',extra_link),
 ('bake_directory',lambda o,m:setattr(m,'bake_directory','/tmp/foreign-cache')),
 ('scene_simplify',lambda o,m:setattr(bpy.context.scene.render,'use_simplify',True)),
 ('scene_animation',lambda o,m:bpy.context.scene.animation_data_create()),
 ('frame_handler',lambda o,m:bpy.app.handlers.frame_change_post.append(lambda s:None)),
 ('interface_default_attribute',lambda o,m:setattr(m.node_group.interface.items_tree[0],'default_attribute_name','some_attribute')),
 ('interface_force_non_field',lambda o,m:setattr(m.node_group.interface.items_tree[0],'force_non_field',True)),
 ('same_size_rewire',lambda o,m:m.node_group.links.new(n(m,'Separate XYZ').outputs['X'],n(m,'Math').inputs[0])),
 ('owner_constraint',lambda o,m:o.constraints.new('LIMIT_LOCATION')),
]
for label,mutation in tests:run(label,nodep,mutation)
run('render_context',nodep,kwargs={'depsgraph_mode':'RENDER'})
for label,mutation in [
 ('subsurf_level',lambda o,m:setattr(m,'levels',2)),
 ('subsurf_simple',lambda o,m:setattr(m,'subdivision_type','SIMPLE')),
 ('subsurf_limit_surface',lambda o,m:setattr(m,'use_limit_surface',False)),
 ('subsurf_driver',lambda o,m:m.driver_add('levels').driver.__setattr__('expression','1')),
]:run(label,subp,mutation)

# Fixed-context guard separately; no special caller can authorize moving use.
o,m=build(nodep)
issues=guard.modifier_issues(o,m,fixed_context=False)
assert issues;rows.append({'case':'moving_context','expected_reject':True,'rejected':True,'issues':issues})
cleanup()
# Linked-library graph is created only from this tiny generated fixture.
o,m=build(nodep);name=m.node_group.name
temporary=Path(tempfile.mkdtemp(prefix='maz-static-local-fixture-'));lib=temporary/'tiny-linked-fixture.blend'
bpy.data.libraries.write(str(lib),{m.node_group})
bpy.data.node_groups.remove(m.node_group,do_unlink=True)
with bpy.data.libraries.load(str(lib),link=True) as (available,requested):requested.node_groups=[name]
m.node_group=requested.node_groups[0]
issues=guard.modifier_issues(o,m,fixed_context=True)
assert issues;rows.append({'case':'linked_library_tree','expected_reject':True,'rejected':True,'issues':issues})
cleanup()
# Composition controls verify the local clause cannot replace the original
# ancestor, Boolean operand or upstream-modifier checks. Fresh context per case.
import cab_reviewed_dependency_context as composition
composition_rows=[]
for case in ['baseline','animated_parent','moving_boolean_operand','unsupported_upstream_modifier']:
    o,m=build(nodep);moving=set()
    if case=='animated_parent':
        parent=bpy.data.objects.new('__LOCAL_GUARD_PARENT',None);bpy.context.scene.collection.objects.link(parent)
        o.parent=parent;parent.driver_add('location',0).driver.expression='frame'
    elif case=='moving_boolean_operand':
        bpy.ops.mesh.primitive_cube_add(size=.05);operand=bpy.context.object;operand.name='__LOCAL_GUARD_MOVING'
        moving.add(operand.name);boolean=o.modifiers.new('Temporary moving Boolean operand','BOOLEAN');boolean.object=operand
    elif case=='unsupported_upstream_modifier':
        modifier=o.modifiers.new('Temporary unsupported upstream','WAVE');o.modifiers.move(len(o.modifiers)-1,0)
    assert not guard.modifier_issues(o,m,fixed_context=True),'Local clause unexpectedly changed'
    ctx=composition.make_context(moving);issues=ctx['audit'](o)
    assert bool(issues)==(case!='baseline'),(case,issues)
    composition_rows.append({'case':case,'rejected':bool(issues),'issues':issues})
    cleanup()

# Positive frame-invariance sample and simple expected analytic mapping. This is
# deliberately a fixture result, not a whole-model or continuous proof.
o,m=build(nodep);samples=[]
for frame in [0,1,31]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh()
    samples.append([list(v.co) for v in mesh.vertices]);e.to_mesh_clear()
assert samples[0]==samples[1]==samples[2]
constants={x['name']:x for x in profiles['node_trees'][nodep['node_tree']]['nodes']}
offset=constants['Math.003']['inputs'][1]['default_value']
side=constants['Math.006']['inputs'][1]['default_value']
maxerr=0.
for v,p in zip(o.data.vertices,samples[0]):
    x,y,z=v.co;expected=(max(y-1.940000057220459,0)*.4000000059604645+offset+z,(x+.5350000262260437)*side,y)
    maxerr=max(maxerr,max(abs(a-b) for a,b in zip(p,expected)))
assert maxerr<1e-6
cleanup()
report={'status':'EXACT_LOCAL_MODIFIER_FIXTURE_PASS_NOT_SOURCE_ACCEPTANCE','blender_version':bpy.app.version_string,
        'positive_cases':sum(not r['expected_reject'] for r in rows),
        'negative_cases':sum(r['expected_reject'] for r in rows),'cases':rows,
        'fixture_frame_samples':[0,1,31],'fixture_analytic_max_error_m':maxerr,
        'master_opened':False,'vehicle_assets_modified':False,'rendered':False,
        'composition_controls':composition_rows,
        'profiles_sha256':guard.PROFILE_SHA256,
        'module_sha256':hashlib.sha256((ROOT/'cab_static_local_modifier_guard.py').read_bytes()).hexdigest()}
OUT=ROOT.parent/'work/cloud-static-local-cab-20261001';OUT.mkdir(parents=True,exist_ok=True)
(OUT/'fixture-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('SUMMARY',report['status'],report['positive_cases'],report['negative_cases'],flush=True)

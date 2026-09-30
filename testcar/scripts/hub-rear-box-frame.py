"""Native curve/modifier front correction. Inputs and original components retained."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path(os.environ['HUB_OUTPUT_DIR'])
def C(p):return Vector((p[0],-p[2],p[1]))
def parent(o,p):
    m=o.matrix_world.copy();o.parent=p;o.matrix_world=m
def finish(o,name,mat,p):
    o.name=name;o.data.materials.append(mat);parent(o,p);o['restoration']='Photo-fitted front assembly 20260930; dimensions not factory calibrated'
    return o
def bevel(o,w=.008):
    m=o.modifiers.new('Manufactured edge radii','BEVEL');m.width=w;m.segments=3
    if o.type=='MESH':o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
def cube(name,size,pos,mat,p):
    bpy.ops.mesh.primitive_cube_add(size=1,location=C(pos));o=bpy.context.object;o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,name,mat,p);bevel(o);return o
def tube(name,pts,r,mat,p):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=16;d.bevel_depth=r;d.bevel_resolution=4;d.use_fill_caps=True
    s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for q,pt in zip(s.bezier_points,pts):q.co=C(pt);q.handle_left_type='AUTO';q.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return finish(o,name,mat,p)
def disk(name,pos,r,depth,mat,p):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=C(pos),rotation=(0,math.pi/2,0));o=bpy.context.object;finish(o,name,mat,p);bevel(o,.004);return o
def bounds(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();ps=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
    return {'min':[min(p.x for p in ps),min(p.z for p in ps),-max(p.y for p in ps)],'max':[max(p.x for p in ps),max(p.z for p in ps),-min(p.y for p in ps)]}
def components(o):
    adj=[[] for v in o.data.vertices]
    for e in o.data.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
    seen=set()
    for i in range(len(adj)):
        if i in seen:continue
        todo=[i];seen.add(i);ids=[]
        while todo:
            j=todo.pop();ids.append(j)
            for k in adj[j]:
                if k not in seen:seen.add(k);todo.append(k)
        yield ids
def archive(o):
    m=o.matrix_world.copy();o.hide_render=True;o.hide_set(True);o['supersededBy']='Front restoration 20260930';o.parent=None;o.matrix_world=m
    coll=bpy.data.collections.get('ARCHIVE_FRONT_20260930') or bpy.data.collections.new('ARCHIVE_FRONT_20260930')
    if coll.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(coll)
    for c in list(o.users_collection):c.objects.unlink(o)
    coll.objects.link(o)
def split_old(textured,targets):
    if not textured:
        for name in targets:
            o=bpy.data.objects.get(name)
            if o:archive(o)
        return
    # Native merged materials retain disconnected original pieces. Match each
    # old authored component's world bounds; preserve all other UV/corner data.
    unmatched=set(targets)
    # Glass/metal mirror faces were intentionally retained as separate objects
    # by the original bake workflow; archive those by their exact names.
    for name in list(unmatched):
        if bpy.data.objects.get(name):archive(bpy.data.objects[name]);unmatched.remove(name)
    for o in list(bpy.data.objects):
        if o.type!='MESH' or not o.name.startswith('BL_Merged'):continue
        chosen=set();found=[]
        for ids in components(o):
            ps=[o.matrix_world@o.data.vertices[i].co for i in ids]
            b=[min(p.x for p in ps),min(p.z for p in ps),-max(p.y for p in ps),max(p.x for p in ps),max(p.z for p in ps),-min(p.y for p in ps)]
            for name in unmatched:
                ref=targets[name]
                if max(abs(a-c) for a,c in zip(b,ref))<2e-5:chosen.update(ids);found.append(name);break
        if not chosen:continue
        bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
        for v in o.data.vertices:v.select=v.index in chosen
        for e in o.data.edges:e.select=all(i in chosen for i in e.vertices)
        for f in o.data.polygons:f.select=all(i in chosen for i in f.vertices)
        before=set(bpy.data.objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
        new=set(bpy.data.objects)-before;assert len(new)==1
        old=new.pop();old.name='ARCHIVED_'+o.name;archive(old);unmatched.difference_update(found)
    assert not unmatched,('unmatched old components',unmatched)
report={'scope':'Rear toolbox assembly moved between actual third/fourth axles; original box dimensions retained; only frame paint corrected','files':[]}
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
targets=None
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();tex=filename.endswith('Textured.blend');body=bpy.data.objects['body'];parts=[];checks=[]
    names=[f'BL_Rear_box_{s}' for s in [-1,1]]+[f'BL_Rear_box_lid_{s}' for s in [-1,1]]+[f'BL_Rear_box_latch_{s}_{x}' for s in [-1,1] for x in [4.94,5.24]]
    if not tex:
        targets={n:bounds(bpy.data.objects[n])['min']+bounds(bpy.data.objects[n])['max'] for n in names}
    # Each separate original piece is kept in the archive. Its duplicate retains
    # authored geometry, modifiers and UVs; no manually generated mesh topology.
    for index,n in enumerate(names):
        before=set(bpy.data.objects);split_old(tex,{n:targets[n]})
        if tex:
            extracted=set(bpy.data.objects)-before;assert len(extracted)==1,(n,'Expected one original component');original=extracted.pop()
        else:original=bpy.data.objects[n]
        o=original.copy();o.data=original.data.copy();bpy.context.collection.objects.link(o);o.name='BL_RearRestoration_'+n.removeprefix('BL_');o.hide_render=False;o.hide_set(False);parent(o,body);o.location.x-=1.57;o['source']='maz543a-4.jpg, maz543a-5.jpg and factory-543a-profile.jpg';o['dimensionStatus']='Original fitted box dimensions retained; factory dimensions, lid internals OPEN';parts.append(o)
    paint=bpy.data.materials.get('MAZ543A_Frame_dark_enamel') or bpy.data.materials.new('MAZ543A_Frame_dark_enamel');paint.use_nodes=True;p=paint.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.006,.008,.007,1);p.inputs['Metallic'].default_value=.15;p.inputs['Roughness'].default_value=.76
    frame_names=['frame_0002','frame_0003','frame_0004']
    for n in frame_names:
        o=bpy.data.objects[n];o.data.materials.clear();o.data.materials.append(paint)
    for side in [-1,1]:
        box=bpy.data.objects[f'BL_RearRestoration_Rear_box_{side}']
        for x in [3.37,3.67]:
            support=cube(f'BL_RearRestoration_mount_{side}_{x}',[.12,.08,.61],[x,1.175,side*.98],paint,body);parts.append(support);bpy.context.view_layer.update()
            for mate in [box,bpy.data.objects['frame_0002']]:
                pairs=len(tree(support).overlap(tree(mate)));checks.append({'mount':support.name,'mate':mate.name,'intersectionPairs':pairs});assert pairs>0,('Disconnected mounting interface',filename,support.name,mate.name)
    bpy.context.view_layer.update()
    for s in [-1,1]:
        moved=bounds(bpy.data.objects[f'BL_RearRestoration_Rear_box_{s}']);ref=targets[f'BL_Rear_box_{s}'];expected=ref[:];expected[0]-=1.57;expected[3]-=1.57;actual=moved['min']+moved['max'];assert max(abs(a-b) for a,b in zip(actual,expected))<2e-5,('Original box dimensions changed',filename,s)
    report['files'].append({'file':filename,'parts':[{'name':o.name,'parent':o.parent.name,'bounds':bounds(o)} for o in parts],'connections':checks,'frameMaterials':frame_names,'axleCentersX':[2.42,4.62],'boxCenterX':3.52,'limits':'Photographic position correction; existing approximate box proportions retained. Mount geometry is fitted, not factory calibrated; lid internals, suspension travel and whole undercarriage paint remain OPEN'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if tex:
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(o):
            while o:
                if o.name in excluded:return False
                o=o.parent
            return True
        def descendants(o):
            for c in o.children:yield c;yield from descendants(c)
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        for o in descendants(root):
            if allowed(o):o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(OUT/'rear-box-frame-verification.json').write_text(json.dumps(report,indent=2))

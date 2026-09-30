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
report={'scope':'Central cover and low round mirrors; bumper/ windshield remain open','files':[]};target_bounds=None
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    tex=filename.endswith('Textured.blend')
    names=['BL_Radiator_top_hatch']+[f'BL_Cab_{s}_mirror_{k}' for s in [-1,1] for k in ['back','face','stalk']]
    if not tex:
        target_bounds={}
        for n in names:
            o=bpy.data.objects.get(n)
            if o:
                b=bounds(o);target_bounds[n]=b['min']+b['max']
        # Native curve stalk exports as independently merged mesh pieces.
    split_old(tex,target_bounds)
    body=bpy.data.objects['body'];paint=bpy.data.materials['OD_green_aged_enamel'];steel=bpy.data.materials['Phosphated_steel'];silver=bpy.data.materials['Worn_steel'];added=[]
    # NURBS sheet: native spline control lattice, Solidify and Bevel remain editable.
    bpy.ops.surface.primitive_nurbs_surface_surface_add();o=bpy.context.object
    s=o.data.splines[0];assert len(s.points)==16
    xs=[-5.56,-5.08,-3.90,-2.93];zs=[-.51,-.17,.17,.51];hs=[2.035,2.325,2.345,2.345]
    for j in range(4):
        for i in range(4):
            pt=C((xs[i],hs[i]+(.018 if j in [1,2] else -.018),zs[j]));s.points[j*4+i].co=(*pt,1)
    s.use_endpoint_u=True;s.use_endpoint_v=True;o.data.resolution_u=16;o.data.resolution_v=12
    finish(o,'BL_Front_center_cover_NURBS',paint,body)
    # Keep the native editable surface, derive a sheet for actual Boolean port.
    source=o.copy();source.data=o.data.copy();bpy.context.collection.objects.link(source);source.name='SOURCE_Front_cover_NURBS';source.parent=None;source.hide_render=True;source.hide_set(True)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object
    o['editableSurfaceSource']=source.name
    m=o.modifiers.new('Hollow stamped cover 8mm','SOLIDIFY');m.thickness=.008;m.offset=-1
    # Existing expansion cap protrudes through a real clearance port. Do not
    # move the cooling mechanism or make the cover pass through the cap.
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.05,depth=.8,location=C((-4.65,2.30,.42)));port=bpy.context.object;port.name='TOOL_Expansion_cap_access_port';port.hide_render=True;port.hide_set(True)
    m=o.modifiers.new('Expansion filler clearance port','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=port
    bevel(o,.003);added.append(o)
    added.append(cube('BL_Front_cover_lip',[.12,.105,1.42],[-5.53,1.998,0],paint,body))
    for z in [-.46,.46]:
        added.append(tube('BL_Front_cover_latch_'+str(z),[[-5.598,2.00,z],[-5.614,2.035,z],[-5.57,2.078,z]],.011,steel,body))
    for side in [-1,1]:
        shell=bpy.data.objects['cab_pivot_001' if side==-1 else 'cab_pivot_005']
        added.append(tube(f'BL_Front_mirror_arm_{side}',[[-5.30,1.235,side*1.50],[-5.41,1.36,side*1.69],[-5.45,1.48,side*1.78],[-5.45,1.59,side*1.79]],.013,paint,shell))
        added.append(disk(f'BL_Front_mirror_back_{side}',[-5.45,1.62,side*1.79],.073,.037,paint,shell))
        added.append(disk(f'BL_Front_mirror_face_{side}',[-5.429,1.62,side*1.79],.066,.005,silver,shell))
    bpy.context.view_layer.update()
    # Real surface BVH checks in world coordinates against installed mechanisms.
    def tree(ob):
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear();return t
    ct=tree(added[0]);hits=[];tested=0
    for ob in bpy.data.objects:
        cab_surface=ob.parent and ob.parent.name in {'cab_pivot_001','cab_pivot_005'} and ob.name.startswith(('BL_Cab_','BL_Merged_cab_'))
        if ob.type=='MESH' and (ob.name.startswith(('D12_','COOL_')) or cab_surface):
            tested+=1
            if ct.overlap(tree(ob)):hits.append(ob.name)
    assert not hits,('cover intersects installed mechanics',hits)
    row={'file':filename,'archivedOriginals':list(target_bounds),'parts':[{'name':a.name,'parent':a.parent.name,'bounds':bounds(a),'modifiers':[m.type for m in a.modifiers]} for a in added],'mechanicalSurfaceIntersectionTest':{'tested':tested,'intersections':hits},'expansionAccessPort':{'centerBrowser':[-4.65,2.30,.42],'radiusM':.05,'capRadiusM':.039,'nominalRadialClearanceM':.011},'dimensions':'Photographic fit; factory dimension validation OPEN'}
    report['files'].append(row)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if tex:
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(ob):
            while ob:
                if ob.name in excluded:return False
                ob=ob.parent
            return True
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        def descendants(ob):
            for c in ob.children:yield c;yield from descendants(c)
        bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        for ob in descendants(root):
            if allowed(ob):ob.hide_set(False);ob.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(OUT/'front-assembly-verification.json').write_text(json.dumps(report,indent=2))

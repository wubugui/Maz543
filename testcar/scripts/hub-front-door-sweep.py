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
# Read-only evaluation of actual rig poses and surfaces; no saved scene changes.
from mathutils import Matrix
report={'scope':'Four actual door hinges vs all new front components at frame zero','sampling':'0..99 degrees in 3 degree increments; not a continuous collision proof','doors':[]}
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
def descendants(o):
    for c in o.children:yield c;yield from descendants(c)
bpy.ops.wm.open_mainfile(filepath=str(Path('MAZ543A_Master.blend').resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
fixed=[o for o in bpy.data.objects if o.parent and o.name.startswith('BL_Front_') and o.type in ['MESH','CURVE']]
static={o.name:tree(o) for o in fixed}
for name,side in [('cab_pivot_002',-1),('cab_pivot_003',-1),('cab_pivot_006',1),('cab_pivot_007',1)]:
    door=bpy.data.objects[name];base=door.matrix_basis.copy();parts=[o for o in descendants(door) if o.type in ['MESH','CURVE']];hits=[];states=[]
    assert parts,('Missing actual door meshes',name)
    for deg in range(0,100,3):
        # Runtime rotates this real hinge by -side * opening/100 * pi*.55.
        door.matrix_basis=base@Matrix.Rotation(-side*math.radians(deg),4,'Z');bpy.context.view_layer.update();states.append({'degrees':deg,'nativeMatrixWorld':[list(row) for row in door.matrix_world]})
        for part in parts:
            moving=tree(part)
            for other,t in static.items():
                count=len(moving.overlap(t))
                if count:hits.append({'degrees':deg,'doorPart':part.name,'fixedPart':other,'intersectionPairs':count})
    door.matrix_basis=base;bpy.context.view_layer.update()
    report['doors'].append({'hinge':name,'parts':len(parts),'states':states,'intersections':hits})
count=sum(len(d['intersections']) for d in report['doors']);report['status']='PASS sampled actual front clearance' if count==0 else 'FAIL sampled actual front clearance';report['failedPairs']=count;report['fullVehicleAcceptance']='16 OPEN; all original cab/frame/interior surfaces and continuous travel still require separate checks'
(OUT/'front-door-sweep-verification.json').write_text(json.dumps(report,indent=2))

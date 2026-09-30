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

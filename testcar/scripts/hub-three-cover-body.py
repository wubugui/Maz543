import bmesh
from mathutils import Matrix
report={'scope':'Three real central engine cover panels and front hinge, from 1977 original technical-description p173; original fitted NURBS contour retained','files':[]}
def cylinder_y(name,pos,r,depth,mat,p):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=C(pos),rotation=(math.pi/2,0,0));o=bpy.context.object;finish(o,name,mat,p);bevel(o,.001);return o
def topology(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();bm=bmesh.new();bm.from_mesh(m);r={'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolumeM3':bm.calc_volume(signed=True)};bm.free();ev.to_mesh_clear();return r
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
def overlaps(a,b):return all(a['min'][i]<=b['max'][i] and b['min'][i]<=a['max'][i] for i in range(3))
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();body=bpy.data.objects['body'];original=bpy.data.objects['BL_Front_center_cover_NURBS'];source_topology=topology(original);parts=[];metal=bpy.data.materials['MAZ543A_Front_dark_enamel'];paint=bpy.data.materials['OD_green_aged_enamel']
    hinge=bpy.data.objects.new('BL_Front_cover_hinge',None);bpy.context.collection.objects.link(hinge);hinge.location=C([-4.58,2.336,0]);parent(hinge,body);hinge['source']='1977 original technical description p173';hinge['dimensionStatus']='Fitted hinge and service angle; factory dimensions and actual catches OPEN'
    for label,lo,hi in [('front',-5.80,-4.5815),('middle',-4.5785,-3.8215),('rear',-3.8185,-2.80)]:
        o=original.copy();o.data=original.data.copy();bpy.context.collection.objects.link(o);o.name=f'BL_Front_cover_{label}_panel';o.hide_render=False;o.hide_set(False)
        cutter=cube(f'CUTTER_Central_cover_{label}',[hi-lo,6,6],[(lo+hi)/2,2.3,0],paint,body);modifier=o.modifiers.new('Separate manufactured cover panel','BOOLEAN');modifier.operation='INTERSECT';modifier.solver='EXACT';modifier.object=cutter;archive(cutter);parent(o,hinge if label=='front' else body);o['source']='1977 original technical description p173, three top panels';o['dimensionStatus']='Original fitted contour; seams, hinge axis and removable fixings uncalibrated';parts.append(o)
    archive(original)
    for side in [-1,1]:
        pin=cylinder_y(f'BL_Front_cover_hinge_pin_{side}',[-4.58,2.336,side*.475],.007,.075,metal,body);parts.append(pin)
        knuckle=cylinder_y(f'BL_Front_cover_hinge_knuckle_{side}',[-4.58,2.336,side*.475],.012,.022,metal,hinge)
        hole=cylinder_y(f'CUTTER_Cover_knuckle_bore_{side}',[-4.58,2.336,side*.475],.0073,.05,metal,body);cut=knuckle.modifiers.new('Real hinge bearing bore','BOOLEAN');cut.operation='DIFFERENCE';cut.solver='EXACT';cut.object=hole;archive(hole);parts.append(knuckle)
        for z in [side*.438,side*.512]:
            lug=cube(f'BL_Front_cover_fixed_hinge_lug_{side}_{abs(z)}',[.040,.025,.018],[-4.565,2.340,z],metal,body);parts.append(lug)
    bpy.context.view_layer.update();details=[{'name':o.name,'parent':o.parent.name,'bounds':bounds(o),'topology':topology(o)} for o in parts]
    assert all(d['topology']['nonManifoldEdges']==0 and d['topology']['signedVolumeM3']>0 for d in details),('Panel/hinge topology failure',details)
    # Broad phase only selects actual native objects; each shortlisted surface is
    # checked with evaluated triangles. Original stationary mounting contact at
    # zero degrees is recorded separately from service-opening interference.
    moving=[o for o in parts if o.parent==hinge];swept={'min':[-5.8,1.95,-.54],'max':[-4.3,3.6,.54]};static={};static_bounds={}
    for o in bpy.data.objects:
        if o.type not in ['MESH','CURVE'] or not o.parent or o in moving or o.hide_get() or o.name.startswith('SOURCE_'):continue
        b=bounds(o)
        if overlaps(b,swept):static[o.name]=tree(o);static_bounds[o.name]=b
    base=hinge.matrix_basis.copy();states=[];hits=[]
    for deg in range(0,61,3):
        hinge.matrix_basis=base@Matrix.Rotation(math.radians(deg),4,'Y');bpy.context.view_layer.update();states.append({'degrees':deg,'nativeMatrixWorld':[list(row) for row in hinge.matrix_world]})
        for o in moving:
            b=bounds(o);t=tree(o)
            for n,fixed in static.items():
                if n.startswith('BL_Front_cover_hinge_pin_') or n.startswith('BL_Front_cover_fixed_hinge_lug_'):continue
                if overlaps(b,static_bounds[n]):
                    count=len(t.overlap(fixed))
                    if count:hits.append({'degrees':deg,'panel':o.name,'fixed':n,'trianglePairs':count})
    hinge.matrix_basis=base;bpy.context.view_layer.update()
    report['files'].append({'file':filename,'parts':details,'originalCoverTopology':source_topology,'hinge':{'name':hinge.name,'browserPosition':[-4.58,2.336,0],'browserRotationAxis':'Z negative','states':states},'sampledIntersections':hits,'staticCandidates':len(static),'limits':'0..60/3degree sampled stationary scene only; catches/load/continuous contact and factory dimensional acceptance OPEN'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if filename.endswith('Textured.blend'):
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
(OUT/'three-cover-verification.json').write_text(json.dumps(report,indent=2))

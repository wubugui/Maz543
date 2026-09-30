# Native curves -> filled geometry, Geometry Nodes facade mapping, Boolean aperture.
# No authored mesh vertex/face lists. Original geometry and textures retained.
import bmesh
report={'scope':'Enlarge actual windshield opening using native curves and Boolean modifiers','files':[]};targets=None
WINDOW=[(.16,2.54),(.80,2.54),(.86,2.45),(.90,1.84),(.83,1.785),(.32,1.785),(.13,2.05),(.13,2.43)]
def rounded(poly,r=.045,steps=8):
    result=[]
    for i,pt in enumerate(poly):
        p=Vector(pt);a=Vector(poly[i-1])-p;b=Vector(poly[(i+1)%len(poly)])-p
        ra=min(r,a.length*.3);rb=min(r,b.length*.3);a=p+a.normalized()*ra;b=p+b.normalized()*rb
        for k in range(steps+1):
            t=k/steps;q=(1-t)**2*a+2*t*(1-t)*p+t*t*b;result.append(tuple(q))
    return result
def scaled(poly,k):
    cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly)
    return [(cx+(x-cx)*k,cy+(y-cy)*k) for x,y in poly]
def panel(name,side,poly,depth,offset,mat,p):
    d=bpy.data.curves.new(name+'_Editable_outline','CURVE');d.dimensions='2D';d.fill_mode='BOTH';d.extrude=depth;d.resolution_u=12
    s=d.splines.new('POLY');s.points.add(len(poly)-1);s.use_cyclic_u=True
    for q,(u,h) in zip(s.points,poly):q.co=(u,h,0,1)
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    if mat:finish(o,name,mat,p)
    # Convert the native filled/extruded curve, then retain an editable GN warp.
    bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,1.94,0),plane_no=(0,1,0),clear_inner=False,clear_outer=False)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    # The right facade field has negative determinant. Reverse native faces
    # before mapping so the Boolean cutter and glazing keep outward normals.
    if side==1:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    group=bpy.data.node_groups.new(name+'_Front_slope_map','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n=group.nodes;l=group.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');position=n.new('GeometryNodeInputPosition');sep=n.new('ShaderNodeSeparateXYZ');l.new(position.outputs['Position'],sep.inputs[0])
    def calc(op,a,b):
        q=n.new('ShaderNodeMath');q.operation=op
        if isinstance(a,(int,float)):q.inputs[0].default_value=a
        else:l.new(a,q.inputs[0])
        if isinstance(b,(int,float)):q.inputs[1].default_value=b
        else:l.new(b,q.inputs[1])
        return q.outputs[0]
    xx=calc('ADD',calc('ADD',calc('MULTIPLY',calc('MAXIMUM',calc('SUBTRACT',sep.outputs['Y'],1.94),0),.4),-5.45-offset),sep.outputs['Z'])
    yy=calc('MULTIPLY',calc('ADD',sep.outputs['X'],.535),-side)
    comb=n.new('ShaderNodeCombineXYZ');l.new(xx,comb.inputs['X']);l.new(yy,comb.inputs['Y']);l.new(sep.outputs['Y'],comb.inputs['Z']);setpos=n.new('GeometryNodeSetPosition');l.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);l.new(comb.outputs[0],setpos.inputs['Position']);l.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
    mod=o.modifiers.new('Native field mapping to sloped cab front','NODES');mod.node_group=group
    return o
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();tex=filename.endswith('Textured.blend')
    if tex:
        # Opaque seals were consolidated into the old texture atlas. Append
        # the exact authored rubber shader from the supplied native master.
        needed=[n for n in ['Rubber_window_seals','Laminated_glass','Phosphated_steel'] if bpy.data.materials.get(n) is None]
        if needed:
            with bpy.data.libraries.load(str(Path('MAZ543A_Master.blend').resolve()),link=False) as (available,loaded):
                assert all(n in available.materials for n in needed);loaded.materials=needed
    if not tex:
        names=[f'BL_Cab_{s}_{k}' for s in [-1,1] for k in ['windscreen_gasket','windscreen','wiper_arm','wiper_blade']]
        targets={n:bounds(bpy.data.objects[n])['min']+bounds(bpy.data.objects[n])['max'] for n in names}
    split_old(tex,targets)
    results=[]
    for side,parent_name in [(-1,'cab_pivot_001'),(1,'cab_pivot_005')]:
        p=bpy.data.objects[parent_name]
        facade=bpy.data.objects[f'BL_Cab_{side}_front_shell'] if not tex else bpy.data.objects[f'BL_Merged_{parent_name}_OD_green_aged_enamel']
        opening=rounded(WINDOW)
        cut=panel('TOOL_Windshield_opening_'+str(side),side,opening,.25,0,None,None);cut.hide_render=True;cut.hide_set(True)
        bo=facade.modifiers.new('Actual enlarged front window opening','BOOLEAN');bo.operation='DIFFERENCE';bo.solver='EXACT';bo.object=cut
        gasket=panel(f'BL_Front_windshield_gasket_{side}',side,scaled(opening,1.018),.006,.009,bpy.data.materials['Rubber_window_seals'],p)
        inner=panel('TOOL_Windshield_gasket_inner_'+str(side),side,scaled(opening,.928),.08,.009,None,None);inner.hide_render=True;inner.hide_set(True)
        m=gasket.modifiers.new('Hollow rubber gasket','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=inner;bevel(gasket,.003)
        glass=panel(f'BL_Front_windshield_glass_{side}',side,scaled(opening,.926),.004,-.006,bpy.data.materials['Laminated_glass'],p)
        def front(u,h,depth):return [-5.45+max(0,h-1.94)*.4-depth,h,side*(.535+u)]
        arm=tube(f'BL_Front_wiper_arm_{side}',[front(.45,2.53,.031),front(.54,1.94,.049)],.0075,bpy.data.materials['Phosphated_steel'],p)
        blade=tube(f'BL_Front_wiper_blade_{side}',[front(.47,2.32,.058),front(.57,1.86,.058)],.011,bpy.data.materials['Rubber_window_seals'],p)
        bpy.context.view_layer.update();ev=facade.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
        tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
        rays=[]
        for h,z,expect in [(1.89,1.10,False),(2.3,.95,False),(2.4,1.12,False),(1.5,1.05,True),(1.5,.65,False)]:
            # Textured paint is a merged cab mesh. Limit the ray to the entire
            # front facade slab; distant rear walls must not count as blocked
            # glass. Both native files use the same probe and expected result.
            q=tree.ray_cast(C([-6,h,side*z]),Vector((1,0,0)),.85)
            hit=q[0] is not None
            assert hit==expect,('Actual aperture ray',filename,side,h,z,hit,expect);rays.append({'h':h,'lateral':z,'hitShell':hit,'rayNativeXRange':[-6,-5.15],'hitPointNative':list(q[0]) if hit else None})
        bm=bmesh.new();bm.from_mesh(mesh);bad=sum(not e.is_manifold for e in bm.edges);bm.free();ev.to_mesh_clear()
        if not tex:assert bad==0,('Non-manifold enlarged shell',side,bad)
        results.append({'side':side,'facade':facade.name,'rays':rays,'nonManifoldEdges':bad,'glassBounds':bounds(glass),'newParts':[gasket.name,glass.name,arm.name,blade.name]})
    report['files'].append({'file':filename,'facades':results,'status':'Actual aperture ray checks passed; photo proportions and factory dimensions OPEN'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if tex:
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(o):
            while o:
                if o.name in excluded:return False
                o=o.parent
            return True
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        def descendants(o):
            for c in o.children:yield c;yield from descendants(c)
        bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        for o in descendants(root):
            if allowed(o):o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(OUT/'windshield-native-verification.json').write_text(json.dumps(report,indent=2))

# Read-only actual evaluated surfaces. No scene geometry changes.
report={'scope':'Frame-zero front mounting surfaces; full dynamics OPEN','files':[]}
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
bpy.ops.wm.open_mainfile(filepath=str(Path('MAZ543A_Master.blend').resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
names=['BL_Front_box_bumper','BL_Front_hook_mount','BL_Front_single_recovery_hook','BL_Front_lower_shield','frame_0002','frame_0003','frame_0004']
trees={n:tree(bpy.data.objects[n]) for n in names};pairs=[]
for a,b in [('BL_Front_box_bumper','BL_Front_hook_mount'),('BL_Front_single_recovery_hook','BL_Front_hook_mount'),('BL_Front_lower_shield','BL_Front_box_bumper')]:
    pairs.append({'a':a,'b':b,'surfaceIntersectionPairs':len(trees[a].overlap(trees[b]))})
samples=[]
for side in [-1,1]:
    point=C([-5.36,.945,side*1.10]);near=[]
    for name in ['frame_0002','frame_0003','frame_0004']:
        q=trees[name].find_nearest(point)
        if q[0] is not None:near.append({'object':name,'distance_m':q[3],'native_point':list(q[0]),'browser_point':[q[0].x,q[0].z,-q[0].y]})
    samples.append({'probe':'Bumper rear face','side':side,'nearestFrameSurfaces':sorted(near,key=lambda x:x['distance_m'])})
    cab=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(f'BL_Cab_{side}_') and o.parent and o.parent.name in ['cab_pivot_001','cab_pivot_005']]
    point=C([-5.30,1.235,side*1.50]);near=[]
    for o in cab:
        q=tree(o).find_nearest(point)
        if q[0] is not None:near.append({'object':o.name,'distance_m':q[3],'browser_point':[q[0].x,q[0].z,-q[0].y]})
    samples.append({'probe':'New low mirror arm root','side':side,'nearestCabSurfaces':sorted(near,key=lambda x:x['distance_m'])[:3]})
report.update(pairs=pairs,samples=samples,limits='Nearest-surface probes and static intersection counts are evidence for mount design; not load rating or full travel clearance.')
(OUT/'front-installation-audit.json').write_text(json.dumps(report,indent=2))

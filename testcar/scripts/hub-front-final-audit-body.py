import bmesh
report={'scope':'Read-only original vs corrected baked cab topology and final front geometry','files':[]}
for filename in ['Baseline_Textured.blend','MAZ543A_Textured.blend','MAZ543A_Master.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();results=[]
    names=[f'BL_Merged_cab_pivot_{p}_OD_green_aged_enamel' for p in ['001','005']] if filename!='MAZ543A_Master.blend' else [f'BL_Cab_{s}_front_shell' for s in [-1,1]]
    for name in names:
        o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();bm=bmesh.new();bm.from_mesh(mesh)
        results.append({'name':name,'vertices':len(bm.verts),'faces':len(bm.faces),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'wireEdges':sum(e.is_wire for e in bm.edges),'signedVolumeM3':bm.calc_volume(signed=True)})
        bm.free();ev.to_mesh_clear()
    if filename!='Baseline_Textured.blend':
        results.extend({'name':o.name,'parent':o.parent.name,'bounds':bounds(o)} for o in bpy.data.objects if o.parent and o.name.startswith('BL_Front_') and o.type in ['MESH','CURVE'])
    report['files'].append({'file':filename,'objects':results})
(OUT/'front-final-native-audit.json').write_text(json.dumps(report,indent=2))

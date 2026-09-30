report={'scope':'Read-only actual rear toolbox/tyre surfaces at rest and installed engine/cooling vs rear hood envelopes','limitations':'No suspension travel or factory dimensional certification; existing fitted native assembly is being measured, not accepted'}
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
bpy.ops.wm.open_mainfile(filepath=str(Path('MAZ543A_Master.blend').resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
rear=[o for o in bpy.data.objects if o.parent and o.name.startswith('BL_RearRestoration_') and o.type in ['MESH','CURVE']]
tyres=[o for o in bpy.data.objects if o.name.startswith(tuple(f'BL_Tyre_{i}_' for i in [4,5,6,7])) and o.parent]
fixed={o.name:tree(o) for o in tyres};hits=[]
for o in rear:
    t=tree(o)
    for name,v in fixed.items():
        count=len(t.overlap(v))
        if count:hits.append({'rearPart':o.name,'tyre':name,'intersectionPairs':count})
report['rearStaticTyreClearance']={'parts':len(rear),'tyres':len(tyres),'hits':hits,'status':'PASS sampled rest pose' if not hits else 'FAIL'}
hood=[o for o in bpy.data.objects if o.parent and o.name.startswith(('BL_Power_bay','BL_Bay_','BL_Louver_','BL_Hood_')) and o.type in ['MESH','CURVE']]
report['hoodParts']=[{'name':o.name,'bounds':bounds(o)} for o in hood]
report['installedEnvelopes']={}
for label,prefix in [('engine','D12_'),('cooling','COOL_')]:
    rows=[bounds(o) for o in bpy.data.objects if o.parent and o.name.startswith(prefix) and o.type in ['MESH','CURVE']]
    report['installedEnvelopes'][label]={'objects':len(rows),'min':[min(r['min'][i] for r in rows) for i in range(3)],'max':[max(r['max'][i] for r in rows) for i in range(3)]}
(OUT/'rear-static-hood-audit.json').write_text(json.dumps(report,indent=2))

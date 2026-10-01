"""Fresh readback of photo-grip candidate; preserves old r3 failures as OPEN."""
import bpy,bmesh,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-cover-grips-20261001'
def snapshot(o,dg):
    e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles()
    v=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',v)
    t=np.empty(len(m.loop_triangles)*3,dtype=np.int32);m.loop_triangles.foreach_get('vertices',t)
    record={'local_geometry_sha256':hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest(),'vertices':len(m.vertices),'triangles':len(m.loop_triangles),'matrix_world':[list(r) for r in e.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render}
    points=[e.matrix_world@p.co for p in m.vertices];tri=[tuple(x.vertices) for x in m.loop_triangles]
    e.to_mesh_clear();return record,points,tri
def bounds(points):return [[min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]]
def broad(a,b):return all(a[0][k]<=b[1][k] and b[0][k]<=a[1][k] for k in range(3))
report={'scope':'New photo-observed grips only; retained r3 latch release and lip/grille failures remain OPEN. Four diagnostic poses are not continuous clearance proof.','files':[],'all16VehicleGates':'OPEN'}
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    path=OUT/filename;before=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0)
    ctrl=bpy.data.objects['BL_Cover_service_DIAGNOSTIC_CONTROL'];ctrl['service_stage']=0.;ctrl.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    original=json.loads((OUT/(filename+'.source-geometry-fingerprints.json')).read_text());changed=[]
    for name,expected in original.items():
        actual,_,_=snapshot(bpy.data.objects[name],dg)
        if actual!=expected:changed.append(name)
    assert not changed,changed
    grip_names=['BL_Photo_front_cover_top_grip_-1','BL_Photo_front_cover_top_grip_1'];panel=bpy.data.objects['BL_Front_cover_front_panel'];topology=[];relative={}
    for name in grip_names:
        o=bpy.data.objects[name];ev=o.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(m);bm.normal_update()
        points=[ev.matrix_world@v.co for v in m.vertices];tri=[tuple(t.vertices) for t in m.loop_triangles];tree=BVHTree.FromPolygons(points,tri,all_triangles=True)
        row={'name':name,'vertices':len(m.vertices),'non_manifold_edges':sum(not x.is_manifold for x in bm.edges),'non_manifold_vertices':sum(not x.is_manifold for x in bm.verts),'volume_m3':bm.calc_volume(signed=True),'degenerate_faces':sum(x.calc_area()<1e-15 for x in bm.faces),'nonadjacent_self_intersections':sum(1 for a,b in tree.overlap(tree) if a<b and not set(tri[a])&set(tri[b]))}
        topology.append(row);pm=panel.evaluated_get(dg).matrix_world.inverted();relative[name]=[pm@p for p in points];bm.free();ev.to_mesh_clear()
    poses=[]
    for stage in [0,1,1.5,2]:
        ctrl['service_stage']=stage;ctrl.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pm=panel.evaluated_get(dg).matrix_world
        grips={};errors={}
        for name in grip_names:
            rec,p,t=snapshot(bpy.data.objects[name],dg);grips[name]=(p,t,BVHTree.FromPolygons(p,t,all_triangles=True),bounds(p))
            errors[name]=max((point-pm@local).length for point,local in zip(p,relative[name]))
        contacts=[]
        for o in bpy.context.scene.objects:
            if o.type not in {'MESH','CURVE','SURFACE','FONT'} or o.name in grip_names:continue
            if o.hide_render or o.name.startswith(('CUTTER_','TOOL_','SOURCE_','ARCHIVE')) or any(c.name.startswith('ARCHIVE') for c in o.users_collection):continue
            ev=o.evaluated_get(dg);box=bounds([ev.matrix_world@Vector(v) for v in ev.bound_box])
            possible=[n for n,g in grips.items() if broad(g[3],box)]
            if not possible:continue
            _,p,t=snapshot(o,dg);tree=BVHTree.FromPolygons(p,t,all_triangles=True)
            for name in possible:
                hits=grips[name][2].overlap(tree)
                if hits:contacts.append({'grip':name,'other':o.name,'triangle_pairs':len(hits),'classification':'FITTED_FOOT_EMBED_ATTACHMENT_UNVALIDATED' if o==panel else 'UNRESOLVED_SURFACE_INTERSECTION'})
        poses.append({'service_stage':stage,'grip_attachment_assumption_world_vertex_error_m':errors,'surface_intersections':contacts})
    row={'file':filename,'candidate_sha256':before,'old_geometry_objects_exactly_preserved':len(original),'changed_old_geometry_objects':changed,'new_grips':topology,'diagnostic_poses':poses,'file_unchanged':hashlib.sha256(path.read_bytes()).hexdigest()==before,'interior_containment_scope':'Only triangle intersections in the sampled pose broadphase; no general containment or swept-solid claim.','source_photo_handling':'Build script uses source URLs and metadata only; no new photograph is loaded or packed'}
    report['files'].append(row);(OUT/'native-readback.json').write_text(json.dumps(report,indent=2))
    assert all(r['non_manifold_edges']==r['non_manifold_vertices']==r['degenerate_faces']==r['nonadjacent_self_intersections']==0 and r['volume_m3']>0 for r in topology)
    assert all(max(p['grip_attachment_assumption_world_vertex_error_m'].values())<2e-5 for p in poses)
    assert all(c['classification']=='FITTED_FOOT_EMBED_ATTACHMENT_UNVALIDATED' for p in poses for c in p['surface_intersections'])
    assert row['file_unchanged']
    print('PHOTO_GRIPS_READBACK',filename,len(original),'old geometries preserved;2closed grips;4diagnostic poses',flush=True)

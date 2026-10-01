"""Check saved fitted relief, its zero-amplitude control and changed interfaces."""
import bpy,bmesh,json,hashlib,os,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-cover-contour-20261001';SOURCE=ROOT/'outputs/cloud-cover-grips-20261001'
records=json.loads((OUT/'native-readback.json').read_text()) if (OUT/'native-readback.json').exists() else []
filenames=['MAZ543A_Master.blend','MAZ543A_Textured.blend']
if os.environ.get('MAZ_CONTOUR_FILE'):filenames=[os.environ['MAZ_CONTOUR_FILE']]
def snapshot(o,topology=False):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    a=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',a);t=np.empty(len(me.loop_triangles)*3,dtype=np.int32);me.loop_triangles.foreach_get('vertices',t)
    local=[v.co.copy() for v in me.vertices];world=[ev.matrix_world@p for p in local];tri=[tuple(v.vertices) for v in me.loop_triangles]
    fingerprint={'local_geometry_sha256':hashlib.sha256(a.tobytes()+t.tobytes()).hexdigest(),'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'matrix_world':[list(r) for r in ev.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render}
    tree=BVHTree.FromPolygons(world,tri,all_triangles=True,epsilon=0);stats=None
    if topology:
        bm=bmesh.new();bm.from_mesh(me);bm.normal_update();stats={'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'non_manifold_vertices':sum(not v.is_manifold for v in bm.verts),'volume_m3':bm.calc_volume(signed=True),'degenerate_faces':sum(f.calc_area()<1e-15 for f in bm.faces),'nonadjacent_self_intersections':sum(1 for i,j in tree.overlap(tree) if i<j and not set(tri[i])&set(tri[j]))};bm.free()
    ev.to_mesh_clear();return {'fingerprint':fingerprint,'local':local,'world':world,'tri':tri,'tree':tree,'topology':stats}
def nearest_max(a,b):
    k=KDTree(len(b))
    for i,p in enumerate(b):k.insert(p,i)
    k.balance();return max(k.find(p)[2] for p in a)
for filename in filenames:
    path=OUT/filename;before=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0)
    control=bpy.data.objects['BL_Cover_service_DIAGNOSTIC_CONTROL'];control['service_stage']=0;control.update_tag();bpy.context.view_layer.update()
    original=json.loads((SOURCE/(filename+'.source-geometry-fingerprints.json')).read_text());panel=bpy.data.objects['BL_Front_cover_front_panel'];changed=[]
    for name,expected in original.items():
        if name==panel.name:continue
        if snapshot(bpy.data.objects[name])['fingerprint']!=expected:changed.append(name)
    assert not changed,changed
    modifier=next(m for m in panel.modifiers if m.name.startswith('PHOTO fitted'));socket=next(s.identifier for s in modifier.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name=='Fitted amplitude m')
    amplitude=modifier[socket];default=snapshot(panel,True)
    modifier[socket]=0.;panel.update_tag();bpy.context.view_layer.update();zero=snapshot(panel)
    src=json.loads((OUT/(filename+'.source-panel.json')).read_text());src_vertices=[Vector(p) for p in src['local_vertices']]
    zero_difference=max(nearest_max(src_vertices,zero['local']),nearest_max(zero['local'],src_vertices))
    # A local control isolates the field from unknown photographed dimensions.
    # It checks that disabling the proposed relief recovers its input surface.
    modifier[socket]=amplitude;panel.update_tag();bpy.context.view_layer.update();restored=snapshot(panel,True)
    assert restored['fingerprint']==default['fingerprint']
    parts={panel.name:restored}
    for side in [-1,1]:
        name='BL_Photo_front_cover_top_grip_'+str(side);parts[name]=snapshot(bpy.data.objects[name],True)
    interface_names=['BL_Front_cover_lip','BL_Front_cover_middle_panel','BL_Front_cover_latch_-0.46','BL_Front_cover_latch_0.46']
    interfaces={n:snapshot(bpy.data.objects[n]) for n in interface_names};contacts=[]
    for name,part in parts.items():
        for other,other_part in {**interfaces,**parts}.items():
            if name==other:continue
            hits=part['tree'].overlap(other_part['tree'])
            if hits:contacts.append({'a':name,'b':other,'surface_triangle_pairs':len(hits),'status':'REPORTED_UNVALIDATED_INTERFACE'})
    poses=[]
    for stage in [.5,1,1.5,2]:
        control['service_stage']=stage;control.update_tag();bpy.context.view_layer.update()
        moving={n:snapshot(bpy.data.objects[n]) for n in parts};fixed={n:snapshot(bpy.data.objects[n]) for n in interface_names}
        deformation={n:max(nearest_max(parts[n]['local'],p['local']),nearest_max(p['local'],parts[n]['local'])) for n,p in moving.items()}
        intersections=[];seen=set()
        for name,p in moving.items():
            for other,q in {**fixed,**moving}.items():
                key=tuple(sorted([name,other]))
                if name==other or key in seen:continue
                seen.add(key);hits=p['tree'].overlap(q['tree'])
                if hits:intersections.append({'a':name,'b':other,'surface_triangle_pairs':len(hits),'status':'REPORTED_UNVALIDATED_INTERFACE'})
        poses.append({'diagnostic_service_stage':stage,'local_vertex_set_deformation_m':deformation,'selected_surface_intersections':intersections})
    control['service_stage']=0;control.update_tag();bpy.context.view_layer.update()
    row={'file':filename,'candidate_sha256':before,'unchanged_original_geometry_objects_except_front_panel':len(original)-1,'unexpected_changed_original_geometry_objects':changed,'zero_amplitude_bidirectional_vertex_set_difference_m':zero_difference,'zero_amplitude_source_triangle_index_match':zero['tri']==[tuple(t) for t in src['triangles']],'restored_default_exact':True,'modified_parts_topology':{n:p['topology'] for n,p in parts.items()},'closed_selected_interface_surface_intersections':contacts,'additional_selected_diagnostic_poses':poses,'scope':'Three modified geometries and selected interfaces in five discrete states only; not full clearance, containment or continuous service sweep. Inherited r3 failures remain OPEN.','source_photo_calibration':'Fitted broad relief; no manufacturer pressing dimensions','file_unchanged':hashlib.sha256(path.read_bytes()).hexdigest()==before,'all16VehicleGates':'OPEN'}
    records=[r for r in records if r['file']!=filename]+[row];(OUT/'native-readback.json').write_text(json.dumps(records,indent=2))
    assert zero_difference<2e-5
    assert all(max(p['local_vertex_set_deformation_m'].values())<2e-5 for p in poses)
    assert all(t['non_manifold_edges']==t['non_manifold_vertices']==t['degenerate_faces']==t['nonadjacent_self_intersections']==0 and t['volume_m3']>0 for t in row['modified_parts_topology'].values())
    assert row['file_unchanged']
    print('PHOTO_CONTOUR_READBACK',filename,'zero_field_difference',zero_difference,'selected_interfaces',len(contacts),flush=True)

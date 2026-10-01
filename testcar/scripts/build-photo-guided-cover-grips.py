"""Add only the two photo-observed top grips to independent r3 vehicle copies.

This is a visual omission correction, not repair of the old latch/lip failures.
Native Bezier/Bevel/Weld remain editable; no guessed screw holes or hinge axes.
"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-cover-service-r3-20260930'
OUT=ROOT/'outputs/cloud-cover-grips-20261001';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def geometry_fingerprints():
    import numpy as np
    dg=bpy.context.evaluated_depsgraph_get();rows={}
    for o in bpy.context.scene.objects:
        if o.type not in {'MESH','CURVE','SURFACE','FONT'}:continue
        e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles()
        v=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',v)
        t=np.empty(len(m.loop_triangles)*3,dtype=np.int32);m.loop_triangles.foreach_get('vertices',t)
        rows[o.name]={'local_geometry_sha256':hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest(),'vertices':len(m.vertices),'triangles':len(m.loop_triangles),'matrix_world':[list(r) for r in e.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render}
        e.to_mesh_clear()
    return rows
def parent_keep(o,p):
    bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=p;o.matrix_world=world;bpy.context.view_layer.update()
records=[]
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    path=SOURCE/filename;before=sha(path)
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0)
    ctrl=bpy.data.objects['BL_Cover_service_DIAGNOSTIC_CONTROL'];ctrl['service_stage']=0.;ctrl.update_tag();bpy.context.view_layer.update()
    original=geometry_fingerprints();panel=bpy.data.objects['BL_Front_cover_front_panel']
    e=panel.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    v=[e.matrix_world@p.co for p in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles]
    tree=BVHTree.FromPolygons(v,faces,all_triangles=True,epsilon=0);e.to_mesh_clear()
    grips=[]
    for side in [-1,1]:
        x=-5.36;center=side*.245;width=.18;rise=.045;radius=.008
        y0,y1=center-width/2,center+width/2
        hits=[]
        for y in [y0,y1]:
            hit,normal,face,distance=tree.ray_cast(Vector((x,y,3)),Vector((0,0,-1)),2.)
            assert hit is not None and 2<hit.z<2.4
            hits.append(hit.z)
        points=[]
        for fraction,height in [(0,0),(0,.020),(.12,.041),(.3,rise),(.7,rise),(.88,.041),(1,.020),(1,0)]:
            y=y0+fraction*width;z=hits[0]*(1-fraction)+hits[1]*fraction-.003+height;points.append((x,y,z))
        curve=bpy.data.curves.new('PHOTO_GRIP_native_bezier_'+str(side),'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3;curve.resolution_u=12;curve.use_fill_caps=True
        sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
        for bp,co in zip(sp.bezier_points,points):bp.co=co;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
        o=bpy.data.objects.new('BL_Photo_front_cover_top_grip_'+str(side),curve);bpy.context.scene.collection.objects.link(o)
        curve.materials.append(bpy.data.materials['OD_green_aged_enamel'])
        weld=o.modifiers.new('Native coincident curve cap seam weld','WELD');weld.merge_threshold=1e-6
        parent_keep(o,panel)
        o['source']='Adrian Kot Flickr8680069876 + Fototruck1875,232059,83391; register hood-photo-register-20261001.json'
        o['role']='Photograph-observed transverse arched top grip, separate from front-edge fastener'
        o['calibration']='FITTED:180mm width,45mm rise,16mm tube diameter; exact section, feet/fasteners and dimensions not established'
        o['attachment']='Fitted3mm endpoint embed into current panel; intended mount contact, not weld/fastener or strength validation'
        o['motion']='Follows existing front panel as attachment assumption; old r3 latch diagnostic and interference failures remain'
        grips.append({'name':o.name,'source_surface_foot_z_m':hits,'fitted_curve_points_world_m':points,'tube_radius_m':radius})
    bpy.context.view_layer.update();after=geometry_fingerprints()
    changed=[name for name,row in original.items() if after.get(name)!=row];assert not changed,changed
    record={'file':filename,'source_sha256':before,'old_geometry_objects_preserved':len(original),'new_grips':grips,'status':'VISUAL_OMISSION_CORRECTION_ONLY_R3_FAILURES_REMAIN','all16VehicleGates':'OPEN'}
    note=bpy.data.texts.new('PHOTO_GRIPS_20261001_SCOPE');note.write(json.dumps(record,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    assert sha(path)==before
    record['candidate_sha256']=sha(OUT/filename);records.append(record)
    (OUT/(filename+'.source-geometry-fingerprints.json')).write_text(json.dumps(original,indent=2))
    (OUT/'build-manifest.json').write_text(json.dumps(records,indent=2))
    print('PHOTO_GRIPS_SAVED',filename,len(original),'old geometry objects exactly preserved',flush=True)

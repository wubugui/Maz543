"""Photo-fitted continuous front-cover relief, independent of production.

Native local-position Geometry Nodes precede the original Solidify/Booleans.
The fit is not an OEM pressing, material/section or latch-support certification.
"""
import bpy,json,math,hashlib,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'outputs/cloud-cover-grips-20261001';OUT=ROOT/'outputs/cloud-cover-contour-20261001';OUT.mkdir(exist_ok=True)
filenames=['MAZ543A_Master.blend','MAZ543A_Textured.blend']
if os.environ.get('MAZ_CONTOUR_FILE'):filenames=[os.environ['MAZ_CONTOUR_FILE']]
report=json.loads((OUT/'build-manifest.json').read_text()) if (OUT/'build-manifest.json').exists() else []
for filename in filenames:
    path=SOURCE/filename;before=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0)
    ctrl=bpy.data.objects['BL_Cover_service_DIAGNOSTIC_CONTROL'];ctrl['service_stage']=0;ctrl.update_tag();bpy.context.view_layer.update()
    panel=bpy.data.objects['BL_Front_cover_front_panel'];assert all(abs(panel.matrix_world[i][j]-(1 if i==j else 0))<1e-8 for i in range(4) for j in range(4))
    ev=panel.evaluated_get(bpy.context.evaluated_depsgraph_get());source_mesh=ev.to_mesh();source_mesh.calc_loop_triangles()
    (OUT/(filename+'.source-panel.json')).write_text(json.dumps({'source_sha256':before,'local_vertices':[list(v.co) for v in source_mesh.vertices],'triangles':[list(t.vertices) for t in source_mesh.loop_triangles]}))
    ev.to_mesh_clear()
    old_stack=[m.name for m in panel.modifiers];solidify=next((i for i,m in enumerate(panel.modifiers) if m.type=='SOLIDIFY'),None);assert solidify is not None
    group=bpy.data.node_groups.new('Photo fitted broad front-cover relief | local coordinates','GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    amp=group.interface.new_socket(name='Fitted amplitude m',in_out='INPUT',socket_type='NodeSocketFloat');amp.default_value=.028;amp.min_value=0;amp.max_value=.05
    nodes=group.nodes;links=group.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');pos=nodes.new('GeometryNodeInputPosition');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(pos.outputs['Position'],sep.inputs['Vector'])
    def math_node(operation,inputs,label):
        n=nodes.new('ShaderNodeMath');n.operation=operation;n.label=label
        for i,value in enumerate(inputs):
            if isinstance(value,(int,float)):n.inputs[i].default_value=value
            else:links.new(value,n.inputs[i])
        return n.outputs[0]
    phase=math_node('MULTIPLY',[sep.outputs['Y'],2*math.pi/.49],'Fitted transverse period490mm')
    wave=math_node('COSINE',[phase],'Central broad ridge and side shoulders')
    positive=math_node('MULTIPLY_ADD',[wave,.5,.5],'Two grip troughs between broad ridges')
    def fade(a,b,va,vb,label):
        n=nodes.new('ShaderNodeMapRange');n.clamp=True;n.interpolation_type='SMOOTHERSTEP';n.label=label
        links.new(sep.outputs['X'],n.inputs['Value'])
        for key,val in [('From Min',a),('From Max',b),('To Min',va),('To Max',vb)]:n.inputs[key].default_value=val
        return n.outputs['Result']
    front=fade(-5.56,-5.47,0,1,'Fitted90mm front-edge runout')
    rear=fade(-4.82,-4.58,1,0,'Fitted240mm rear seam runout')
    delta=math_node('MULTIPLY',[positive,front],'Front runout');delta=math_node('MULTIPLY',[delta,rear],'Rear runout');delta=math_node('MULTIPLY',[delta,inp.outputs['Fitted amplitude m']],'Fitted amplitude, not measured')
    combine=nodes.new('ShaderNodeCombineXYZ');links.new(delta,combine.inputs['Z'])
    setpos=nodes.new('GeometryNodeSetPosition');links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);links.new(combine.outputs['Vector'],setpos.inputs['Offset']);links.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
    mod=panel.modifiers.new('PHOTO fitted continuous relief before shell thickness','NODES');mod.node_group=group;mod[amp.identifier]=.028
    bpy.context.view_layer.objects.active=panel
    while list(panel.modifiers).index(mod)>solidify:bpy.ops.object.modifier_move_up(modifier=mod.name)
    panel['photo_contour_status']='FITTED_GEOMETRIC_STUDY; broad ridge/trough evidence only; exact pressing, width, edge fold and back reinforcement unknown'
    panel['photo_contour_sources']='Adrian Kot Flickr8680069876 MAZ543A-labelled; Fototruck1875,232059,83391; see hood-photo-register-20261001.json'
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();e=panel.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles()
    tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);e.to_mesh_clear()
    foot_updates=[]
    for side in [-1,1]:
        grip=bpy.data.objects['BL_Photo_front_cover_top_grip_'+str(side)];points=grip.data.splines[0].bezier_points;world=grip.matrix_world.copy();inv=world.inverted()
        ends=[world@points[0].co,world@points[-1].co];new_z=[]
        for endpoint in ends:
            p,_,_,_=tree.ray_cast(Vector((endpoint.x,endpoint.y,3)),Vector((0,0,-1)),2);assert p is not None;new_z.append(p.z-.003)
        shifts=[new_z[i]-ends[i].z for i in range(2)]
        for point in points:
            p=world@point.co;f=(p.y-ends[0].y)/(ends[1].y-ends[0].y);p.z+=shifts[0]*(1-f)+shifts[1]*f;point.co=inv@p
        grip['photo_contour_attachment']='Foot endpoint elevations refitted to actual new panel,3mm embed; hardware/strength still OPEN; changing relief requires reseating'
        foot_updates.append({'grip':grip.name,'endpoint_z_shifts_m':shifts})
    bpy.context.view_layer.update()
    row={'file':filename,'source_sha256':before,'fitted_amplitude_m':.028,'fitted_transverse_period_m':.49,'front_runout_x_m':[-5.56,-5.47],'rear_runout_x_m':[-4.82,-4.58],'existing_modifier_stack':old_stack,'new_modifier_stack':[m.name for m in panel.modifiers],'geometry_node_group':group.name,'amplitude_socket_identifier':amp.identifier,'grip_foot_refits':foot_updates,'scope':'Only front surface and two grips; all original r3 latch, lip/grille and factory mounting failures remain','all16VehicleGates':'OPEN'}
    note=bpy.data.texts.new('PHOTO_CONTOUR_STUDY_SCOPE');note.write(json.dumps(row,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True);assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    row['candidate_sha256']=hashlib.sha256((OUT/filename).read_bytes()).hexdigest();report=[r for r in report if r['file']!=filename]+[row];(OUT/'build-manifest.json').write_text(json.dumps(report,indent=2));print('PHOTO_CONTOUR_SAVED',filename,flush=True)

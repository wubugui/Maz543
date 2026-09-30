"""Measure actual installed interfaces before attempting to attach the Cardan.

All dimensions here describe the authored model, not the original truck.
The independent Cardan is tested in its current envelope; it is not scaled to fit.
"""
import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Master.blend'))
bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
data = json.loads((ROOT/'work/cardan-poses.json').read_text())['spec']

def vec(v): return [float(x) for x in v]
def web(v): return [float(v.x), float(v.z), float(-v.y)]
def interface(name):
    o = bpy.data.objects[name]
    # The flange's authored geometry uses local +X as its outward face normal.
    x = max(o['fittedAxialFaces'])
    p = o.matrix_world @ Vector((x,0,0))
    u = (o.matrix_world.to_3x3() @ Vector((1,0,0))).normalized()
    return p,u
def angle(a,b): return math.degrees(math.acos(max(-1,min(1,a.dot(b)))))

# Verify the actual independent native fork seating offset before using it.
with bpy.data.libraries.load(str(ROOT/'outputs/MAZ543A_Cardan_Master.blend'),link=False) as (src,dst):
    dst.objects = ['CJ_flange_fork_0','CJ_flange_fork_1']
forks = list(dst.objects)
offsets = []
for end,o in enumerate(forks):
    assert o is not None
    coordinates = [v.co.x for v in o.data.vertices]
    offsets.append(-min(coordinates) if end == 0 else max(coordinates))
assert all(abs(x-.05)<1e-6 for x in offsets), offsets
for o in forks: bpy.data.objects.remove(o,do_unlink=True)

rows=[]
for side in range(2):
    lower,lu=interface(f'COOL_lower_cardan_flange_{side}')
    upper,uu=interface(f'COOL_upper_input_flange_{side}')
    a=lower+lu*offsets[0]; b=upper+uu*offsets[1]
    span=b-a; length=span.length; direction=span.normalized()
    beta0=angle(lu,direction); beta1=angle(-uu,direction)
    overlap=data['maleEnd']-(length-data['femaleReach'])
    endgap=length-.044-data['maleEnd']
    validAngles=max(beta0,beta1)<=data['maxBend']+1e-7
    validLength=data['crossDistance']-1e-7<=length<=data['crossDistance']+data['maxExtension']+1e-7
    rows.append(dict(side=side,lowerFace=web(lower),lowerOutward=web(lu),upperFace=web(upper),upperOutward=web(uu),
        lowerCross=web(a),upperCross=web(b),faceSeparationMM=(upper-lower).length*1000,
        crossDistanceMM=length*1000,directedJointAnglesDegrees=[beta0,beta1],
        splineOverlapMM=overlap*1000,splineEndGapMM=endgap*1000,
        independentRigAngleRangePass=validAngles,independentRigLengthRangePass=validLength,
        installableInCurrentVerifiedRig=validAngles and validLength,
        native=dict(lowerFace=vec(lower),upperFace=vec(upper),lowerCross=vec(a),upperCross=vec(b),lowerAxis=vec(lu),upperAxis=vec(uu))))
drift=0.0
for frame in [60,120,300,600]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    for row in rows:
        for kind,name in [('lower',f'COOL_lower_cardan_flange_{row["side"]}'),('upper',f'COOL_upper_input_flange_{row["side"]}')]:
            p,u=interface(name)
            drift=max(drift,(p-Vector(row['native'][kind+'Face'])).length,(u-Vector(row['native'][kind+'Axis'])).length)
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
assert drift<1e-5, 'Moving interface axis requires time-dependent installation analysis'
report=dict(status='OPEN',coordinateSystem='Browser: X longitudinal, Y up, Z lateral; values are authored model metres.',
    sourceMaster='MAZ543A_Master.blend',sampledFrames=[0,60,120,300,600],maximumInterfacePositionOrUnitAxisDrift=drift,
    angleDefinition='Directed: lower outward normal to lower-to-upper cross line; negative upper outward normal to that line. Not the acute angle between unoriented shaft lines.',
    nativeForkSeatOffsetsMM=[x*1000 for x in offsets],
    verifiedIndependentCrossRangeMM=[data['crossDistance']*1000,(data['crossDistance']+data['maxExtension'])*1000],
    verifiedIndependentMaximumBendDegrees=data['maxBend'],connections=rows,
    limits='Rigid flange seats and current fork offsets only. Exceeding this inspection-rig envelope does not establish original MAZ joint limits. No installation dimension has been inferred from the exploded view; no geometry moved to manufacture a passing result.')
(ROOT/'outputs/cardan-installation-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

# An editable inspection file makes the measured failure reviewable in Blender.
col=bpy.data.collections.new('INSTALLATION_MEASUREMENTS');bpy.context.scene.collection.children.link(col)
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
red=material('Unclosed shaft line',(1,.12,.035));blue=material('Flange axis',(.04,.48,1));white=material('Measurement text',(.8,.85,.9))
def line(name,points,mat,r=.002):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,v in zip(s.points,points):p.co=(*v,1)
    o=bpy.data.objects.new(name,c);col.objects.link(o);c.materials.append(mat)
def label(name,text,p):
    c=bpy.data.curves.new(name,'FONT');c.body=text;c.size=.025;c.align_x='CENTER'
    o=bpy.data.objects.new(name,c);col.objects.link(o);c.materials.append(white);o.location=p
    o.rotation_euler=(math.pi/2,0,0)
for row in rows:
    n=row['native'];lo=Vector(n['lowerFace']);hi=Vector(n['upperFace']);a=Vector(n['lowerCross']);b=Vector(n['upperCross'])
    line('Unclosed_Cardan_'+str(row['side']),[a,b],red)
    for name,p,u in [('lower',lo,Vector(n['lowerAxis'])),('upper',hi,Vector(n['upperAxis']))]:
        line(f'Face_normal_{row["side"]}_{name}',[p,p+u*.1],blue)
    mid=Vector((-5.12,-.30 if row['side']==0 else .30,1.13))
    label('Connection_'+str(row['side']),f'{row["crossDistanceMM"]:.1f} mm\n{row["directedJointAnglesDegrees"][0]:.1f} / {row["directedJointAnglesDegrees"][1]:.1f} deg',mid)
text=bpy.data.texts.new('CARDAN_INSTALLATION_AUDIT.json');text.write(json.dumps(report,indent=2))
label('Audit_caption','MODEL INTERFACES - NOT ORIGINAL DIMENSIONS\nBlue: outward axes   Orange: required cross-centre line',Vector((-5.12,0,1.84)))
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
scene.world.color=(.03,.03,.03)
# Isolate the installed gearboxes only in this separate inspection scene.
for o in bpy.data.objects:
    if o.type in ['MESH','CURVE']:
        o.hide_render=not (o.get('lowerDrive') or o.get('upperGearbox')) or o.get('coolingRole') in ['housing','support']
for o in col.objects:o.hide_render=False
for o in bpy.context.scene.objects:
    if o.type in ['MESH','CURVE']:o.hide_set(o.hide_render)
camera_data=bpy.data.cameras.new('Installed interface inspection');camera=bpy.data.objects.new('Installed interface inspection',camera_data);scene.collection.objects.link(camera)
camera.location=(-6.5,0,1.50);target=Vector((-4.82,0,1.50));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=1.15;scene.camera=camera
for o in col.objects:
    if o.type=='FONT':o.rotation_euler=camera.rotation_euler
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.region_3d.view_camera_zoom=0
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Installation_Audit.blend'),compress=True)
scene.render.filepath=str(ROOT/'outputs/cardan-installation-audit.png');bpy.ops.render.render(write_still=True)
print('CARDAN_INSTALLATION_MEASURED',json.dumps(report),flush=True)

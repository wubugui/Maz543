"""Independent FG16 structural study, never a production writer.

Native Bezier/POLY profiles -> Blender conversion -> Screw/Solidify/Boolean.
No mesh vertices/faces are manually constructed. Every metric is a fitted study
parameter; Fig.137 is undimensioned. Run with official Blender 4.5.13, 4 threads.
"""
import bpy, bmesh, math, json, hashlib, itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REF = ROOT/'testcar/work/cloud-reference-20260930/nominal-table'
PRODUCTION = [ROOT/'testcar/outputs/MAZ543A_Master.blend', ROOT/'testcar/outputs/MAZ543A_Textured.blend', ROOT/'testcar/public/models/maz543a-blender.glb']
SOURCE = 'https://drive.google.com/file/d/1quwh1UlmlDyw-WHAIPwLYbylRmNDXUr1/view?usp=drivesdk'
EXPECTED = ['0391bfde5b7474a5f1ac4eac955f2fd8dbbb6febd33fb7d772a2cd18575edec3', 'f927cfffae77e443fe6f7c8536bb2344d6b7694f335a071a26d4bba22e350f5d', '4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

before={str(p.relative_to(ROOT)):sha(p) for p in PRODUCTION}
assert list(before.values())==EXPECTED, before
bpy.ops.wm.open_mainfile(filepath=str(PRODUCTION[0]))
production_geometry={}
for name in ['BL_Searchlight_housing','BL_Searchlight_lens','BL_Searchlight_stand']:
    obj=bpy.data.objects[name]
    raw={'verts':[list(v.co) for v in obj.data.vertices], 'edges':[list(e.vertices) for e in obj.data.edges], 'faces':[list(p.vertices) for p in obj.data.polygons], 'matrix':[list(row) for row in obj.matrix_world]}
    production_geometry[name]={'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons), 'geometry_matrix_sha256':hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()}
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.name='FG16_ASSEMBLED_STUDY'
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='MILLIMETERS'
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.cycles.max_bounces=12
scene.cycles.transmission_bounces=8
scene.render.threads_mode='FIXED'
scene.render.threads=4
scene.render.resolution_x=1400
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Neutral studio world')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.29,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
scene.view_settings.view_transform='AgX'
scene.render.film_transparent=False

def coll(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
parts=coll('01_FG16_SOURCE_INDEXED_COMPONENTS')
profiles=coll('02_EDITABLE_SOURCE_CURVES')
bench=coll('03_STUDY_FIXTURE_NOT_VEHICLE_HARDWARE')
cutters=coll('04_NATIVE_BOOLEAN_TOOLS')
studio=coll('05_CYCLES_STUDIO')
profiles.hide_render=True
profiles.hide_viewport=True
cutters.hide_render=True
def move_coll(o,c):
    for existing in list(o.users_collection):existing.objects.unlink(o)
    c.objects.link(o)
def mat(name,color,metallic=0,rough=.3,transmission=0,ior=1.5):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Transmission Weight'].default_value=transmission
    bs.inputs['IOR'].default_value=ior
    m['status']='Illustrative material, no specimen-calibrated roughness/IOR/reflectance'
    return m
paint=mat('FITTED olive painted metal',(.16,.195,.08),.55,.29)
rim_mat=mat('FITTED slightly worn rim paint',(.12,.145,.061),.62,.26)
rubber=mat('FITTED dark gasket',(.017,.02,.014),0,.58)
silver=mat('FITTED optical reflector appearance',(.8,.84,.86),.96,.11)
metal=mat('FITTED plated lamp base',(.42,.38,.27),.8,.26)
glass=mat('SOURCE clear colorless smooth glass | IOR fitted',(.99,.995,1),0,.025,1,1.5)
bulbglass=mat('FITTED bulb glass',(.98,.99,1),0,.055,1,1.47)
wiremat=mat('FITTED wire-route envelope',(.045,.049,.04),0,.62)
fixturemat=mat('STUDY fixture dark graphite',(.032,.045,.057),.65,.3)
floor_mat=mat('Studio floor',(.21,.25,.29),0,.66)
labelmat=mat('Label white',(.78,.83,.86),0,.8)

def empty(name,c,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);c.objects.link(o);o.location=loc;o.empty_display_size=.025;return o
yaw=empty('CONTROL_YAW_340deg_SOURCE_ZERO_FITTED',parts)
yaw['azimuth_deg']=0.0
yaw.id_properties_ui('azimuth_deg').update(min=-170,max=170,soft_min=-170,soft_max=170,description='Source total span 340 degrees; symmetric zero and stop directions fitted. Does not model cab steering control.')
yaw['source']='1977 p216: horizontal total travel 340 degrees'
yaw['zero_and_stops']='FITTED: ±170 is centered convenience, not documented original orientation'
yaw['vertical_motion']='UNMODELED: until mechanical stop, no source angle value'
yaw.rotation_mode='XYZ'
fc=yaw.driver_add('rotation_euler',2);d=fc.driver;d.expression='max(-170,min(170,a))*pi/180'
v=d.variables.new();v.name='a';v.type='SINGLE_PROP';v.targets[0].id=yaw;v.targets[0].data_path='["azimuth_deg"]'
lim=yaw.constraints.new('LIMIT_ROTATION');lim.name='Source 340 total; reference zero fitted';lim.owner_space='LOCAL';lim.use_limit_z=True;lim.min_z=math.radians(-170);lim.max_z=math.radians(170)
head=empty('FG16_OPTICAL_AXIS_X',parts,(0,0,.238));head.parent=yaw
head['status']='Independent study placement; does not prescribe installed stem length or 2920 mm vehicle posture'

register=[]
def tag(obj,number,desc,method,source=True):
    obj['source_figure']='1977 third edition, Fig.137 p217' if source else 'Study fixture only'
    obj['source_label']=str(number)
    obj['description']=desc
    obj['dimension_status']='FITTED: undimensioned drawing; no manufacturing dimension/tolerance claim'
    obj['authoring_method']=method
    register.append({'object':obj.name,'source_label':str(number),'description':desc,'method':method,'dimension_status':'FITTED','is_vehicle_component':source})
    return obj

def curve_profile(name,pts,closed=False,smooth=True):
    cu=bpy.data.curves.new(name+'_editable_curve','CURVE');cu.dimensions='3D';cu.resolution_u=12
    sp=cu.splines.new('BEZIER' if smooth else 'POLY')
    if smooth:
        sp.bezier_points.add(len(pts)-1)
        for p,co in zip(sp.bezier_points,pts):
            p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    else:
        sp.points.add(len(pts)-1)
        for p,co in zip(sp.points,pts):p.co=(*co,1)
    sp.use_cyclic_u=closed
    o=bpy.data.objects.new(name+'_PROFILE',cu);profiles.objects.link(o)
    o['status']='Editable native curve source for revolved part; rerun build to regenerate profile mesh'
    return o

def revolve(name,xy,material,number,desc,closed=False,smooth=True,thickness=None,offset=-1):
    src=curve_profile(name,[(x,r,0) for x,r in xy],closed,smooth)
    o=src.copy();o.data=src.data.copy();parts.objects.link(o);o.name=name
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.parent=head
    screw=o.modifiers.new('Native Screw X 360deg | profile retained','SCREW');screw.axis='X';screw.angle=2*math.pi;screw.steps=96;screw.render_steps=128;screw.use_merge_vertices=True;screw.merge_threshold=.00001;screw.use_normal_calculate=True;screw.use_smooth_shade=True
    if thickness:
        sol=o.modifiers.new('FITTED wall via native Solidify','SOLIDIFY');sol.thickness=thickness;sol.offset=offset;sol.use_even_offset=True;sol.use_rim=True
    o.data.materials.append(material)
    tag(o,number,desc,'Native curve converted by Blender, live Screw'+(' + Solidify' if thickness else ''))
    return o

# Outer diameter/depth are only continuity-scale choices, not original measurements.
housing=revolve('FG16_06_Hollow_curved_body',[(.086,0),(.080,.030),(.061,.066),(.025,.099),(-.025,.116),(-.061,.117),(-.072,.115)],paint,6,'Curved hollow lamp body; lower wire port cut by native Boolean',thickness=.002,offset=-1)
glassobj=revolve('FG16_01_Colorless_smooth_glass',[(-.094,0),(-.093,.035),(-.089,.075),(-.081,.108)],glass,1,'Smooth clear colorless glass; shallow curvature fitted from section, not flat white disk',thickness=.003,offset=-1)
rim=revolve('FG16_02_Independent_front_rim',[(-.087,.109),(-.089,.112),(-.089,.117),(-.085,.12),(-.076,.12),(-.073,.116),(-.073,.114),(-.078,.114),(-.080,.111),(-.081,.109)],rim_mat,2,'Independent front retaining rim; lip profile fitted',closed=True,smooth=False)
bev=rim.modifiers.new('FITTED formed edge fillet','BEVEL');bev.width=.0007;bev.segments=3
gasket=revolve('FG16_03_Sealing_ring',[(-.081,.108),(-.081,.1115),(-.076,.1130),(-.075,.109),(-.079,.1078)],rubber,3,'Separate seal at glass/rim/optical element interface; compression unverified',closed=True,smooth=False)
reflector=revolve('FG16_05_Hollow_optical_element',[(.009,.017),(.004,.021),(-.010,.043),(-.034,.071),(-.061,.099),(-.076,.109)],silver,5,'Hollow concave optical element; exact optical prescription/coating unverified',thickness=.0015,offset=-1)
bulb=revolve('FG16_04_Lamp_glass',[(-.070,0),(-.068,.012),(-.058,.021),(-.042,.023),(-.021,.017),(-.007,.0105),(.001,.0105)],bulbglass,4,'Bulb envelope; filament geometry and lamp manufacturing dimensions unmodeled',thickness=.00045,offset=-1)
bulbbase=revolve('FG16_04_Lamp_metal_base',[(.022,0),(.022,.010),(.018,.014),(-.001,.014),(-.001,.0105),(.0,.0105),(.0,.013),(.017,.013),(.021,.0095),(.021,0)],metal,4,'Simplified lamp mounting base; bayonet details/electrode count/thread pitch unverified',closed=False,smooth=False)
bulbbase.modifiers[0].use_normal_flip=True
socket=revolve('FG16_07_Cap_base',[(.004,.0165),(.004,.025),(.025,.027),(.034,.021),(.034,.005),(.031,.005),(.028,.0165),(.022,.0165),(.022,.010),(.019,.0145),(.005,.0145)],metal,7,'Source cap/base arrangement behind central lamp; contact mechanism not resolved',closed=True,smooth=False)
bev=socket.modifiers.new('FITTED cap edge fillet','BEVEL');bev.width=.0004;bev.segments=2

def native_cyl(name,radius,depth,loc,material,c,parent=None,axis='Z',vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;move_coll(o,c)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    if parent:o.parent=parent
    o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o

# Single route envelope intentionally avoids asserting a conductor count.
cu=bpy.data.curves.new('Wiring route editable Bezier','CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=.003;cu.bevel_resolution=4;cu.use_fill_caps=True
sp=cu.splines.new('BEZIER');sp.bezier_points.add(6)
for p,co in zip(sp.bezier_points,[(.031,0,0),(.042,0,0),(.045,0,-.020),(.024,0,-.048),(.003,0,-.076),(0,0,-.117),(0,0,-.183)]):
    p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
wire_source=bpy.data.objects.new('FG16_08_Wiring_route_PROFILE',cu);profiles.objects.link(wire_source)
wire=wire_source.copy();wire.data=cu.copy();parts.objects.link(wire);wire.name='FG16_08_Wiring_route_envelope';wire.parent=head;wire.data.materials.append(wiremat)
bpy.ops.object.select_all(action='DESELECT');wire.select_set(True);bpy.context.view_layer.objects.active=wire;bpy.ops.object.convert(target='MESH');wire=bpy.context.object
weld=wire.modifiers.new('Native Weld curve cap seams','WELD');weld.merge_threshold=.000001
tag(wire,8,'One route envelope for documented wires, NOT a conductor-count assertion; no electrical circuit','Native Bezier tube with caps converted by Blender, live Weld; curve retained')
port=native_cyl('TOOL_wire_exit_clearance',.010,.060,(0,0,-.119),fixturemat,cutters,head)
port.hide_render=True;port.hide_set(True);port.display_type='WIRE'
bm=housing.modifiers.new('Native Boolean fitted wire exit aperture','BOOLEAN');bm.operation='DIFFERENCE';bm.solver='EXACT';bm.object=port
seam=housing.modifiers.new('Native Weld Boolean near-coincident seam','WELD');seam.merge_threshold=.000001

# Source fastener is identified; omit fabricated installation geometry.
fastener=empty('FG16_09_FASTENER_UNMODELED_LOCATOR',parts,(.014,0,-.137));fastener.parent=head;fastener.empty_display_type='SPHERE';fastener.empty_display_size=.008
tag(fastener,9,'Source fastening screw identified; geometry, exact axis and attached bracket UNMODELED','Non-rendering source locator, NOT a reconstructed fastener')
fastener['modeling_status']='UNMODELED_SOURCE_IDENTIFIED'

# Separate, explicitly non-original support to make the horizontal study control usable.
fixturebase=native_cyl('BENCH_pedestal_NOT_VEHICLE_PART',.08,.016,(0,0,.008),fixturemat,bench)
tag(fixturebase,'BENCH','Display-only pedestal, no claim of real cab mounting geometry','Native cylinder',False)
fixturestem=native_cyl('BENCH_support_NOT_VEHICLE_PART',.017,.090,(0,0,.060),fixturemat,bench,yaw)
tag(fixturestem,'BENCH','Display-only stand; original cab stem, controls, vertical articulation remain unmodeled','Native cylinder',False)
fixturetop=native_cyl('BENCH_collar_NOT_VEHICLE_PART',.023,.027,(0,0,.1075),fixturemat,bench,yaw)
tag(fixturetop,'BENCH','Display-only collar; native bore keeps wiring envelope clear','Native cylinder + Boolean',False)
stemport=native_cyl('TOOL_bench_wire_bore',.006,.15,(0,0,.083),fixturemat,cutters,yaw)
stemport.hide_set(True);stemport.hide_render=True
for o in [fixturestem,fixturetop]:
    m=o.modifiers.new('Wire routing bore | illustrative bench','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=stemport
for o in [fixturebase,fixturestem,fixturetop]:
    m=o.modifiers.new('Bench edge bevel','BEVEL');m.width=.001;m.segments=3

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001));ground=bpy.context.object;ground.name='Studio_ground';move_coll(ground,studio);ground.data.materials.append(floor_mat)
def camera(name,loc,target,ortho):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=ortho;data.lens=50;return o
cam=camera('CAMERA_ASSEMBLED',(-.52,-.68,.44),(0,0,.184),.57);scene.camera=cam
secam=camera('CAMERA_SECTION',(-.15,-.80,.27),(0,0,.183),.53)
def area(name,loc,power,size,target):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Key softbox',(-.4,-.4,.72),32,.42,(0,0,.2))
area('Rear contour',(.45,.15,.5),42,.3,(0,0,.2))
area('Front glass strip',(-.5,.4,.32),18,.25,(0,0,.23))
overlay=bpy.data.materials.new('Study annotation');overlay.use_nodes=True
nt=overlay.node_tree;nt.nodes.clear();n=nt.nodes.new('ShaderNodeEmission');n.inputs[0].default_value=(.79,.85,.9,1);n.inputs[1].default_value=.8;output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(n.outputs[0],output.inputs[0])
def label(name,body,loc,size):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x='LEFT'
    ob=bpy.data.objects.new(name,cu);studio.objects.link(ob);ob.parent=cam;ob.location=loc;cu.materials.append(overlay);return ob
label('LABEL_title','FG16  |  SOURCE STRUCTURE STUDY',(-.254,.201,-.2),.010)
footer=label('LABEL_footer','FITTED DIMENSIONS  /  DISPLAY STAND IS NOT VEHICLE HARDWARE',(-.254,-.209,-.2),.007)
darkoverlay=overlay.copy();darkoverlay.name='Study annotation dark';darkoverlay.node_tree.nodes.get('Emission').inputs[0].default_value=(.065,.085,.10,1);footer.data.materials.clear();footer.data.materials.append(darkoverlay)

for filename in ['1977-original-p216-217.png','1977-original-p26-27.png']:
    im=bpy.data.images.load(str(REF/filename));im.pack();im.use_fake_user=True;im['source_url']=SOURCE
    im['source_title']='Колесное шасси МАЗ-543 и его модификации. Техническое описание'
    im['source_edition']='3rd edition, Moscow 1977, Военное издательство Министерства обороны СССР'
    im['source_sha256']=sha(REF/filename)
    im['rights_status']='Local research reference; public redistribution license not established. Shareable edition omits scan pixels.'
notes='''FG16 / ФГ16 independent structural study, 2026-09-30
Original 1977 third edition table p27 names ФГ16 without suffix. Fig.137 p217
identifies 1 glass, 2 rim, 3 gasket, 4 lamp, 5 optical element, 6 body,
7 cap/base, 8 wires, 9 fastening screw. Native curves are retained and live
Screw/Solidify/Boolean modifiers are editable. Single wire route is an envelope,
not a count of conductors. Fastener #9 is a non-rendering locator only;
its geometry and original mounting installation remain unmodeled.
The actual section supports a curved hollow body, separate clear smooth glass,
retaining parts and hollow optical bowl. It supplies NO manufacturing dimensions.
240 mm scale and about 180 mm depth inherit unverified historical photo fitting;
all cross-sections, curvature, thicknesses, bulb and socket dimensions are fitted.
No optical prescription, wattage, voltage, luminous output or beam validation.
340 degrees is documented horizontal total travel. The bench property limits
azimuth to ±170 for convenience; zero and stop directions are not original data.
Vertical motion is explicitly UNMODELED; the manual provides no angle range.
Bench pedestal/support is NOT vehicle mounting hardware. Original support,
cab control mechanism, mechanical vertical stops and installed height are OPEN.
No original production file, old candidate, web asset or vehicle pose is changed.
All 16 whole-vehicle gates remain OPEN. This study is not promoted to production.
Section render cuts only glass/rim/gasket/reflector/housing, keeping bulb/base/
wiring and bench uncut for visibility. It is a presentation cut, not a real part.
'''
txt=bpy.data.texts.new('READ_ME_FG16_STUDY.txt');txt.write(notes)
txt=bpy.data.texts.new('BUILD_SCRIPT_SOURCE.py');txt.write(Path(__file__).read_text())
(OUT/'README.md').write_text(notes+'\nSource: '+SOURCE+'\n',encoding='utf8')
(OUT/'parts-register.json').write_text(json.dumps(register,ensure_ascii=False,indent=2),encoding='utf8')

def evaluated(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();return e,me
def mesh_stats(o):
    e,me=evaluated(o);b=bmesh.new();b.from_mesh(me);b.normal_update()
    coords=[o.matrix_world@v.co for v in me.vertices]
    result={'name':o.name,'type':o.type,'vertices':len(me.vertices),'faces':len(me.polygons),'edges':len(me.edges),'boundary_edges':sum(x.is_boundary for x in b.edges),'non_manifold_edges':sum(not x.is_manifold for x in b.edges),'loose_vertices':sum(not v.link_edges for v in b.verts),'volume_m3_signed':b.calc_volume(signed=True),'modifiers':[m.type for m in o.modifiers],'bounds':{'min':[min(p[i] for p in coords) for i in range(3)],'max':[max(p[i] for p in coords) for i in range(3)]}}
    b.free();e.to_mesh_clear();return result
def world_bvh(o):
    e,me=evaluated(o);me.calc_loop_triangles();pts=[o.matrix_world@v.co for v in me.vertices];tri=[tuple(t.vertices) for t in me.loop_triangles];tree=BVHTree.FromPolygons(pts,tri,all_triangles=True,epsilon=0.0);e.to_mesh_clear();return tree

bpy.context.view_layer.update()
geometry=[o for o in parts.objects if o.type in {'MESH','CURVE'}]
topology=[mesh_stats(o) for o in geometry]
print('FG16_NATIVE_TOPOLOGY',json.dumps(topology),flush=True)
# Record contacts honestly. Expected pair labels do not override observed overlap.
expected_contacts={frozenset(pair):reason for pair,reason in [
    (['FG16_01_Colorless_smooth_glass','FG16_03_Sealing_ring'],'Glass edge/gasket seat; fitted seal compression, not calibrated'),
    (['FG16_02_Independent_front_rim','FG16_03_Sealing_ring'],'Rim clamps gasket; fitted seal compression'),
    (['FG16_03_Sealing_ring','FG16_05_Hollow_optical_element'],'Gasket/optical-element seat; uncalibrated'),
    (['FG16_02_Independent_front_rim','FG16_06_Hollow_curved_body'],'Rim/housing retaining interface; fitted'),
    (['FG16_04_Lamp_glass','FG16_04_Lamp_metal_base'],'Bulb envelope to mounting base; attachment seam'),
    (['FG16_04_Lamp_metal_base','FG16_07_Cap_base'],'Bulb cap seat in lamp base; contact geometry approximate'),
    (['FG16_05_Hollow_optical_element','FG16_07_Cap_base'],'Optical bowl central cap interface; approximate'),
    (['FG16_07_Cap_base','FG16_08_Wiring_route_envelope'],'Wiring enters cap, route envelope only'),
]}
trees={o.name:world_bvh(o) for o in geometry}
contacts=[]
for a,b in itertools.combinations(geometry,2):
    hits=trees[a.name].overlap(trees[b.name]);key=frozenset([a.name,b.name])
    if hits or key in expected_contacts:
        contacts.append({'a':a.name,'b':b.name,'surface_triangle_pairs':len(hits),'intended_interface':expected_contacts.get(key),'classification':'INTENDED_ASSEMBLY_INTERFACE_REQUIRES_CALIBRATION' if key in expected_contacts else 'UNRESOLVED_SURFACE_INTERSECTION'})

# Axis test includes out-of-range values, establishing actual constraint response.
axis=[]
for angle in [-210,-170,-90,0,90,170,210]:
    yaw['azimuth_deg']=float(angle);yaw.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update()
    ev=yaw.evaluated_get(bpy.context.evaluated_depsgraph_get())
    actual=math.degrees(ev.matrix_world.to_euler().z)
    axis.append({'input_deg':angle,'evaluated_deg':actual,'expected_deg':max(-170,min(170,angle))})
yaw['azimuth_deg']=0.;yaw.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update()
axis_pass=all(abs(r['evaluated_deg']-r['expected_deg'])<1e-4 for r in axis)

report={'scope':'Independent structural study only; all 16 gates OPEN','blender_version':bpy.app.version_string,'production_sha256_before':before,'production_three_parts_geometry_before':production_geometry,'source':SOURCE,'source_image_sha256':sha(REF/'1977-original-p216-217.png'),'topology':topology,'contacts':contacts,'contact_audit_limit':'Triangle surface overlaps only; full containment and physical seal compression are not certified. Named interfaces are identified, never waived into a general pass. Fitted bench and unsupported screw installation are excluded from a vehicle assembly acceptance.','horizontal_axis':axis,'horizontal_axis_pass':axis_pass,'unresolved':['All metric geometry and material parameters fitted','Original support/yoke, vertical pivot, cab control linkage and vertical stops not reconstructed','Fastening screw shape/axis and installed contact remain unresolved','No calibrated seal compression, optical prescription or electrical circuit','No in-vehicle motion/clearance/AO/browser/installed-height acceptance']}
(OUT/'native-audit-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

# Preserve assembled editable master first. All rendering cuts are in a duplicate scene.
bpy.ops.object.select_all(action='DESELECT');housing.select_set(True);bpy.context.view_layer.objects.active=housing
for area_ui in bpy.context.screen.areas:
    if area_ui.type=='VIEW_3D':
        area_ui.spaces.active.region_3d.view_distance=.6
        area_ui.spaces.active.region_3d.view_location=(0,0,.2)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FG16_Native_Structural_Study.blend'),compress=True)
scene.render.filepath=str(OUT/'cycles-assembled.png');bpy.ops.render.render(write_still=True)

# Scene duplication keeps the source assembly editable and unaffected by display cuts.
bpy.ops.scene.new(type='FULL_COPY');section=bpy.context.scene;section.name='FG16_SECTION_PRESENTATION'
section.camera=bpy.data.objects.get('CAMERA_SECTION.001') or secam
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-.5,.3));cutter=bpy.context.object;cutter.name='SECTION_TOOL_REMOVE_Y_NEGATIVE';cutter.dimensions=(2,1,2);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);cutter.hide_render=True;cutter.hide_set(True);cutter.display_type='WIRE'
section_names=['FG16_01_Colorless_smooth_glass','FG16_02_Independent_front_rim','FG16_03_Sealing_ring','FG16_05_Hollow_optical_element','FG16_06_Hollow_curved_body']
for o in section.objects:
    if o.type=='MESH' and any(o.name.startswith(n) for n in section_names) and '_PROFILE' not in o.name:
        m=o.modifiers.new('Presentation half-section, not manufactured cut','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
for o in section.objects:
    if o.name.startswith('LABEL_'):
        o.parent=section.camera
        if o.name.startswith('LABEL_title'):o.data.body='FG16  |  HALF SECTION STUDY';o.location=(-.239,.187,-.2)
        else:o.location=(-.239,-.194,-.2)
section.render.filepath=str(OUT/'cycles-section.png');bpy.ops.render.render(write_still=True)
# Save both explicitly labeled scenes, reopen default scene assembled.
bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FG16_Native_Structural_Study.blend'),compress=True)
after={str(p.relative_to(ROOT)):sha(p) for p in PRODUCTION}
assert before==after
report['production_sha256_after']=after;report['production_files_byte_unchanged']=True
report['render_engine']='Cycles CPU, 64 samples, actual Blender renders'
report['rendered_views']=['cycles-assembled.png','cycles-section.png']
(OUT/'native-audit-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('FG16_STUDY_COMPLETE',json.dumps({'blend':str(OUT/'FG16_Native_Structural_Study.blend'),'axis_pass':axis_pass,'unresolved_intersections':[r for r in contacts if r['classification'].startswith('UNRESOLVED')]}),flush=True)

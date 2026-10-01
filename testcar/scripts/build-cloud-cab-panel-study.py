"""Independent, native-modifier cab-panel layout study; never opens a vehicle master.

Run with official Blender 4.5.13, --background --threads 4 --python this.py.
The source scans are hashed for provenance only: no source pixels enter Blender.
"""
import bpy
import math
import json
import hashlib
import sys
import argparse
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / 'testcar/outputs/cloud-cab-panel-study-20261001'
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=DEFAULT)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT = args.output.resolve()
OUT.mkdir(parents=True, exist_ok=True)
if (OUT / 'study.blend').exists():
    raise RuntimeError('Refusing to overwrite retained study.blend; use a new revision directory.')

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene['status'] = 'INDEPENDENT FITTED STUDY; NOT INSTALLED; ALL 16 ACCEPTANCE GATES OPEN'
scene['factory_dimensions'] = False
scene['electrical_or_mechanical_simulation'] = False
scene['source_images_loaded_or_packed'] = False
scene['study_axes'] = 'XY panel plane; +Z outward; display separation is not vehicle installation'
scene['builder'] = str(Path(__file__).relative_to(ROOT))

def coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

LEFT = coll('01 LEFT CAB — Fig101 layout study')
RIGHT = coll('02 RIGHT CAB — Fig102 auxiliary panel')
SOURCES = coll('90 EDITABLE SOURCE CURVES — hidden')
CUTLEFT = coll('91 LEFT THROUGH-HOLE CUTTERS — hidden')
CUTRIGHT = coll('92 RIGHT THROUGH-HOLE CUTTERS — hidden')
CUTAUX = coll('93 AUXILIARY BOOLEAN CUTTERS — hidden')
REVIEW = coll('95 REVIEW LABELS — not factory markings')
STAGING = coll('99 REVIEW CAMERA AND LIGHTS')
objects = []
holes = []
solids = []
sources = []
instruments = []

def material(name, color, metal=0.0, rough=.4, transmission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Transmission Weight'].default_value = transmission
    m['evidence_status'] = 'FITTED DISPLAY MATERIAL — source drawing does not establish finish'
    return m

PAINT = material('FITTED muted olive panel enamel', (.12,.145,.09), .28,.36)
BLACK = material('FITTED charcoal housing', (.018,.022,.022), .15,.35)
FACE = material('FITTED uncalibrated dial backing', (.008,.012,.012), 0,.5)
METAL = material('FITTED dull plated bezel', (.27,.29,.27), .7,.26)
GLASS = material('FITTED clear instrument cover', (.72,.8,.75), 0,.12,.92)
IVORY = material('FITTED uncalibrated pointer', (.66,.69,.58), .1,.43)
GRAY = material('FITTED VA180-form gray housing', (.28,.30,.27), .3,.45)
AMBER = material('FITTED indicator proxy glass', (.28,.12,.018), .05,.26)
LABEL = material('Review annotation cream', (.72,.78,.7), 0,.65)

def put(o, collection, parent=None):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    collection.objects.link(o)
    if parent:
        o.parent = parent
    return o

def meta(o, role, collection, parent=None, solid=False, **kw):
    put(o, collection, parent)
    o['role'] = role
    o['dimension_status'] = 'FITTED'
    o['geometry_status'] = 'PROXY / UNDIMENSIONED SOURCE LAYOUT'
    o['installed_in_vehicle'] = False
    for k,v in kw.items():
        o[k] = v if isinstance(v,(str,int,float,bool)) else json.dumps(v, ensure_ascii=False)
    objects.append(o.name)
    if solid:
        o['claimed_closed_solid'] = True
        solids.append(o.name)
    return o

def empty(name, collection, location=(0,0,0), **kw):
    o = bpy.data.objects.new(name,None)
    collection.objects.link(o)
    o.location = location
    o.empty_display_size = .03
    o.empty_display_type = 'PLAIN_AXES'
    for k,v in kw.items(): o[k]=v
    return o

LP = empty('LEFT DISPLAY ROOT — not vehicle datum',LEFT,(-.245,0,0))
RP = empty('RIGHT DISPLAY ROOT — not vehicle datum',RIGHT,(.49,.018,0))
LS = .88 / (1148-282)
RS = .335 / (632-261)
def lp(x,y,z=0): return ((x-715)*LS,(1183-y)*LS,z)
def rp(x,y,z=0): return ((x-447)*RS,(344-y)*RS,z)

def bevel(o, width=.0005, segments=3):
    m=o.modifiers.new('Native engineering edge bevel','BEVEL')
    m.width=width; m.segments=segments
    m.limit_method='ANGLE'
    return m

def cylinder(name,r,depth,loc,collection,parent,mat=BLACK,verts=64,role='fitted separate proxy body'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, end_fill_type='NGON', location=(0,0,0))
    o=bpy.context.object; o.name=name; o.location=loc
    meta(o,role,collection,parent,solid=True)
    o.data.materials.append(mat)
    bevel(o,min(.00045,r*.05,depth*.16),3)
    return o

def cube(name,size,loc,collection,parent,mat=BLACK,edge=.0004,role='fitted separate proxy body'):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.object; o.name=name
    o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.location=loc
    meta(o,role,collection,parent,solid=True)
    o.data.materials.append(mat)
    if edge: bevel(o,edge,3)
    return o

def curve_surface(name, coords, thick, collection, parent, mat, role, keep_source=True):
    # Author a native 2D POLY curve, convert with Blender's operator, retain source.
    # There is deliberately no manual mesh creation/from_pydata/bmesh construction.
    cu=bpy.data.curves.new(name+' editable 2D contour','CURVE')
    cu.dimensions='2D'; cu.fill_mode='BOTH'; cu.resolution_u=12
    sp=cu.splines.new('POLY'); sp.points.add(len(coords)-1)
    for p,co in zip(sp.points,coords): p.co=(*co,0,1)
    sp.use_cyclic_u=True
    o=bpy.data.objects.new(name,cu); collection.objects.link(o)
    if keep_source:
        src=o.copy(); src.data=cu.copy(); src.name=name+' SOURCE CURVE'
        SOURCES.objects.link(src); src.parent=parent
        src.hide_render=True; src.hide_set(True)
        src['role']='editable native source curve'; src['dimension_status']='FITTED'
        sources.append(src.name)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target='MESH')
    o=bpy.context.object
    meta(o,role,collection,parent,solid=True)
    o.data.materials.append(mat)
    m=o.modifiers.new('Native sheet thickness — FITTED','SOLIDIFY')
    m.thickness=thick; m.offset=0; m.use_even_offset=True
    return o

def arc_strip(name,cx,cy,r0,r1,start,end,z,collection,parent,mat):
    n=36
    angles=[math.radians(start+(end-start)*i/n) for i in range(n+1)]
    pts=[(cx+r1*math.cos(a),cy+r1*math.sin(a)) for a in angles]
    pts += [(cx+r0*math.cos(a),cy+r0*math.sin(a)) for a in reversed(angles)]
    o=curve_surface(name,pts,.002,collection,parent,mat,'observed arc silhouette, fitted profile',False)
    o.location.z=z; bevel(o,.00035,2)
    return o

def torus(name,r,minor,loc,collection,parent,mat=METAL):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=minor,major_segments=64,minor_segments=12)
    o=bpy.context.object; o.name=name; o.location=loc
    meta(o,'native toroidal bezel proxy',collection,parent,solid=True)
    o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth=True
    return o

def cutter(name,x,y,r,plate,collection,parent):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=.18)
    o=bpy.context.object; o.name=name; o.location=(x,y,0)
    put(o,collection,parent)
    o.hide_render=True; o.hide_set(True); o.display_type='WIRE'
    o['role']='native Boolean through-hole cutter'; o['dimension_status']='FITTED'
    h={'id':name,'plate':plate,'center_local_m':[x,y], 'radius_m':r,
       'dimension_status':'FITTED','cutter':o.name}
    holes.append(h)
    return o

def subtract_collection(o,collection):
    m=o.modifiers.new('Actual openings — retained native Boolean operands','BOOLEAN')
    m.operation='DIFFERENCE'; m.solver='EXACT'; m.operand_type='COLLECTION'; m.collection=collection
    return m

# A traced, undimensioned contour. Pixel coordinates are in review planes, not
# asserted factory drawing coordinates. The scans themselves contain no dimensions.
left_outline=[(282,1357),(285,1024),(289,1015),(296,1010),(648,1012),
              (650,1037),(650,1058),(654,1074),(665,1085),(680,1091),
              (699,1094),(716,1090),(731,1080),(741,1066),(744,1048),
              (744,1013),(1023,1015),(1024,1184),(1146,1315),(1148,1348),
              (981,1351),(967,1370),(291,1370)]
# The lower shallow return is visible in Fig101. It is represented in the flat
# contour only; its unknown fold, true bend radius and mounting relation stay open.
left=curve_surface('LEFT PANEL — real openings / fitted silhouette', [lp(x,y)[:2] for x,y in left_outline], .003,LEFT,LP,PAINT,'fitted panel plate')
left['source']='1977 Fig101 pp174–175'
left['unknowns']='true dimensions, fold geometry, installed attitude, rear brackets, hardware, thickness'

right_outline=[(263,544),(261,158),(266,148),(617,141),(617,196),
               (624,280),(631,356),(628,404),(619,503),(617,538)]
right=curve_surface('RIGHT PANEL — real openings / fitted silhouette', [rp(x,y)[:2] for x,y in right_outline], .003,RIGHT,RP,PAINT,'fitted auxiliary panel plate')
right['source']='1977 Fig102 p176'
right['unknowns']='true dimensions, folded return, installed attitude, rear mounts, hardware, thickness'

CAPTIONS={56:'speedometer',57:'pneumatic air pressure',58:'engine tachometer',59:'coolant temperature',60:'engine oil pressure',61:'engine oil temperature',62:'gearbox lubrication pressure',63:'voltammeter',64:'fan switch',65:'fuel level',66:'gearbox oil temperature',67:'gearbox boosters oil pressure',68:'converter oil temperature',69:'converter outlet oil pressure',70:'engine running hours'}
layout=[
 ('A1',58,347,1078,34,False,'round_pointer'),
 ('A2',59,432,1078,32,True,'round_pointer'),
 ('A3',61,519,1078,32,True,'round_pointer'),
 ('A4',63,608,1078,32,True,'pressure_style_unassigned'),
 ('A5',66,785,1078,32,True,'round_pointer'),
 ('A6',68,875,1078,32,True,'round_pointer'),
 ('A7',70,960,1082,32,False,'counter_window_unmarked'),
 ('B1',57,355,1188,42,False,'speedometer_style_unassigned'),
 ('B2',60,451,1188,31,True,'round_pointer'),
 ('B3',62,540,1188,31,True,'round_pointer'),
 ('B4',64,627,1188,32,False,'VA180_style_inference_unassigned'),
 ('B5',65,715,1188,31,False,'round_pointer'),
 ('B6',67,802,1188,31,True,'round_pointer'),
 ('B7',69,890,1188,31,True,'round_pointer'),
]

def pointer(name,x,y,r,angle,collection,parent,z=.0105):
    # Angle is only an undimensioned observed silhouette fit, never a reading.
    a=math.radians(angle)
    ux,uy=math.cos(a),math.sin(a); vx,vy=-uy,ux
    pts=[(x-ux*r*.13+vx*r*.07,y-uy*r*.13+vy*r*.07),
         (x+ux*r*.72,y+uy*r*.72),
         (x-ux*r*.13-vx*r*.07,y-uy*r*.13-vy*r*.07)]
    o=curve_surface(name,pts,.0006,collection,parent,IVORY,'uncalibrated pointer silhouette',False)
    o.location.z=z; o['reading']='NONE — uncalibrated display proxy'
    cylinder(name+' pivot',r*.085,.0014,(x,y,z+.0004),collection,parent,BLACK,32)
    return o

for index,(slot,leader,px,py,pr,eyebrow,kind) in enumerate(layout):
    x,y,_=lp(px,py); r=pr*LS
    mount_r=r*.865
    cutter('L-HOLE-'+slot,x,y,mount_r+.0007,left.name,CUTLEFT,LP)
    assembly=empty('LEFT '+slot+' / drawing leader '+str(leader),LEFT)
    assembly.parent=LP
    assembly['physical_slot_id']=slot
    assembly['drawing_leader']=leader
    assembly['caption_function_id']=leader
    assembly['caption_function_text']=CAPTIONS[leader]
    assembly['assignment_status']='UNRESOLVED CAPTION / DRAWING CONFLICT' if slot in ('A4','B1','B4') else 'caption and physical leader recorded separately'
    assembly['observed_silhouette']=kind
    assembly['factory_dimensions']=False
    assembly['calibrated_scale']=False
    assembly['actual_internal_mechanism']='UNKNOWN; not modeled'
    body=cylinder('LEFT '+slot+' separate rear body',mount_r,.036,(x,y,-.016),LEFT,assembly,BLACK)
    body['axial_depth_status']='FITTED, not device drawing'
    # VA180 supplementary image supports shape only, not exact identity/scale.
    face_mat=GRAY if slot=='B4' else FACE
    cylinder('LEFT '+slot+' blank face',r*.91,.002,(x,y,.007),LEFT,assembly,face_mat)
    torus('LEFT '+slot+' independent bezel',r*.945,r*.052,(x,y,.0075),LEFT,assembly,GRAY if slot=='B4' else METAL)
    if kind in ('counter_window_unmarked','speedometer_style_unassigned'):
        cube('LEFT '+slot+' empty counter window',(r*1.04,r*.22,.0008),(x,y+r*.30,.0085),LEFT,assembly,IVORY,.0002,'unmarked observed counter-window proxy')
        # Empty dark inset: no fabricated digits, units or capacity labels.
        cube('LEFT '+slot+' counter aperture proxy',(r*.96,r*.155,.0006),(x,y+r*.30,.009),LEFT,assembly,FACE,.00015)
    if slot=='B4':
        arc_strip('LEFT B4 uncalibrated arc-window silhouette',x,y-r*.20,r*.30,r*.80,20,160,.009,LEFT,assembly,FACE)
        cylinder('LEFT B4 observed lower-button proxy',r*.13,.005,(x+r*.35,y-r*.73,.011),LEFT,assembly,BLACK,32)
    if slot!='A7':
        pointer('LEFT '+slot+' uncalibrated pointer',x,y,r,52 if slot=='A1' else 140,LEFT,assembly)
    cylinder('LEFT '+slot+' separate cover glass',r*.875,.0012,(x,y,.0122),LEFT,assembly,GLASS)
    if eyebrow:
        arc_strip('LEFT '+slot+' observed upper arch proxy',x,y,r*1.17,r*1.33,25,155,.006,LEFT,assembly,BLACK)
    instruments.append({'slot_id':slot,'drawing_leader':leader,'caption_function_id':leader,
        'caption_function':CAPTIONS[leader],'source_review_plane_xy':[px,py],
        'source_review_plane_radius':pr,'center_local_m':[x,y],'fitted_face_radius_m':r,
        'visual_kind':kind,'mapping_conflict':slot in ('A4','B1','B4'),
        'root_object':assembly.name,'scale_graduations':'NOT MODELED','dimension_status':'FITTED'})

def simple_control(key,px,py,pr,kind,which='L',caption=None):
    proj,parent,collection,cut,plate=(lp,LP,LEFT,CUTLEFT,left) if which=='L' else (rp,RP,RIGHT,CUTRIGHT,right)
    s=LS if which=='L' else RS
    x,y,_=proj(px,py); r=pr*s
    root=empty(which+' '+key+' control assembly',collection); root.parent=parent
    root['physical_position_id']=key
    root['observed_proxy_kind']=kind
    root['caption_assignment']=caption or 'UNKNOWN — physical silhouette only'
    root['dimension_status']='FITTED'
    cr=r*.43 if kind not in ('socket','indicator','fuse') else r*.72
    cutter(which+'-HOLE-'+key,x,y,cr+.0006,plate.name,cut,parent)
    cylinder(which+' '+key+' separate rear body',cr,.020,(x,y,-.008),collection,root,BLACK,48)
    cylinder(which+' '+key+' front base',r,.003,(x,y,.0035),collection,root,METAL,48)
    if kind=='socket':
        cylinder(which+' '+key+' socket blank face',r*.84,.004,(x,y,.006),collection,root,BLACK,48)
        # Contact internals/pin pattern is deliberately not fabricated.
        torus(which+' '+key+' socket rim',r*.88,r*.09,(x,y,.008),collection,root,METAL)
    elif kind=='indicator':
        cylinder(which+' '+key+' indicator proxy',r*.70,.005,(x,y,.007),collection,root,AMBER,48)
    elif kind=='fuse':
        cylinder(which+' '+key+' fuse button',r*.70,.006,(x,y,.007),collection,root,BLACK,48)
    else:
        cylinder(which+' '+key+' observed hexagonal mount',r*.61,.004,(x,y,.007),collection,root,GRAY,6)
        cube(which+' '+key+' switch or button silhouette',(r*.39,r*.84,.010),(x,y,.012),collection,root,BLACK,min(.001,r*.15))
    return root

# Six small between-row circles are visible but lack unambiguous leaders in this
# scan: do not assign them a control function or electrical state.
for i,(x,y) in enumerate([(387,1119),(473,1122),(561,1122),(668,1125),(832,1127),(922,1129)],1):
    simple_control('M'+str(i),x,y,12,'indicator')

# Lower physical silhouettes. Unresolved leader assignments are intentionally
# absent rather than silently transferred from visually adjacent caption text.
lower=[
 ('C01',353,1266,10,'fuse'),('C02',353,1292,10,'indicator'),('C03',353,1319,10,'indicator'),
 ('C04',395,1268,10,'fuse'),('C05',443,1268,10,'fuse'),
 ('C06',494,1262,19,'switch'),('C07',539,1263,19,'switch'),('C08',585,1263,19,'switch'),
 ('C09',632,1265,19,'switch'),('C10',679,1266,19,'switch'),('C11',726,1269,19,'switch'),
 ('C12',395,1317,18,'switch'),('C13',443,1317,18,'switch'),('C14',551,1311,22,'switch'),
 ('C15',616,1316,8,'fuse'),('C16',677,1316,8,'fuse'),('C17',738,1316,8,'fuse'),
 ('C18',801,1316,8,'switch'),('C19',869,1317,18,'switch'),('C20',873,1267,20,'switch'),
 ('C21',919,1316,20,'switch'),('C22',976,1315,9,'fuse'),('C23',1036,1316,23,'socket'),
 ('C24',1072,1285,9,'switch'),('C25',1023,1258,18,'switch'),('C26',987,1182,18,'indicator')]
for key,x,y,r,kind in lower:
    root=simple_control(key,x,y,r,kind)
    if key=='C01':
        root['drawing_leader']=56
        root['caption_conflict']='Fig101 caption56 says speedometer, but drawing56 points to small control here'

# Right Fig102: eight caption functions, with two physical thermal fuses (6a/6b).
right_positions=[
 ('R1',457,379,23,'switch','Fig102:1 fan switch'),
 ('R2',440,466,25,'switch','Fig102:2 water-heater switch'),
 ('R3',377,466,25,'switch','Fig102:3 cab ceiling-light switch'),
 ('R4',313,466,25,'switch','Fig102:4 panel illumination switch'),
 ('R5',326,280,30,'socket','Fig102:5 plug socket'),
 ('R6a',328,380,12,'fuse','Fig102:6 thermal fuse, left'),
 ('R6b',392,380,12,'fuse','Fig102:6 thermal fuse, right'),
 ('R8',500,288,26,'switch','Fig102:8 driver-signal button')]
for key,x,y,r,kind,caption in right_positions:
    simple_control(key,x,y,r,kind,'R',caption)

# The large upper centre circle is a task lamp (caption7), never an engine dial.
x,y,_=rp(421,231); r=59*RS
lamp=empty('RIGHT R7 TASK LAMP — not an instrument',RIGHT); lamp.parent=RP
lamp['caption_function']='Fig102:7 task lamp'; lamp['dimension_status']='FITTED'
lamp['internal_optics_and_switching']='UNKNOWN; no light/electrical simulation'
cutter('R-HOLE-R7',x,y,r*.65,right.name,CUTRIGHT,RP)
cylinder('RIGHT R7 fitted rear lamp body',r*.63,.028,(x,y,-.011),RIGHT,lamp,BLACK)
cylinder('RIGHT R7 dark reflector proxy',r*.93,.003,(x,y,.005),RIGHT,lamp,GRAY)
torus('RIGHT R7 task-lamp rolled rim',r*.95,r*.052,(x,y,.007),RIGHT,lamp,METAL)
# Native scaled UV sphere gives a shallow lens-envelope proxy. Its optical
# profile and actual lens section are unknown; this is not an optical model.
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=24,radius=1)
dome=bpy.context.object; dome.name='RIGHT R7 shallow lamp lens proxy'
dome.scale=(r*.88,r*.88,r*.24)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
dome.location=(x,y,.007)
meta(dome,'fitted shallow task lamp lens; no optical prescription',RIGHT,lamp,solid=True)
dome.data.materials.append(GLASS)
for p in dome.data.polygons: p.use_smooth=True
# A simple bell-shaped shield outline follows the drawing, without invented guts.
shieldpts=[(x-r*.18,y+r*.18),(x-r*.22,y-r*.17),(x-r*.34,y-r*.51),
           (x-r*.51,y-r*.66),(x+r*.51,y-r*.66),(x+r*.34,y-r*.51),
           (x+r*.22,y-r*.17),(x+r*.18,y+r*.18)]
shield=curve_surface('RIGHT R7 observed bell-form shield proxy',shieldpts,.0015,RIGHT,lamp,PAINT,'source-observed inner silhouette / fitted flat shield',False)
shield.location.z=.009; bevel(shield,.001,3)

# The tall right-hand strip with two oblong openings is drawn but not identified
# by a figure leader. Keep it separately editable and explicitly unidentified.
strippts=[rp(x,y)[:2] for x,y in [(543,504),(542,215),(549,210),(547,188),(586,188),(588,504)]]
strip=curve_surface('RIGHT UNIDENTIFIED VERTICAL STRIP — fitted',strippts,.002,RIGHT,RP,PAINT,'observed strip; purpose unknown')
strip.location.z=.005
slotcollection=coll('94 RIGHT STRIP SLOT CUTTERS — hidden')
for n,sy in enumerate([277,422],1):
    sx,yy,_=rp(565,sy)
    cut=cube('RIGHT STRIP oblong cutter '+str(n),(.024,.011,.06),(sx,yy,.005),slotcollection,RP,BLACK,.005,'Boolean strip slot cutter')
    cut.hide_render=True; cut.hide_set(True); cut.display_type='WIRE'
    cut['claimed_closed_solid']=False; solids.remove(cut.name)
    holes.append({'id':cut.name,'plate':strip.name,'center_local_m':[sx,yy],
       'radius_m':.0035,'dimension_status':'FITTED oblong opening','cutter':cut.name})
subtract_collection(strip,slotcollection); bevel(strip,.0004,3)

subtract_collection(left,CUTLEFT); bevel(left,.0005,3)
subtract_collection(right,CUTRIGHT); bevel(right,.0005,3)

# Discrete metadata labels are review aids, not decals or reconstructed printing.
def text_label(name,text,loc,size):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=text; cu.size=size
    cu.align_x='CENTER'; cu.align_y='CENTER'; cu.extrude=0
    o=bpy.data.objects.new(name,cu); REVIEW.objects.link(o); o.location=loc
    cu.materials.append(LABEL)
    o['role']='REVIEW ANNOTATION — NOT FACTORY MARKING'
    return o

text_label('LEFT review title','LEFT CAB / Fig.101',(-.245,.230,.002),.017)
text_label('RIGHT review title','RIGHT CAB / Fig.102',(.49,.230,.002),.017)
text_label('Scope review note','FITTED LAYOUT STUDY  |  UNCALIBRATED PROXIES  |  NOT INSTALLED',(.03,-.253,.002),.012)
for item in instruments:
    x,y=item['center_local_m']
    text_label('Slot '+item['slot_id'],item['slot_id'],(x+LP.location.x,y-.046,.021),.007)
REVIEW.hide_render=True

def camera(name,loc,target,ortho):
    d=bpy.data.cameras.new(name); o=bpy.data.objects.new(name,d); STAGING.objects.link(o)
    o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.type='ORTHO'; d.ortho_scale=ortho; d.lens=50
    return o

scene.camera=camera('REVIEW FRONT ORTHOGRAPHIC',(.025,0,2.2),(.025,0,0),1.38)
camera('REVIEW REAR ORTHOGRAPHIC',(.025,0,-2.2),(.025,0,0),1.38)
camera('REVIEW OBLIQUE',(.035,-1.15,1.8),(.025,0,0),1.36)
for name,loc,power,size in [('Review key',(-.7,.6,1.5),140,1.4),('Review fill',(.8,.1,.9),70,.9)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);STAGING.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Neutral study world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.075,.065,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.resolution_x=2200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'

src_dir=ROOT/'testcar/work/cloud-cab-reference-20261001'
def shafile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
registry={
 'study':'MAZ543A cab panels — independent fitted native layout study',
 'status':'NOT INSTALLED; no promotion; all 16 whole-vehicle acceptance gates OPEN',
 'scope':'Two panel silhouettes, through-holes, separate instrument/control proxy bodies; no calibrated instrument faces or functional simulation',
 'sources':[
   {'id':'M1977-F101','title':'MAZ543 technical description, 1977, Fig101, pp174–175',
    'url':'https://djvu.online/file/zjMdLY3MFjmTL','local_research_file':'testcar/work/cloud-cab-reference-20261001/p174-175.png',
    'sha256':shafile(src_dir/'p174-175.png'),'pixels_inspected':True,'pixels_embedded':False,
    'observed':'14 circular instrument positions, 2 rows of7; central upper U cutout; asymmetric lower/right extension; numerous smaller control silhouettes',
    'source_review_plane':[1376,1818], 'scan_native_pixels':[3327,4397],
    'limits':'Undimensioned scan, fitted projected layout, not metrology or a factory fabrication drawing'},
   {'id':'M1977-F102','title':'MAZ543 technical description, 1977, Fig102, p176',
    'url':'https://djvu.online/file/zjMdLY3MFjmTL','local_research_file':'testcar/work/cloud-cab-reference-20261001/p176-177.png',
    'sha256':shafile(src_dir/'p176-177.png'),'pixels_inspected':True,'pixels_embedded':False,
    'source_review_plane':[1818,1376],'scan_native_pixels':[4397,3327],
    'observed':'Auxiliary controls, two thermal fuses, large task lamp; no engine-gauge cluster; tall unidentified two-slot strip',
    'limits':'Undimensioned, no scale transfer between left/right figures; right width is independently fitted'},
   {'id':'VA180-supplement','local_research_file':'testcar/work/cloud-cab-reference-20261001/va180-direct-device-photo.jpg',
    'url':'https://zapadpribor.com/va-180/',
    'image_url':'https://zapadpribor.com/static/images/catalog/8330/800x600/va-180-photo-1.jpg',
    'sha256':shafile(src_dir/'va180-direct-device-photo.jpg'),'pixels_inspected':True,'pixels_embedded':False,
    'observed':'Gray round housing, upper arcuate window, lower button',
    'inference':'B4 drawing silhouette resembles VA180; this does not reconcile manual leader64 with caption64 fan switch',
    'unknown':'Photographed rating/version, exact1977 vehicle compatibility and physical dimensions unverified'},
   {'id':'DTF-removed-panel','url':'https://dtf.ru/snowrunner/4141704-snowrunner-sravnenie-zikz-612h-s-maz-543',
    'local_research_file':'testcar/work/cloud-cab-reference-20261001/dtf-panel-explanation.webp',
    'sha256':shafile(src_dir/'dtf-panel-explanation.webp'),'pixels_inspected':True,'pixels_embedded':False,
    'attribution':'WolfPRo article; original photographer not established',
    'observed':'Removed physical panel; lower-left speedometer-like face with odometer, lower-middle VA180-like face/button, upper-middle pressure-style face; upper-left instrument absent',
    'limits':'Vehicle variant/year unknown; flat upper edge differs from original1977 U cutout. Shape corroboration only, not factory layout or dimensional standard.'},
   {'id':'DTF-installed-panel','url':'https://dtf.ru/snowrunner/4141704-snowrunner-sravnenie-zikz-612h-s-maz-543',
    'local_research_file':'testcar/work/cloud-cab-reference-20261001/dtf-switch-placement.webp',
    'sha256':shafile(src_dir/'dtf-switch-placement.webp'),'pixels_inspected':True,'pixels_embedded':False,
    'observed':'Lower controls visible beside column-mounted mechanical parts and pipes',
    'limits':'Vehicle variant/year, exact mounting attitude and adjacent mechanism functions unknown. No pipes or adjacent mechanisms reconstructed in this study.'}],
 'caption_functions':CAPTIONS,
 'physical_instruments':instruments,
 'conflicts':[
    {'drawing_leader':56,'physical_position':'C01 small control','caption':'speedometer','resolution':'OPEN'},
    {'drawing_leader':57,'physical_position':'B1 speedometer-like silhouette','caption':'pneumatic air pressure','resolution':'OPEN'},
    {'drawing_leader':63,'physical_position':'A4 pressure-style silhouette','caption':'voltammeter','resolution':'OPEN'},
    {'drawing_leader':64,'physical_position':'B4 VA180-like silhouette','caption':'fan switch','resolution':'OPEN'}],
 'right_caption_layout':[{'slot':k,'source_review_plane_xy':[x,y],'caption':cap} for k,x,y,r,kind,cap in right_positions]+[
    {'slot':'R7','source_review_plane_xy':[421,231],'caption':'Fig102:7 task lamp, not gauge'}],
 'model_range_data':{'status':'Not independently pixel-checked by this builder; parent researcher has pp29 and218–220 evidence. No calibrated scales were created.'},
 'fitted_parameters':{'left_nominal_review_width_m':.88,'left_thickness_m':.003,'right_nominal_review_width_m':.335,'right_thickness_m':.003,
    'left_review_px_to_m':LS,'right_review_px_to_m':RS,
    'all_hole_centers_and_diameters':'FITTED','all_body_depths':'FITTED','display_separation':'NOT installation','materials':'FITTED DISPLAY'},
 'unknowns':['factory dimensions and tolerance','exact part diameters and rear depths','correct ambiguous caption-to-position mapping',
    'legible scale graduation locations','exact internal mechanisms','electrical connections and causal simulation','original finish/material specification',
    'fasteners and rear mounting construction','panel fold angles and bend radii','true cab installation and clearance'],
 'omissions':['No calibrated graduations, numerals, units or factory markings','No inferred electrical operation or internal mechanism',
    'No mounting fasteners or guessed threads','No claim every left small control is functionally identified','No vehicle installation'],
 'geometry_method':'Blender native primitives and 2D source curves, native convert, Solidify, Boolean, Bevel; no scripted manual mesh construction',
 'source_pixel_policy':'Local research only; no images loaded into Blender or copied to output',
 'supplementary_register':'testcar/reference/cab-panel-supplementary-20261001.json; includes manufacturer SP110-3802010 later catalogue mounting diameter85mm (not bezel), without asserting1977 compatibility',
}
(OUT/'source-registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
manifest={'blender':bpy.app.version_string,'blender_build_hash':bpy.app.build_hash.decode(),
          'study_axes':scene['study_axes'],'panel_objects':[left.name,right.name],
          'auxiliary_plate_objects':[strip.name], 'claimed_closed_solids':solids,
          'source_curves':sources,'through_holes':holes,'instrument_roots':[x['root_object'] for x in instruments],
          'left_main_instrument_count':len(instruments),'left_control_proxy_count':len(lower)+6,
          'right_caption_function_count':8,'right_physical_control_lamp_count':9,
          'rendered':False,'production_opened':False,'all_16_gates':'OPEN'}
(OUT/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
tb=bpy.data.texts.new('READ ME — evidence and limitations')
tb.write(json.dumps({'scope':registry['scope'],'conflicts':registry['conflicts'],'unknowns':registry['unknowns'],
                    'fitted_parameters':registry['fitted_parameters'],'all_16_gates':'OPEN'},indent=2))
# Source scans are deliberately never opened as bpy images or used as textures.
assert not any(im.source=='FILE' or im.packed_file for im in bpy.data.images)
bpy.ops.object.select_all(action='DESELECT')
left.select_set(True);bpy.context.view_layer.objects.active=left
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'study.blend'))
print('CAB_PANEL_STUDY_BUILT',json.dumps({'output':str(OUT),'objects':len(bpy.data.objects),'claimed_solids':len(solids),'holes':len(holes),'instruments':len(instruments)}))

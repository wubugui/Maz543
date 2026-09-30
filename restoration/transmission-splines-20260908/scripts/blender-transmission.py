"""Two coupled planetary rows and four friction packs, MAZ manual figs.42/44.
Tooth counts are ratio-derived; dimensions and installation remain fitted.
"""
import bpy,bmesh,math,json,ast,sys
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cooling_spring_geometry import parameters,vertices,weights
DATA=json.loads((ROOT/'work/transmission/poses.json').read_text());S=DATA['spec']
PROFILES=json.loads((ROOT/'work/transmission/profiles.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
REG=[];root=None
tree=ast.parse((ROOT/'scripts/blender-d12.py').read_text())
names={'C','empty','mat','mesh','prism','box','lathe','cylinder','ring','pipe'}
def tag(o,part,source='',role='internal',**kw):
    o['transmissionPart']=part;o['transmissionRole']=role
    o['sourceId']='MAZ 1973 figs.42/44';o['dimensionStatus']='Ratio-derived tooth counts; fitted dimensions and installation, not factory measurements.'
    REG.append(o.name);return o
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'transmission_helpers','exec'))
root=empty('S543_TRANSMISSION');root['partId']='drive';root['dimensionStatus']='Reconstruction, not factory CAD';root['spec']=json.dumps(S)
STEEL=mat('TX_ground_steel',(.26,.28,.29),.91,.30)
FORGED=mat('TX_forged_steel',(.10,.12,.13),.86,.41)
FRICTION=mat('TX_sintered_friction',(.30,.19,.085),.72,.53)
CAST=mat('TX_cast_housing',(.14,.18,.15),.38,.48)
RUBBER=mat('TX_oil_seals',(.012,.014,.013),.02,.78)
carrier=empty('TX_carrier',root);sun41=empty('TX_sun41',root);sun21=empty('TX_sun21',root)
ring18=empty('TX_ring18',root);ring40=empty('TX_ring40',root)

def extrude_annulus(name,data,lo,hi,parent,material=STEEL):
    pts,caps,n=data['points'],data['caps'],data['outerCount'];count=len(pts)
    vs=[(x,y,z) for x in [lo,hi] for y,z in pts]
    fs=[tuple(reversed(f)) for f in caps]+[tuple(v+count for v in f) for f in caps]
    for start,end in [(0,n),(n,count)]:
        for j in range(start,end):
            k=start+(j-start+1)%(end-start);fs.append((j,k,k+count,j+count))
    return mesh(name,vs,fs,material,parent)

def gear(name,n,lo,hi,parent,bore=.027,internal=False):
    key=next(k for k in PROFILES if S[k]==n)
    o=extrude_annulus(name,PROFILES[key],lo,hi,parent)
    o['teeth']=n;o['gearProfile']='20 degree involute; reconstructed backlash, not factory cutter data'
    return o

gear('TX_41_input_sun',S['sun41'],.028,.071,sun41,bore=.027)
gear('TX_21_reaction_sun',S['sun21'],-.085,-.042,sun21,bore=.032)
gear('TX_18_reverse_ring',S['ring18'],-.085,-.042,ring18,internal=True)
gear('TX_40_first_ring',S['ring40'],.028,.071,ring40,internal=True)
# Stepped coaxial shafts and sleeves with actual through bores.
lathe('TX_15_input_shaft',[(-.285,.015),(-.285,.027),(.030,.027),(.030,.034),(.055,.034),(.055,.015)],(0,0,0),STEEL,sun41,closed=True)
lathe('TX_21_hollow_reaction_sleeve',[(-.230,.028),(-.230,.036),(-.075,.036),(-.075,.046),(-.040,.046),(-.040,.028)],(0,0,0),STEEL,sun21,closed=True)
lathe('TX_28_output_shaft',[(.085,.014),(.085,.038),(.110,.038),(.110,.027),(.290,.027),(.290,.014)],(0,0,0),STEEL,carrier,closed=True)
for x in [-.108,.096]:
    # Annular carrier plates, connected by six machined pin seats.
    ring('TX_carrier_plate_'+str(x),.158,.042,.010,(x,0,0),FORGED,carrier,n=128)
    ring('TX_carrier_hub_'+str(x),.047,.037 if x<0 else .028,.016,(x,0,0),FORGED,carrier,n=96)
for j in range(3):
    a=j*2*pi/3
    for kind,key,r,phi,lo,hi in [('long43','long43',S['longRadius'],a,-.085,.071),('short20','short20',S['shortRadius'],a+S['planetOffset'],-.085,-.042)]:
        parent=empty(f'TX_{kind}_{j}',carrier,(0,r*cos(phi),r*sin(phi)))
        gear(f'TX_{kind}_{j}_teeth',S[key],lo,hi,parent,bore=.013)
        pinroot=empty(f'TX_pin_{kind}_{j}',carrier,(0,r*cos(phi),r*sin(phi)))
        lathe(f'TX_pin_{kind}_{j}_hollow',[(-.113,.005),(-.113,.010),(.103,.010),(.103,.005)],(0,0,0),STEEL,pinroot,closed=True)
        for x in [lo+.009,hi-.009]:
            ring(f'TX_{kind}_{j}_inner_race_{x}',.01035,.010,.009,(x,0,0),STEEL,pinroot)
            ring(f'TX_{kind}_{j}_outer_race_{x}',.013,.01265,.009,(x,0,0),STEEL,parent)
            # Rollers are retained as editable geometry; bearing dynamics pending.
            for k in range(12):
                b=k*2*pi/12;cylinder(f'TX_{kind}_{j}_roller_{x}_{k}',.0011,.007,(x,.0115*cos(b),.0115*sin(b)),STEEL,pinroot,n=10)
        for x in [-.109,.097]:
            ring(f'TX_pin_seat_{kind}_{j}_{x}',.019,.010,.016,(x,0,0),FORGED,pinroot)
    # Carrier webs are shaped annular sectors with a centre bore, no solid disk.
    for x in [-.102,.090]:
        o=box(f'TX_carrier_web_{j}_{x}',(.016,.105,.018),(x,.092,0),FORGED,carrier,edge=.003)
        # Orient the radial web in native coordinates around its own centre.
        o.rotation_euler.x=a

def drum(name,parent,lo,hi,inner,outer):
    return lathe(name,[(lo,inner),(lo,outer),(hi,outer),(hi,inner)],(0,0,0),FORGED,parent,closed=True,n=128)

# Pack counts are sourced; local travel, spring supports and dimensions fitted.
CONTACT=DATA['contact'];SPRINGS={}
def spring_spec(name):
    return dict(releaseSpringLength=CONTACT['springLength'],releaseSpringRadius=CONTACT['springRadius'],
                releaseSpringWire=CONTACT['springWire'],releaseSpringTurns=CONTACT['springTurns'],
                clutchTravel=CONTACT['pistonGap']+(DATA['clutches'][name]['count']-1)*CONTACT['plateGap'])

def coil(name,parent,pack,direction):
    spec=spring_spec(pack);L,R,arc,endR=parameters(spec,0);steps=160;sides=12;faces=[]
    for row in range(steps):
        for j in range(sides):
            k=(j+1)%sides;a=row*sides;b=(row+1)*sides;faces.append((a+j,a+k,b+k,b+j))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple(steps*sides+j for j in range(sides))])
    data=bpy.data.meshes.new(name);data.from_pydata(vertices(spec,L,R,arc,steps,sides),[],faces);data.materials.append(STEEL)
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.parent=parent
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    if direction<0:ob.rotation_euler.y=pi
    for p in data.polygons:p.use_smooth=len(p.vertices)==4
    ob.shape_key_add(name='Basis')
    for key_name,length,radius in [('Pitch',L-spec['clutchTravel'],R),('Radius',L,endR)]:
        key=ob.shape_key_add(name=key_name)
        for point,co in zip(key.data,vertices(spec,length,radius,arc,steps,sides)):point.co=co
    tag(ob,name);ob['springPack']=pack;ob['parametricSpring']=True
    SPRINGS[parent.name]=(ob,spec)

def slotted_drum(name,parent,lo,hi,inner,outer,slotlo,slothi):
    # Eight real pusher slots. No hidden collision exemptions for the tabs.
    if lo<slotlo:drum(name+'_front',parent,lo,slotlo,inner,outer)
    if slothi<hi:drum(name+'_rear',parent,slothi,hi,inner,outer)
    for j in range(8):
        a=j*pi/4+.022;b=(j+1)*pi/4-.022;n=16
        points=[(r*cos(t),r*sin(t)) for r,angles in [(outer,[a+(b-a)*k/n for k in range(n+1)]),(inner,[b-(b-a)*k/n for k in range(n+1)])] for t in angles]
        m=len(points);vs=[(x,y,z) for x in [max(lo,slotlo),min(hi,slothi)] for y,z in points]
        fs=[tuple(reversed(range(m))),tuple(range(m,2*m))]+[(k,(k+1)%m,(k+1)%m+m,k+m) for k in range(m)]
        mesh(name+'_segment_'+str(j),vs,fs,FORGED,parent)

for name,pack in DATA['clutches'].items():
    count,start,ri,ro,direction=[pack[k] for k in ['count','start','inner','outer','direction']]
    driven={'first':ring40,'second':sun21,'direct':sun21,'reverse':ring18}[name]
    stationary=ring18 if name=='direct' else root
    thickness=CONTACT['plateThickness'];pitch=thickness+CONTACT['plateGap']
    travel=spring_spec(name)['clutchTravel']
    pack_start=start if direction==1 else start-(count-1)*pitch
    for j in range(count):
        x=pack_start+j*pitch
        # Alternating steel reaction plates and bronze-coloured sintered plates.
        parent=stationary if j%2==0 else driven
        slider=empty(f'TX_disc_slide_{name}_{j}',parent)
        ring(f'TX_{name}_disc_{j:02}',ro,ri,thickness,(x,0,0),STEEL if j%2==0 else FRICTION,slider,n=128)
    drum(f'TX_{name}_splined_hub',driven,pack_start-.004,pack_start+count*pitch+.003,ri-.007,ri-.001)
    piston=empty('TX_piston_'+name,stationary)
    x=start-direction*.005
    slotted_drum(f'TX_{name}_reaction_drum',stationary,pack_start-.004,pack_start+count*pitch+.004,ro+.001,ro+.008,
                 min(x,x+direction*travel)-.002,max(x,x+direction*travel)+.002)
    profile=[(x-.002,ri-.0005),(x-.002,ro+.0005),(x-.0006,ro+.0005),(x-.0006,ro-.0001),
             (x+.0006,ro-.0001),(x+.0006,ro+.0005),(x+.002,ro+.0005),(x+.002,ri-.0005),
             (x+.0006,ri-.0005),(x+.0006,ri+.0001),(x-.0006,ri+.0001),(x-.0006,ri-.0005)]
    lathe(f'TX_{name}_annular_piston',profile,(0,0,0),FORGED,piston,closed=True,n=128)
    for k,r in enumerate([ri-.0005,ro+.0005]):
        lathe(f'TX_{name}_piston_seal_{k}',[(x+.0005*cos(a*2*pi/16),r+.0005*sin(a*2*pi/16)) for a in range(16)],(0,0,0),RUBBER,piston,closed=True,n=128)
    far=pack_start+(count-1)*pitch if direction==1 else pack_start
    ring(f'TX_{name}_reaction_stop',ro+.008,ri,.002,(far+direction*(thickness/2+.001),0,0),FORGED,stationary,n=128)
    if name!='direct':ring(f'TX_{name}_spring_support_hoop',.245,.230,.003,(x+direction*.024,0,0),FORGED,stationary,n=128)
    for j in range(8):
        a=j*pi/4;r=ro+.014;yz=(r*cos(a),r*sin(a));begin=x+direction*.003;end=x+direction*.021
        mount=empty(f'TX_spring_mount_{name}_{j}',stationary,(begin,*yz));coil(f'TX_{name}_return_spring_{j}',mount,name,direction)
        ring(f'TX_{name}_moving_spring_seat_{j}',.005,.0016,.0015,(begin-direction*.0014,*yz),STEEL,piston,n=32)
        ring(f'TX_{name}_fixed_spring_seat_{j}',.005,.0016,.0015,(end+direction*.0014,*yz),STEEL,stationary,n=32)
        cylinder(f'TX_{name}_spring_guide_{j}',.0012,.033,(x+direction*.0085,*yz),STEEL,stationary,n=16)
        tab=box(f'TX_{name}_pusher_tab_{j}',(.0016,r-ro-.001,.002),(x+direction*.0011,(r+ro-.005)/2,0),FORGED,piston,edge=0)
        tab.rotation_euler.x=a
        # Fixed shoulders react into the stationary housing, or rotating ring18
        # for the direct pack. These supports are a fitted reconstruction.
        if name=='direct':
            cylinder(f'TX_{name}_anchor_{j}',.0025,.014,(end+.009,*yz),FORGED,stationary,n=16)
        else:
            anchor=box(f'TX_{name}_anchor_{j}',(.002,.240-r,.003),(end+direction*.003,(r+.240)/2,0),FORGED,stationary,edge=0);anchor.rotation_euler.x=a
    for j in range(8):
        a=(j+.5)*pi/4
        # Longitudinal keys on reaction drums; disc tooth detail still pending.
        o=box(f'TX_{name}_drum_rib_{j}',(count*.0021+.006,.007,.008),(pack_start+(count-1)*.00105,ro+.007,0),FORGED,stationary,edge=.0005)
        o.rotation_euler.x=a

# Continuous stepped bells connect the geared rings to their clutch hubs while
# passing outside the carrier and inside the fixed reverse reaction drum.
lathe('TX_18_stepped_clutch_bell',[(-.150,.096),(-.150,.168),(-.095,.168),(-.095,.205),(-.084,.205),(-.084,.199),(-.089,.199),(-.089,.162),(-.144,.162),(-.144,.096)],(0,0,0),FORGED,ring18,closed=True,n=160)
lathe('TX_40_stepped_clutch_bell',[(.066,.168),(.066,.182),(.165,.182),(.165,.179),(.175,.179),(.175,.143),(.183,.143),(.183,.137),(.169,.137),(.169,.176),(.072,.176),(.072,.168)],(0,0,0),FORGED,ring40,closed=True,n=160)
ring('TX_21_direct_hub_shoulder',.044,.032,.026,(-.164,0,0),FORGED,sun21,n=96)

# Split inspection housing, end bearing seats, ribs and fasteners.
housing=empty('TX_housing',root)
for x,ri,ro in [(-.250,.040,.245),(.250,.028,.245)]:
    ring('TX_end_cover_'+str(x),ro,ri,.016,(x,0,0),CAST,housing,n=128,role='cover')
    ring('TX_end_bearing_outer_'+str(x),ri+.013,ri+.008,.016,(x,0,0),STEEL,root)
    for k in range(16):
        a=k*2*pi/16
        cylinder(f'TX_cover_fastener_{x}_{k}',.005,.010,(x-.010,(ro-.012)*cos(a),(ro-.012)*sin(a)),STEEL,housing,n=6,role='cover')
for j in range(12):
    a=j*2*pi/12
    o=box(f'TX_housing_rib_{j}',(.500,.015,.011),(0,.240,0),CAST,housing,edge=.002,role='cover');o.rotation_euler.x=a
for side in [-1,1]:box(f'TX_mount_foot_{side}',(.27,.025,.060),(-.04,-.221,side*.152),CAST,housing,edge=.005,role='cover')

# Embed the original references and explicit reconstruction boundaries.
for filename in ['000-0672.jpg','000-3024.jpg','000-3031.jpg','000-0735.jpg']:
    im=bpy.data.images.load(str(ROOT/'work/reference-docs/transmission'/filename));im.pack();im.use_fake_user=True
text=bpy.data.texts.new('TX_READ_ME');text.write('MAZ 1973 figs.42/44. Two coupled rows, common carrier, 15/11/9/15 friction discs. Tooth counts inferred from ratios, dimensions fitted. Neutral turbine speed, hydraulic shifting, bearing rollers, spring/piston contact and casing surface completion remain OPEN.\n')
scene=bpy.context.scene;scene.render.fps=60;scene.frame_start=0;scene.frame_end=600
for sample in DATA['samples']:
    for name,pose in sample['pose'].items():
        ob=bpy.data.objects[name];ob.rotation_euler.x=pose['rx'];ob.keyframe_insert('rotation_euler',frame=sample['frame'])
        if 'p' in pose:ob.location=C(pose['p']);ob.keyframe_insert('location',frame=sample['frame'])
        if name in SPRINGS:
            spring,spec=SPRINGS[name]
            for key,value in zip(['Pitch','Radius'],weights(spec,pose['springTravel'])):
                block=spring.data.shape_keys.key_blocks[key];block.value=value;block.keyframe_insert('value',frame=sample['frame'])
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(0)
for spring,spec in SPRINGS.values():
    for fc in spring.data.shape_keys.animation_data.action.fcurves:
        for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
# Export applied visible geometry while retaining articulated parents.
bpy.ops.object.select_all(action='DESELECT')
for o in list(bpy.data.objects):
    if o.type=='CURVE' or (o.type=='MESH' and not o.data.shape_keys):
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-transmission.glb'),export_format='GLB',export_extras=True,export_animations=False,export_apply=False,export_morph=True,export_draco_mesh_compression_enable=True,export_draco_position_quantization=16)
(ROOT/'outputs/transmission-build.json').write_text(json.dumps({'objects':len(bpy.data.objects),'parts':len(REG),'spec':S,'limits':text.as_string()},indent=2))
print('TRANSMISSION BUILT',len(REG),flush=True)

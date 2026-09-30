"""Two coupled planetary rows and four friction packs, MAZ manual figs.42/44.
Tooth counts are ratio-derived; dimensions and installation remain fitted.
"""
import bpy,bmesh,math,json,ast,sys
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
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
    ring('TX_carrier_hub_'+str(x),.047,.028,.016,(x,0,0),FORGED,carrier,n=96)
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

# Pack topology and disc counts are sourced. The .0021 m plate pitch and
# .0018 m piston stroke are fitted inspection dimensions, not hydraulic results.
packs=[('second',11,-.213,.043,.082,sun21,root,1),
       ('direct',9,-.173,.045,.096,sun21,ring18,1),
       ('reverse',15,-.134,.169,.207,ring18,root,1),
       ('first',15,.206,.144,.179,ring40,root,-1)]
for name,count,start,ri,ro,driven,stationary,direction in packs:
    pack_start=start if direction==1 else start-(count-1)*.0021
    for j in range(count):
        x=pack_start+j*.0021
        # Alternating steel reaction plates and bronze-coloured sintered plates.
        parent=stationary if j%2==0 else driven
        ring(f'TX_{name}_disc_{j:02}',ro,ri,.0018,(x,0,0),STEEL if j%2==0 else FRICTION,parent,n=128)
    drum(f'TX_{name}_reaction_drum',stationary,pack_start-.004,pack_start+count*.0021+.004,ro+.001,ro+.008)
    drum(f'TX_{name}_splined_hub',driven,pack_start-.004,pack_start+count*.0021+.003,ri-.007,ri-.001)
    piston=empty('TX_piston_'+name,stationary)
    x=pack_start-.005 if direction==1 else pack_start+(count-1)*.0021+.005
    ring(f'TX_{name}_annular_piston',ro+.003,ri-.002,.004,(x,0,0),FORGED,piston,n=128)
    for r in [ri-.001,ro+.002]:ring(f'TX_{name}_piston_seal_{r}',r+.0009,r-.0009,.0016,(x,0,0),RUBBER,piston,n=96)
    for j in range(8):
        a=j*2*pi/8;r=(ri+ro)/2
        points=[(x-direction*(.005+.012*k/120),r*cos(a)+.003*cos(k*10*pi/120),r*sin(a)+.003*sin(k*10*pi/120)) for k in range(121)]
        pipe(f'TX_{name}_return_spring_{j}',points,.00065,STEEL,stationary)
    for j in range(18):
        a=j*2*pi/18
        # Longitudinal keys on reaction drums; disc tooth detail still pending.
        o=box(f'TX_{name}_drum_rib_{j}',(count*.0021+.006,.007,.008),(pack_start+(count-1)*.00105,ro+.007,0),FORGED,stationary,edge=.0005)
        o.rotation_euler.x=a

# Continuous stepped bells connect the geared rings to their clutch hubs while
# passing outside the carrier and inside the fixed reverse reaction drum.
lathe('TX_18_stepped_clutch_bell',[(-.150,.096),(-.150,.168),(-.095,.168),(-.095,.205),(-.084,.205),(-.084,.195),(-.089,.195),(-.089,.162),(-.144,.162),(-.144,.096)],(0,0,0),FORGED,ring18,closed=True,n=160)
lathe('TX_40_stepped_clutch_bell',[(.066,.168),(.066,.182),(.165,.182),(.165,.179),(.175,.179),(.175,.137),(.169,.137),(.169,.176),(.072,.176),(.072,.168)],(0,0,0),FORGED,ring40,closed=True,n=160)
ring('TX_21_direct_hub_shoulder',.044,.032,.026,(-.164,0,0),FORGED,sun21,n=96)

# Split inspection housing, end bearing seats, ribs and fasteners.
housing=empty('TX_housing',root)
for x,ri,ro in [(-.250,.040,.221),(.240,.028,.200)]:
    ring('TX_end_cover_'+str(x),ro,ri,.016,(x,0,0),CAST,housing,n=128,role='cover')
    ring('TX_end_bearing_outer_'+str(x),ri+.013,ri+.008,.016,(x,0,0),STEEL,root)
    for k in range(16):
        a=k*2*pi/16
        cylinder(f'TX_cover_fastener_{x}_{k}',.005,.010,(x-.010,(ro-.012)*cos(a),(ro-.012)*sin(a)),STEEL,housing,n=6,role='cover')
for j in range(12):
    a=j*2*pi/12
    o=box(f'TX_housing_rib_{j}',(.490,.015,.011),(-.005,.218,0),CAST,housing,edge=.002,role='cover');o.rotation_euler.x=a
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
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
# Export applied visible geometry while retaining articulated parents.
bpy.ops.object.select_all(action='DESELECT')
for o in list(bpy.data.objects):
    if o.type in {'MESH','CURVE'}:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-transmission.glb'),export_format='GLB',export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=16)
(ROOT/'outputs/transmission-build.json').write_text(json.dumps({'objects':len(bpy.data.objects),'parts':len(REG),'spec':S,'limits':text.as_string()},indent=2))
print('TRANSMISSION BUILT',len(REG),flush=True)

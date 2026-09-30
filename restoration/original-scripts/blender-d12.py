"""Build a source-indexed D12A-525A engine in Blender, independently of the cab.
No imported generic engine mesh is used. Dimensions without a drawing are
explicit reconstruction parameters; see docs/D12_REFERENCE_REGISTER.md.
"""
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi, sqrt
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'))
POSES=json.loads((ROOT/'work'/'d12-poses.json').read_text())
SPEC=POSES['spec']; BETA=pi/6
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
REG=[]
def C(p):return Vector((p[0],-p[2],p[1]))
def empty(name,parent=None,pos=(0,0,0),rx=0):
    ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob)
    ob.parent=parent;ob.location=C(pos);ob.rotation_euler.x=rx;return ob
root=empty('D12A_525A');root['partId']='engine'
root['model']='D12A-525A transport configuration; measured dimensions incomplete'
def mat(name,color,metal,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
    # Physically small machining/casting texture; no baked occlusion on moving parts.
    n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=950
    coord=m.node_tree.nodes.new('ShaderNodeTexCoord');m.node_tree.links.new(coord.outputs['Object'],n.inputs['Vector'])
    bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00008
    m.node_tree.links.new(n.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],b.inputs['Normal'])
    return m
CAST=mat('D12_cast_aluminium',(.26,.285,.27),.75,.47)
PAINT=mat('D12_grey_green_enamel',(.115,.155,.13),.22,.42)
COVER=mat('D12_cover_enamel',(.032,.047,.035),.28,.38)
STEEL=mat('D12_forged_steel',(.13,.145,.15),.88,.33)
POLISH=mat('D12_machined_steel',(.42,.44,.43),.93,.25)
ALLOY=mat('D12_piston_alloy',(.53,.55,.52),.80,.29)
BRONZE=mat('D12_bearing_bronze',(.31,.22,.10),.77,.31)
IRON=mat('D12_exhaust_cast_iron',(.055,.048,.041),.66,.76)
RUBBER=mat('D12_hose_rubber',(.017,.019,.016),.02,.81)
GASKET=mat('D12_gasket',(.029,.031,.027),.1,.88)
GROUPS={}
for name in ['crankcase','cylinder_blocks','cylinder_heads','cam_covers','intake','exhaust','fuel_injection','timing','starting','mounts']:
    GROUPS[name]=empty('D12_assembly_'+name,root)
    GROUPS[name]['d12Assembly']=name
def tag(o,part,source='D12-F14',role='internal',confidence='family architecture; dimensions reconstructed'):
    o['d12Part']=part;o['sourceId']=source;o['dimensionStatus']=confidence;o['d12Role']=role
    REG.append({'node':o.name,'part':part,'source':source,'role':role,'dimensions':confidence})
    return o
def mesh(name,vs,fs,material,parent=root,edge=0,smooth=False,part=None,source='D12-F14',role='internal'):
    data=bpy.data.meshes.new(name+'_mesh');data.from_pydata([C(v) for v in vs],[],fs);data.update()
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.parent=parent;data.materials.append(material)
    if smooth:
        for p in data.polygons:p.use_smooth=True
    if edge:
        mod=ob.modifiers.new('Machined edge radius','BEVEL');mod.width=edge;mod.segments=2
        mod=ob.modifiers.new('Weighted machining normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    uv=data.uv_layers.new(name='MetricUV')
    for p in data.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]))
        for li in p.loop_indices:
            v=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(v[(axis+1)%3]*3,v[(axis+2)%3]*3)
    return tag(ob,part or name,source,role)
def prism(name,poly,lo,hi,material,parent=root,axis='x',edge=.001,**kw):
    def point(d,u,v):return (d,u,v) if axis=='x' else (u,d,v) if axis=='y' else (u,v,d)
    n=len(poly);vs=[point(d,*p) for d in [lo,hi] for p in poly]
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,parent,edge,**kw)
def box(name,size,pos,material,parent=root,edge=.003,**kw):
    x,y,z=pos;a,b,c=[d/2 for d in size]
    return prism(name,[(y-b,z-c),(y+b,z-c),(y+b,z+c),(y-b,z+c)],x-a,x+a,material,parent,edge=edge,**kw)
def lathe(name,profile,pos,material,parent=root,axis='x',n=48,closed=False,**kw):
    # Profile is (axial distance, radius); supports machined recesses, open bores,
    # ring grooves, sealing lands and genuine annular end faces.
    vs=[]
    for d,r in profile:
        for j in range(n):
            a=j/n*2*pi;v=(d,r*cos(a),r*sin(a)) if axis=='x' else (r*cos(a),d,r*sin(a)) if axis=='y' else (r*cos(a),r*sin(a),d)
            vs.append(tuple(v[k]+pos[k] for k in range(3)))
    fs=[]
    for k in range(len(profile)-1+(1 if closed else 0)):
        k1=(k+1)%len(profile)
        fs += [(k*n+j,k*n+(j+1)%n,k1*n+(j+1)%n,k1*n+j) for j in range(n)]
    return mesh(name,vs,fs,material,parent,smooth=True,**kw)
def cylinder(name,r,length,pos,material,parent=root,axis='x',n=40,**kw):
    return lathe(name,[(-length/2,0),(-length/2,r),(length/2,r),(length/2,0)],pos,material,parent,axis,n,**kw)
def ring(name,r,inside,length,pos,material,parent=root,axis='x',n=48,**kw):
    return lathe(name,[(-length/2,inside),(-length/2,r),(length/2,r),(length/2,inside)],pos,material,parent,axis,n,True,**kw)
def pipe(name,pts,r,material,parent=root,**kw):
    # Smooth bend with round cross section; export as an editable mesh later.
    curve=bpy.data.curves.new(name+'_path','CURVE');curve.dimensions='3D';curve.resolution_u=8;curve.bevel_depth=r;curve.bevel_resolution=2
    if len(pts)>32:
        curve.bevel_resolution=1;sp=curve.splines.new('POLY');sp.points.add(len(pts)-1)
        for p,v in zip(sp.points,pts):p.co=(*C(v),1)
    else:
        sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
        for p,v in zip(sp.bezier_points,pts):p.co=C(v);p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(ob);ob.parent=parent;curve.materials.append(material)
    return tag(ob,kw.get('part',name),kw.get('source','KMZ-525A'),kw.get('role','internal'))
def bolt(name,pos,parent=root,axis='y',r=.008,role='internal'):
    ring(name+'_washer',r*1.4,r*.63,.0025,pos,POLISH,parent,axis,24,part='washer',source='KMZ-525A',role=role)
    ob=cylinder(name+'_hex',r,.009,pos,STEEL,parent,axis,6,part='hexagonal fastener',source='KMZ-525A',role=role)
    return ob
def capsule(length,width,n=14):
    points=[];r=width/2;d=(length-width)/2
    for center,start in [(d,-pi/2),(-d,pi/2)]:
        points += [(center+r*cos(start+i/n*pi),r*sin(start+i/n*pi)) for i in range(n+1)]
    return points
def hollow_plate(name,xs,zs,ylo,yhi,hole,material,parent,**kw):
    # Square/circular annulus is the topology of each liner seat, no painted hole.
    vs=[];n=48
    for y in [ylo,yhi]:
        for inner in [False,True]:
            for j in range(n):
                a=j/n*2*pi;c=cos(a);s=sin(a);r=hole if inner else min(xs/max(abs(c),1e-9),zs/max(abs(s),1e-9))
                vs.append((r*c,y,r*s))
    fs=[]
    for j in range(n):
        k=(j+1)%n;fs += [(j,k,n+k,n+j),(2*n+k,2*n+j,3*n+j,3*n+k),(j,2*n+j,2*n+k,k),(n+k,3*n+k,3*n+j,n+j)]
    return mesh(name,vs,fs,material,parent,edge=.001,**kw)

# Split aluminium crankcase with a curved dry-sump lower casting. No solid box
# is placed through the crank train; access to the seven main bearings is real.
case=GROUPS['crankcase']
for s in [-1,1]:
    poly=[(-.12,s*.22),(.07,s*.22),(.22,s*.155),(.23,s*.137),(.08,s*.199),(-.12,s*.199)]
    prism(f'D12_crankcase_wall_{s}',poly,-.575,.575,CAST,case,edge=.004,source='D12-F11',role='housing')
    box(f'D12_sump_flange_{s}',(1.18,.025,.055),(0,-.13,s*.215),CAST,case,source='D12-F11',role='housing')
    for i in range(13):bolt(f'D12_case_bolt_{s}_{i}',(-.555+i*.092,-.113,s*.218),case,role='housing')
profile=[(-.222,.035),(-.222,.15),(-.18,.213),(-.13,.225),(-.127,.208),(-.166,.19),(-.199,.14),(-.201,.035)]
# Extruded rounded-bottom shell, viewed down the crank axis.
poly=[(y,z) for y,z in profile]+[(y,-z) for y,z in reversed(profile)]
prism('D12_dry_sump_pan',poly,-.59,.59,CAST,case,edge=.004,source='D12-F11',role='housing')
for i in range(7):
    x=-.54+i*.18
    bearing=ring(f'D12_main_bearing_{i+1}',.065,.043,.03,(x,.07,0),BRONZE,root,part='main bearing',source='D12-F12')
    # Cross-sectional split cap; bores and mounting bolts remain visible.
    ring(f'D12_main_cap_{i+1}',.080,.065,.041,(x,.07,0),CAST,root,part='main bearing carrier',source='D12-F11')
    for s in [-1,1]:
        box(f'D12_bearing_ear_{i}_{s}',(.06,.035,.085),(x,.065,s*.083),CAST,root,source='D12-F11')
        bolt(f'D12_bearing_fastener_{i}_{s}',(x,.05,s*.098),root)

crank=empty('D12_crankshaft',root,(0,.07,0))
for i in range(7):cylinder(f'D12_main_journal_{i+1}',.043,.075,(-.54+i*.18,0,0),POLISH,crank,source='D12-F12')
for i in range(6):
    x=(i-2.5)*.18;phase=POSES['pinPhases'][i];py=.09*cos(phase);pz=.09*sin(phase)
    cylinder(f'D12_crankpin_{i+1}',.037,.083,(x,py,pz),POLISH,crank,source='D12-F12')
    # Forged web contains the real offset between main and rod journals.
    for dx in [-.06,.06]:
        web=prism(f'D12_crank_web_{i}_{dx}',capsule(.202,.112),x+dx-.019,x+dx+.019,STEEL,crank,edge=.005,source='D12-F12')
        # Capsule plane uses its long first coordinate as the crank direction.
        web.location=C((0,py/2,pz/2));web.rotation_euler.x=phase
    for dx in [-.021,.021]:ring(f'D12_crank_oil_land_{i}_{dx}',.038,.033,.004,(x+dx,py,pz),POLISH,crank,source='D12-F13')
cylinder('D12_timing_nose',.035,.15,(-.675,0,0),POLISH,crank,source='D12-F13')
cylinder('D12_flywheel_hub',.09,.16,(.638,0,0),STEEL,crank,source='KMZ-525A')
lathe('D12_flywheel',[(.60,.08),(.61,.20),(.65,.305),(.695,.305),(.704,.25),(.702,.12),(.735,.09)],(0,0,0),STEEL,crank,n=96,source='KMZ-525A')
# C5 flywheel ring is authored in blender-starting.py and attached separately.
for i in range(12):
    a=i*pi/6;bolt(f'D12_flywheel_bolt_{i}',(.708,.16*cos(a),.16*sin(a)),crank,'x',.011)

for i in range(6):
    master=empty(f'D12_master_rod_{i+1}',root);slave=empty(f'D12_slave_rod_{i+1}',root)
    # Main big end, separate bearing shells and cap, forked articulated pin ears.
    ring(f'D12_master_big_end_{i}',.061,.038,.075,(0,0,0),STEEL,master,source='D12-F14')
    ring(f'D12_master_shell_{i}',.038,.037,.068,(0,0,0),BRONZE,master,source='D12-F14')
    for dx in [-.028,.028]:
        ring(f'D12_articulation_ear_{i}_{dx}',.026,.014,.018,(dx,SPEC['earAlong'],SPEC['earAcross']),STEEL,master,source='D12-F14')
    cylinder(f'D12_articulation_pin_{i}',.014,.085,(0,SPEC['earAlong'],SPEC['earAcross']),POLISH,master,source='D12-F14')
    # Removable lower cap and its two transverse tapered retaining pins, not a
    # modern two-bolt generic connecting rod (manual p.32).
    for z in [-.049,.049]:cylinder(f'D12_cap_taper_pin_{i}_{z}',.006,.078,(0,-.019,z),POLISH,master,source='D12-F14')
    for assembly,length,suffix in [(master,SPEC['mainRod'],'master'),(slave,SPEC['slaveRod'],'slave')]:
        radius=.024 if suffix=='master' else .026
        ring(f'D12_{suffix}_small_end_{i}',.026,.014,.04,(0,length,0),STEEL,assembly,source='D12-F14')
        ring(f'D12_{suffix}_pin_bush_{i}',.014,.012,.039,(0,length,0),BRONZE,assembly,source='D12-F14')
        if suffix=='slave':ring(f'D12_slave_lower_eye_{i}',.026,.014,.032,(0,0,0),STEEL,assembly,source='D12-F14')
        start=.050 if suffix=='master' else .025;end=length-.023
        # Tapered I beam, two flanges and recessed web instead of a round stick.
        poly=[(start,-.023),(start+.05,-.015),(end,-.019),(end,.019),(start+.05,.015),(start,.023)]
        prism(f'D12_{suffix}_web_{i}',poly,-.005,.005,STEEL,assembly,edge=.002,source='D12-F14')
        for z in [-1,1]:
            poly2=[(start,z*.023),(start+.05,z*.015),(end,z*.019),(end,z*.014),(start+.05,z*.010),(start,z*.018)]
            prism(f'D12_{suffix}_flange_{i}_{z}',poly2,-.019,.019,STEEL,assembly,edge=.0018,source='D12-F14')
    for bank in ['L','R']:
        name=f'{bank}{i+1}';piston=empty('D12_piston_'+name,root)
        # Hollow skirt, machined ring grooves and under-crown; 150 mm nominal
        # cylinder bore with a small displayed clearance, not a service fit.
        profile=[(-.065,.064),(-.065,.0745),(-.027,.0745),(-.025,.070),(-.016,.070),(-.014,.0745),(.007,.0745),(.008,.071),(.013,.071),(.014,.0745),(.032,.0745),(.033,.071),(.038,.071),(.039,.0745),(.056,.0745),(.062,.068),(.062,0),(.050,0),(.047,.061),(-.047,.064)]
        lathe('D12_piston_body_'+name,profile,(0,0,0),ALLOY,piston,'y',64,True,source='D12-F14')
        for k,y in enumerate([.0355,.0105,-.018,-.023,-.056]):
            ring(f'D12_piston_ring_{name}_{k+1}',.07485,.0705,.0032,(0,y,0),STEEL,piston,'y',64,source='D12-F14')
        ring('D12_gudgeon_pin_'+name,.012,.006,.137,(0,0,0),POLISH,piston,'x',48,source='D12-F14')
        for s in [-1,1]:ring(f'D12_pin_boss_{name}_{s}',.024,.012,.028,(s*.047,0,0),ALLOY,piston,'x',32,source='D12-F14')

exec(compile((ROOT/'scripts/d12-cam-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-cam-detail.py'),'exec'))

for bank,s in [('L',-1),('R',1)]:
    b=empty('D12_bank_'+bank,GROUPS['cylinder_blocks'],(0,.07,0),s*BETA)
    head=empty('D12_head_'+bank,GROUPS['cylinder_heads'],(0,.07,0),s*BETA)
    cover=empty('D12_cover_'+bank,GROUPS['cam_covers'],(0,.07,0),s*BETA)
    # Six joined jacket seats with actual hollow cylinder liners, coolant space,
    # continuous outer casting rails and through-studs.
    for i in range(6):
        x=(i-2.5)*.18
        lin=lathe(f'D12_wet_liner_{bank}{i+1}',[(.205,.077),(.205,.075),(.494,.075),(.498,.089),(.486,.089),(.485,.08),(.25,.08)],(x,0,0),POLISH,b,'y',64,True,source='D12-F15',role='liner')
        for y in [.231,.244]:ring(f'D12_liner_seal_{bank}_{i}_{y}',.082,.079,.004,(x,y,0),RUBBER,b,'y',32,source='D12-F15',role='liner')
        seat=empty(f'D12_liner_seat_{bank}{i+1}',b,(x,0,0))
        hollow_plate(f'D12_jacket_deck_{bank}{i+1}',.09,.118,.478,.493,.0805,CAST,seat,source='D12-F15',role='housing')
        hollow_plate(f'D12_jacket_lower_{bank}{i+1}',.09,.114,.25,.266,.081,CAST,seat,source='D12-F15',role='housing')
        for z in [-.107,.107]:
            cylinder(f'D12_head_stud_{bank}_{i}_{z}',.006,.40,(x,.427,z),POLISH,b,'y',20,source='D12-F15')
            bolt(f'D12_head_nut_{bank}_{i}_{z}',(x,.625,z),head,r=.010)
        # Four separate seat rings, valve guides, valves and dual concentric springs.
        for kind in ['intake','exhaust']:
            z=(1 if kind=='intake' else -1)*(-s)*SPEC['valveOffset']
            for j in range(2):
                vx=x+(-1 if j==0 else 1)*SPEC['valveOffset'];vn=f'{bank}{i+1}_{kind}_{j+1}'
                ring('D12_valve_seat_'+vn,.030,.024,.014,(vx,.525,z),STEEL,head,'y',40,source='D12-F16')
                ring('D12_valve_guide_'+vn,.009,.005,.055,(vx,.56,z),BRONZE,head,'y',24,source='D12-F16')
                valve=empty('D12_valve_'+vn,root)
                lathe('D12_valve_head_stem_'+vn,[(0,0),(.001,.026),(.004,.028),(.009,.025),(.021,.006),(.124,.005),(.130,.0065),(.131,0)],(0,0,0),POLISH,valve,'y',40,source='D12-F16')
                cylinder('D12_valve_retainer_'+vn,.018,.006,(0,.107,0),STEEL,valve,'y',28,source='D12-F16')
                cylinder('D12_tappet_'+vn,.016,.017,(0,.119,0),STEEL,valve,'y',32,source='D12-F16')
                spring=empty('D12_spring_'+vn,root)
                for r,turns in [(.014,7),(.010,8)]:
                    pts=[(r*cos(k/(turns*16)*turns*2*pi),k/(turns*16)*SPEC['springLength'],r*sin(k/(turns*16)*turns*2*pi)) for k in range(turns*16+1)]
                    pipe(f'D12_coil_{vn}_{r}',pts,.0017,STEEL,spring,source='D12-F16',part='concentric valve spring')
    for z in [-.115,.115]:
        box(f'D12_block_casting_{bank}_{z}',(1.12,.223,.017),(0,.369,z),CAST,b,edge=.008,source='D12-F15',role='housing')
        box(f'D12_head_casting_{bank}_{z}',(1.14,.144,.018),(0,.572,z),CAST,head,edge=.009,source='D12-F15',role='housing')
        for i in range(12):
            x=-.516+i*.094
            box(f'D12_cast_rib_{bank}_{z}_{i}',(.012,.18,.016),(x,.354,z*1.045),CAST,b,edge=.005,source='KMZ-525A',role='housing')
    for x in [-.568,.568]:
        box(f'D12_block_end_{bank}_{x}',(.017,.223,.23),(x,.369,0),CAST,b,source='D12-F15',role='housing')
        box(f'D12_head_end_{bank}_{x}',(.017,.144,.234),(x,.572,0),CAST,head,source='D12-F15',role='housing')
    # A hollow rolled cam-cover section, perimeter flange and three detachable
    # oval inspection covers per bank, matched to the 525A restoration photos.
    cross=[]
    for radius,reverse in [(.132,False),(.123,True)]:
        pts=[(.674+radius*.69*sin(k/24*pi),radius*cos(k/24*pi)) for k in range(25)]
        cross+=list(reversed(pts)) if reverse else pts
    prism('D12_cam_cover_shell_'+bank,cross,-.594,.594,COVER,cover,edge=.002,smooth=True,source='KMZ-525A',role='cover')
    cap=[(.674,-.132),(.674,.132)]+[(.674+.132*.69*sin(k/24*pi),.132*cos(k/24*pi)) for k in range(1,25)]
    for x in [-.590,.590]:prism(f'D12_cam_cover_end_{bank}_{x}',cap,x-.004,x+.004,COVER,cover,edge=.002,source='KMZ-525A',role='cover')
    for z in [-.125,.125]:
        box(f'D12_cover_flange_{bank}_{z}',(1.22,.012,.032),(0,.677,z),COVER,cover,source='KMZ-525A',role='cover')
        for i in range(13):bolt(f'D12_cover_bolt_{bank}_{z}_{i}',(-.566+i*.0943,.691,z),cover,role='cover')
    for i,x in enumerate([-.392,0,.392]):
        poly=[(u+x,v) for u,v in capsule(.334,.102)]
        prism(f'D12_oval_inspection_seal_{bank}_{i}',poly,.756,.760,GASKET,cover,axis='y',edge=.001,source='KMZ-525A',role='cover')
        prism(f'D12_oval_inspection_lid_{bank}_{i}',[(x+(u-x)*.97,v*.92) for u,v in poly],.759,.765,COVER,cover,axis='y',edge=.003,source='KMZ-525A',role='cover')
        for dx,dz in [(-.145,0),(.145,0),(-.09,-.040),(.09,-.040),(-.09,.040),(.09,.040)]:bolt(f'D12_lid_screw_{bank}_{i}_{dx}_{dz}',(x+dx,.767,dz),cover,r=.0045,role='cover')
    build_cam_bank(bank,s,head)

# The valley houses the central twelve-element pump and two six-branch intake
# manifolds. These visible shapes are variant-confirmed by the KMZ photographs.
inj=GROUPS['fuel_injection'];intake=GROUPS['intake'];exhaust=GROUPS['exhaust']
box('D12_injection_pump_case',(.66,.13,.125),(0,.612,0),CAST,inj,edge=.018,source='KMZ-525A',role='pump-housing')
box('D12_injection_inspection_plate',(.55,.065,.007),(0,.601,-.066),STEEL,inj,edge=.006,source='KMZ-525A',role='pump-housing')
cam=empty('D12_injection_cam',root,(0,.59,0));cylinder('D12_pump_camshaft',.014,.68,(0,0,0),POLISH,cam,source='D12-F18')
for k,name in enumerate(SPEC['fireOrder']):
    x=-.275+k*.05
    cyl=cylinder(f'D12_pump_delivery_holder_{name}',.012,.051,(x,.704,0),POLISH,inj,'y',24,source='KMZ-525A')
    bolt(f'D12_delivery_nut_{name}',(x,.733,0),inj,r=.014)
    pl=empty('D12_pump_plunger_'+name,root);cylinder('D12_plunger_barrel_'+name,.005,.045,(0,.02,0),POLISH,pl,'y',20,source='D12-F18')
    cylinder('D12_pump_return_retainer_'+name,.011,.004,(0,.004,0),STEEL,pl,'y',24,source='D12-F18')
    bank=name[0];i=int(name[1])-1;s=-1 if bank=='L' else 1;bx=(i-2.5)*.18
    def bp(x,y,z):return(x,.07+y*cos(s*BETA)-z*sin(s*BETA),y*sin(s*BETA)+z*cos(s*BETA))
    end=bp(bx,.65,-s*.107)
    pipe('D12_injection_line_'+name,[(x,.756,0),(x,.778,s*.075),(bx,.797,s*.17),end],.0032,POLISH,inj,source='KMZ-525A',part='high pressure injection pipe')
    injector=empty('D12_injector_'+name,inj,end,s*BETA)
    cylinder('D12_injector_body_'+name,.010,.070,(0,-.025,0),POLISH,injector,'y',28,source='KMZ-525A')
    bolt('D12_injector_union_'+name,(0,.012,0),injector,r=.014)
for bank,s in [('L',-1),('R',1)]:
    # Thin-wall manifold mouths and six curved runners, with flange pads.
    lathe('D12_intake_plenum_'+bank,[(-.63,.057),(-.63,.065),(.55,.070),(.58,.057),(.58,.052),(-.63,.051)],(0,.676,s*.185),PAINT,intake,n=64,closed=True,source='KMZ-525A')
    for endx in [-.63,.57]:ring(f'D12_intake_clamp_{bank}_{endx}',.068,.06,.018,(endx,.676,s*.185),POLISH,intake,n=40,source='KMZ-525A')
    lathe('D12_exhaust_manifold_'+bank,[(-.61,.045),(-.61,.055),(.53,.055),(.53,.045)],(0,.514,s*.459),IRON,exhaust,n=48,closed=True,source='KMZ-525A')
    # Transport exhaust manifold has a water jacket with broad flat inspection
    # faces, seen in both factory photos; it is not an exposed circular tube.
    jacket=empty('D12_exhaust_jacket_'+bank,exhaust,(0,.511,s*.456))
    for y in [-.064,.064]:box(f'D12_exhaust_jacket_edge_{bank}_{y}',(1.15,.014,.129),(0,y,0),PAINT,jacket,edge=.008,source='FACTORY-525A',role='housing')
    for z in [-.065,.065]:box(f'D12_exhaust_jacket_face_{bank}_{z}',(1.15,.135,.016),(0,0,z),PAINT,jacket,edge=.013,source='FACTORY-525A',role='housing')
    for x in [-.571,.571]:box(f'D12_exhaust_jacket_end_{bank}_{x}',(.018,.135,.135),(x,0,0),PAINT,jacket,edge=.014,source='FACTORY-525A',role='housing')
    for x in [-.415,-.19,.19,.415]:
        cylinder(f'D12_exhaust_jacket_core_plug_{bank}_{x}',.014,.004,(x,.002,s*.076),CAST,jacket,'z',32,source='FACTORY-525A',role='housing')
    for x in [-.51,.51]:
        for y in [-.043,.043]:bolt(f'D12_exhaust_jacket_bolt_{bank}_{x}_{y}',(x,y,s*.078),jacket,'z',.006,role='housing')
    for i in range(6):
        x=(i-2.5)*.18
        pipe(f'D12_intake_runner_{bank}{i+1}',[(x,.663,s*.193),(x,.597,s*.238),(x,.575,s*.255)],.029,PAINT,intake,source='KMZ-525A')
        pipe(f'D12_exhaust_runner_{bank}{i+1}',[(x,.513,s*.385),(x,.522,s*.420),(x,.514,s*.46)],.027,IRON,exhaust,source='KMZ-525A')
        for z in [s*.257,s*.413]:
            box(f'D12_manifold_flange_{bank}_{i}_{z}',(.082,.058,.013),(x,.534 if abs(z)>.4 else .579,z),CAST,intake if abs(z)<.4 else exhaust,edge=.007,source='KMZ-525A')
            for dx in [-.030,.030]:bolt(f'D12_manifold_nut_{bank}_{i}_{z}_{dx}',(x+dx,.565 if abs(z)>.4 else .608,z),intake if abs(z)<.4 else exhaust,r=.006)
    pipe('D12_coolant_head_rail_'+bank,[(-.59,.416,s*.411),(-.4,.413,s*.431),(.4,.413,s*.431),(.54,.35,s*.43)],.019,PAINT,root,source='KMZ-525A')

# Gear-end drive towers follow the bevel-shaft architecture (not a timing belt).
timing=GROUPS['timing']
for s in [-1,1]:
    pipe(f'D12_timing_tower_{s}',[(-.637,.105,0),(-.637,.399,s*.16),(-.637,.662,s*.30)],.035,CAST,timing,source='D12-F18',role='housing')
    for y,z,r in [(.105,0,.071),(.399,s*.16,.047),(.662,s*.30,.06)]:cylinder(f'D12_bevel_case_{s}_{y}',r,.095,(-.637,y,z),CAST,timing,source='D12-F18',role='housing')
for x in [-.455,.438]:
    for s in [-1,1]:
        box(f'D12_mount_lug_{x}_{s}',(.12,.05,.18),(x,-.077,s*.27),CAST,GROUPS['mounts'],edge=.009,source='KMZ-525A')
        bolt(f'D12_mount_fastener_{x}_{s}',(x,-.044,s*.314),GROUPS['mounts'],r=.014)

# Variant photographs arrived during the reconstruction. These external
# attachments follow the factory pictures and labelled 525A assembly diagram;
# their internals and period-specific dimensional acceptance remain open.
start=GROUPS['starting']
# C5 inertia starter is authored in the separate starting module.
gen=empty('D12_generator',start,(-.285,.166,-.343))
lathe('D12_generator_casting',[(-.195,.031),(-.18,.064),(-.155,.075),(.11,.075),(.15,.066),(.18,.04)],(0,0,0),CAST,gen,n=64,source='FACTORY-525A',role='accessory-housing')
for x in [-.125,.083]:
    ring(f'D12_generator_vent_band_{x}',.078,.074,.051,(x,0,0),STEEL,gen,n=64,source='FACTORY-525A',role='accessory-housing')
    for k in range(16):
        a=k/16*2*pi;o=box(f'D12_generator_slot_{x}_{k}',(.023,.002,.009),(x,.079,0),RUBBER,gen,edge=.002,source='FACTORY-525A',role='accessory-housing');o.rotation_euler.x=a
pipe('D12_generator_power_cable',[(-.43,.18,-.36),(-.50,.12,-.40),(-.45,-.10,-.36),(-.1,-.10,-.32)],.009,RUBBER,start,source='FACTORY-525A')
filter=empty('D12_oil_filter',root,(.045,.162,.341))
lathe('D12_oil_filter_barrel',[(-.237,.044),(-.22,.077),(-.18,.083),(.17,.083),(.207,.073),(.227,.056)],(0,0,0),PAINT,filter,n=64,source='FACTORY-525A',role='accessory-housing')
for x in [-.17,.12]:ring(f'D12_oil_filter_band_{x}',.086,.081,.014,(x,0,0),STEEL,filter,n=40,source='FACTORY-525A',role='accessory-housing')
for k in range(6):
    a=k/6*2*pi;bolt(f'D12_oil_filter_end_bolt_{k}',(-.231,.052*cos(a),.052*sin(a)),filter,'x',.008)
for z in [.308,.375]:pipe(f'D12_filter_oil_pipe_{z}',[(-.195,.164,z),(-.29,.15,z),(-.38,-.081,z),(-.44,-.18,.25)],.012,CAST,root,source='FACTORY-525A')
flycase=ring('D12_flywheel_bellhousing',.337,.319,.09,(.612,.07,0),CAST,root,n=96,source='FACTORY-525A',role='housing')
for k in range(16):
    a=k/16*2*pi;bolt(f'D12_bellhousing_bolt_{k}',(.663,.07+.329*cos(a),.329*sin(a)),root,'x',.008,role='housing')
# Front support casting around the crank drive and flange-mounted lower pump.
ring('D12_front_support',.168,.046,.075,(-.622,.07,0),CAST,timing,n=64,source='FACTORY-525A',role='housing')
for k in range(10):
    a=k/10*2*pi;bolt(f'D12_front_support_bolt_{k}',(-.669,.07+.133*cos(a),.133*sin(a)),timing,'x',.007,role='housing')
water=empty('D12_water_pump',root,(-.541,-.175,0))
for y,r in [(.034,.065),(0,.068),(-.035,.060)]:
    cylinder(f'D12_water_pump_casting_{y}',r,.036,(0,y,0),CAST,water,'y',48,source='FACTORY-525A',role='accessory-housing')
for s in [-1,1]:
    pipe(f'D12_coolant_inlet_{s}',[(-.541,-.175,s*.035),(-.54,-.14,s*.105),(-.50,.19,s*.241),(-.51,.398,s*.29)],.024,CAST,root,source='FACTORY-525A')
    ring(f'D12_coolant_hose_clamp_{s}',.028,.025,.018,(-.51,.349,s*.29),POLISH,root,'y',32,source='FACTORY-525A')
air=empty('D12_air_start_distributor',root,(-.676,.478,0))
cylinder('D12_air_distributor_case',.068,.052,(0,0,0),CAST,air,source='FACTORY-525A',role='accessory-housing')
for k,name in enumerate(SPEC['fireOrder']):
    a=k/12*2*pi;cy=.056*cos(a);cz=.056*sin(a)
    cylinder(f'D12_air_start_union_{name}',.008,.016,(-.033,cy,cz),BRONZE,air,n=6,source='FACTORY-525A')
    s=-1 if name[0]=='L' else 1;i=int(name[1])-1;x=(i-2.5)*.18
    pipe('D12_air_start_pipe_'+name,[(-.715,.478+cy,cz),(-.735,.61,s*.12),(x,.63,s*.27)],.003,CAST,root,source='FACTORY-525A')

for ob in list(bpy.data.objects):
    if ob.name.startswith(('D12_timing_tower_','D12_bevel_case_','D12_cam_24_bevel_')):bpy.data.objects.remove(ob,do_unlink=True)
exec(compile((ROOT/'scripts/d12-timing-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-timing-detail.py'),'exec'))
build_timing_train()
for ob in list(bpy.data.objects):
    if ob.name.startswith(('D12_water_pump','D12_coolant_inlet_','D12_coolant_hose_clamp_')):bpy.data.objects.remove(ob,do_unlink=True)
exec(compile((ROOT/'scripts/d12-water-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-water-detail.py'),'exec'))
build_water_pump()
print('D12_GEOMETRY_AUTHORED',len(REG),flush=True)
for name,pose in POSES['frames'][0]['pose'].items():
    ob=bpy.data.objects.get(name)
    if ob:ob.location=C(pose['p']);ob.rotation_euler.x=pose['rx'];ob.scale.z=pose.get('sy',1)
# Matching web and native poses; 720 degrees with rigid main/articulated rods.
for f in POSES['frames']:
    for name,pose in f['pose'].items():
        ob=bpy.data.objects.get(name)
        if not ob:continue
        ob.location=C(pose['p']);ob.rotation_euler.x=pose['rx'];ob.scale.z=pose.get('sy',1)
        for channel in ['location','rotation_euler','scale']:ob.keyframe_insert(data_path=channel,frame=f['frame'],group='D12 coupled mechanism')
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=241;scene.render.fps=30;scene.frame_set(1)
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
world=bpy.data.worlds.new('D12 inspection studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28;scene.world=world
floor=box('D12_STUDIO_FLOOR',(100,.025,100),(0,-.262,0),mat('D12_studio_floor',(.07,.08,.074),0,.85),None,edge=0)
for name,pos,energy,size,color in [('D12_KEY',(-2,4,2),650,4,(1,.94,.85)),('D12_RIM',(2,3,-3),950,3,(.8,.88,1)),('D12_FILL',(-3,1,-1),280,2,(1,1,1))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=C(pos);ob.rotation_euler=(C((0,.3,0))-ob.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('D12_CAMERA',bpy.data.cameras.new('D12_CAMERA'));bpy.context.collection.objects.link(camera)
camera.location=C((2.05,1.9,2.1));camera.rotation_euler=(C((0,.30,0))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=52;scene.camera=camera
text=bpy.data.texts.new('D12_REFERENCE_AND_SCOPE');text.write((ROOT/'docs'/'D12_REFERENCE_REGISTER.md').read_text(encoding='utf-8'))
engine_collection=bpy.data.collections.new('D12_ENGINE');scene.collection.children.link(engine_collection)
pending=[root]
while pending:
    ob=pending.pop();pending.extend(ob.children)
    for collection in list(ob.users_collection):collection.objects.unlink(ob)
    engine_collection.objects.link(ob)
refs=bpy.data.collections.new('D12_REFERENCE_IMAGES');scene.collection.children.link(refs)
for i,path in enumerate([Path('D:/maz543-references/engine/02-kmz-complete-after.webp'),ROOT/'work/reference-docs/D12-page-33.png',ROOT/'work/reference-docs/D12-page-38.png']):
    if not path.exists():continue
    image=bpy.data.images.load(str(path));image.pack();ob=bpy.data.objects.new('D12_REF_'+path.stem,None);refs.objects.link(ob);ob.empty_display_type='IMAGE';ob.data=image;ob.empty_display_size=2;ob.location=(0,3+i*.05,1);ob.hide_render=True;ob.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'D12A525A_Engine_Master.blend'),compress=True)
scene.render.filepath=str(OUT/'d12a525a-assembled.png');bpy.ops.render.render(write_still=True)

# Export a separate web module so body and detailed mechanics do not become one
# oversized download. Group fixed details by material, role and source, retaining
# all individual objects in the native master and the explicit part register.
def descendants(o):
    r=[]
    for c in o.children:r.append(c);r+=descendants(c)
    return r
bpy.ops.object.select_all(action='DESELECT')
objects=[o for o in descendants(root) if o.type in {'MESH','CURVE'}]
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH')
for holder in [root]+[o for o in descendants(root) if o.type=='EMPTY']:
    batches={}
    for ob in holder.children:
        if ob.type!='MESH':continue
        key=(ob.data.materials[0].name,ob.get('d12Role'),ob.get('sourceId'))
        batches.setdefault(key,[]).append(ob)
    for (material,role,source),batch in batches.items():
        if len(batch)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in batch:o.select_set(True)
        bpy.context.view_layer.objects.active=batch[0];count=len(batch);bpy.ops.object.join()
        ob=bpy.context.object;ob.name=holder.name+'_'+material+'_'+str(role);ob['detail_meshes']=count;ob['d12Role']=role
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
for ob in descendants(root):ob.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/d12a525a-engine.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
# Native cutaway preview is also saved so surface-only beauty cannot hide the
# articulated mechanism or valve-count defects.
for ob in descendants(root):
    if ob.get('d12Role') in ['housing','cover','liner','pump-housing']:ob.hide_render=True
scene.render.filepath=str(OUT/'d12a525a-internals.png');bpy.ops.render.render(write_still=True)
model_register=[entry for entry in REG if not entry['node'].startswith('D12_STUDIO_')]
(OUT/'d12-parts-register.json').write_text(json.dumps(model_register,indent=2),encoding='utf-8')
print('D12_COMPLETE',len(model_register),'registered authored engine pieces (studio excluded)',flush=True)

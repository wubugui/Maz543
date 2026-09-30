"""Four-wheel converter topology from MAZ 1973 fig.42 and 2008 parts drawings.
All unsourced geometry is explicitly fitted. No factory blade/performance claim.
"""
import bpy,bmesh,math,json,ast,sys,hashlib
from pathlib import Path
from math import sin,cos,pi,sqrt
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_strip_mesh import geometry
REG=[];root=None
def tag(o,part,source='',role='internal',**kw):
    o['converterPart']=part;o['sourceId']='1973 fig.42; 2008 converter parts drawings'
    o['dimensionStatus']='Fitted geometry, not factory CAD; blade count/profile, dimensions, fits and materials unverified.'
    REG.append(o.name);return o
tree=ast.parse((ROOT/'scripts/blender-d12.py').read_text());names={'C','empty','mat','mesh','lathe','ring','cylinder'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'helpers','exec'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
root=empty('S543_CONVERTER_ASSEMBLY');root['partId']='drive'
root['status']='Source topology reconstruction. Static assembly inspection; fluid/contact dynamics and factory dimensional fidelity unaccepted.'
groups={name:empty('CA_'+name,root) for name in ['pump','turbine','front_reactor','rear_reactor','fixed_support']}
groups['pump']['connection']='Input shaft 1 -> lockup body 4 -> casing 9 -> pump 12; thrust plate 8 also pump-side.'
groups['turbine']['connection']='Turbine 11 -> hub 2 -> turbine shaft 15 and gearbox input; driven lockup disc 7 via hub 3.'
for key in ['front_reactor','rear_reactor']:groups[key]['connection']='Independent reactor 6 -> outer race 53 -> roller freewheel -> common fixed inner race 13 -> fixed hub 52 -> casing 14.'
STEEL=mat('CA_machined_steel',(.28,.31,.32),.90,.29);PUMP=mat('CA_pump_casting',(.26,.31,.29),.8,.42)
TURB=mat('CA_turbine_casting',(.29,.25,.19),.8,.42);REACTOR=mat('CA_reactor_casting',(.20,.25,.29),.82,.38)
FRICTION=mat('CA_sintered_friction',(.22,.13,.06),.55,.52);SPRING=mat('CA_curved_strip_steel',(.31,.24,.12),.83,.34)
SEAL=mat('CA_seal',(.013,.017,.018),.02,.7)
FIT={'meridianCentreRadiusM':.195,'outerAxialRadiusM':.086,'outerRadialRadiusM':.105,'coreAxialRadiusM':.033,'coreRadialRadiusM':.045,
     'shellThicknessM':.003,'bladeTangentialThicknessM':.002,'bladeCounts':{'pump':32,'turbine':28,'front_reactor':20,'rear_reactor':20},
     'wheelMeridianDegrees':{'pump':[-1,156],'rear_reactor':[158,179],'front_reactor':[181,202],'turbine':[204,357]},
     'sourceNominalRollerM':[.0125,.022],'freewheelRowX':[-.016,.016],'wedgeAngleDeg':7,
     'limits':'Except interpreted 12.5 x 22 mm rollers, all dimensions and blade numbers/angles are reconstruction parameters. Early 543A compatibility with 2008 catalog remains unverified.'}
root['fit']=json.dumps(FIT)
rm=FIT['meridianCentreRadiusM'];ao=FIT['outerAxialRadiusM'];bo=FIT['outerRadialRadiusM'];ai=FIT['coreAxialRadiusM'];bi=FIT['coreRadialRadiusM']
wheel_material={'pump':PUMP,'turbine':TURB,'front_reactor':REACTOR,'rear_reactor':REACTOR}
def meridian(t,u):return (ai+(ao-ai)*u)*sin(t),rm+(bi+(bo-bi)*u)*cos(t)
def shell(name,start,end,outer,parent,material):
    A,B=(ao,bo) if outer else (ai,bi);direction=1 if outer else -1
    angles=[start+(end-start)*i/48 for i in range(49)]
    profile=[(A*sin(t),rm+B*cos(t)) for t in angles]
    profile += [((A+direction*.003)*sin(t),rm+(B+direction*.003)*cos(t)) for t in reversed(angles)]
    ob=lathe(name,profile,(0,0,0),material,parent,n=144,closed=True);ob['shellRole']='outer_shroud' if outer else 'core_ring';return ob
def blade(name,start,end,phase,twist,parent,material):
    ns=20;nr=6;vs=[];width=FIT['bladeTangentialThicknessM']
    for side in [-1,1]:
        for i in range(ns+1):
            s=i/ns;t=start+(end-start)*s
            for j in range(nr+1):
                u=-.003+.006*j/nr+j/nr;x,R=meridian(t,u)
                angle=phase+math.radians(twist)*(s*s*(3-2*s)-.5)+.04*sin(pi*s)*(u-.5)+side*width/(2*R)
                vs.append((x,R*cos(angle),R*sin(angle)))
    count=(ns+1)*(nr+1);fs=[]
    for i in range(ns):
        for j in range(nr):
            a=i*(nr+1)+j;b=a+nr+1
            fs.extend([(a,b,b+1,a+1),(a+count,a+1+count,b+1+count,b+count)])
    outline=list(range(nr+1))+[i*(nr+1)+nr for i in range(1,ns+1)]+[ns*(nr+1)+j for j in range(nr-1,-1,-1)]+[i*(nr+1) for i in range(ns-1,0,-1)]
    for a,b in zip(outline,outline[1:]+outline[:1]):fs.append((a,b,b+count,a+count))
    ob=mesh(name,vs,fs,material,parent,smooth=True);ob['blade']=True;ob['bladeTwistFitDeg']=twist;return ob
for key,angles in FIT['wheelMeridianDegrees'].items():
    start,end=map(math.radians,angles);parent=groups[key];material=wheel_material[key]
    shell('CA_'+key+'_outer_shroud',start,end,True,parent,material)
    shell('CA_'+key+'_core_ring',start,end,False,parent,material)
    twist={'pump':-24,'turbine':38,'front_reactor':-18,'rear_reactor':-15}[key]
    for i in range(FIT['bladeCounts'][key]):blade(f'CA_{key}_blade_{i:02d}',start,end,i*2*pi/FIT['bladeCounts'][key],twist,parent,material)
# Pump-side rotating cover and hydraulic lockup body, surrounding turbine.
cover_profile=[(-.135,.035),(-.135,.075),(-.113,.16),(-.098,.235),(-.064,.284),(-.015,.312),(.004,.312),(.004,.307),(-.014,.307),(-.060,.280),(-.093,.232),(-.108,.158),(-.130,.074),(-.130,.035)]
cover=lathe('CA_09_rotating_casing',cover_profile,(0,0,0),PUMP,groups['pump'],n=192,closed=True);cover['inspectionHide']='housing'
ring('CA_pump_cover_joint',.312,.297,.008,(.0025,0,0),PUMP,groups['pump'],n=192)
lathe('CA_01_input_shaft',[(-.220,.014),(-.220,.032),(-.130,.032),(-.130,.047),(-.116,.047),(-.116,.014)],(0,0,0),STEEL,groups['pump'],n=96,closed=True)
ring('CA_input_flange',.070,.032,.012,(-.205,0,0),STEEL,groups['pump'],n=96)
ring('CA_04_lockup_body',.164,.047,.009,(-.119,0,0),STEEL,groups['pump'],n=144)
piston=empty('CA_lockup_piston',groups['pump']);piston['travelFitM']=.0052;piston['motionStatus']='Geometry inspection only; pressures and stroke not calibrated.'
ring('CA_05_lockup_piston',.157,.052,.006,(-.110,0,0),STEEL,piston,n=144)
for R in [.053,.156]:ring(f'CA_piston_seal_{R}',R+.0006,R-.0006,.002,(-.110,0,0),SEAL,piston,n=144)
ring('CA_07_driven_disc_carrier',.154,.048,.002,(-.101,0,0),STEEL,groups['turbine'],n=144)
for x in [-.1027,-.0993]:ring('CA_07_friction_face_'+str(x),.152,.108,.0014,(x,0,0),FRICTION,groups['turbine'],n=144)
ring('CA_08_thrust_disc',.159,.108,.004,(-.095,0,0),STEEL,groups['pump'],n=144)
lathe('CA_03_lockup_turbine_hub',[(-.103,.024),(-.103,.051),(-.096,.051),(-.096,.033),(-.081,.033),(-.081,.024)],(0,0,0),STEEL,groups['turbine'],n=96,closed=True)
# Turbine connection is routed outside the working torus on its inlet side.
lathe('CA_02_turbine_hub',[(-.089,.024),(-.089,.190),(-.086,.195),(-.083,.190),(-.083,.024)],(0,0,0),TURB,groups['turbine'],n=144,closed=True)
ring('CA_15_turbine_shaft',.024,.010,.329,(.0755,0,0),STEEL,groups['turbine'],n=96)
# Fixed hub and common inner race remain one stationary reaction path.
ring('CA_52_fixed_hub',.046,.028,.1505,(.11975,0,0),STEEL,groups['fixed_support'],n=128)
ring('CA_13_shared_inner_race',.056,.028,.069,(0,0,0),STEEL,groups['fixed_support'],n=192)
ring('CA_fixed_support_flange',.080,.030,.010,(.0395,0,0),STEEL,groups['fixed_support'],n=144)
# Current source-corrected spring geometry, initial static equilibrium only.
strip_data=json.loads((ROOT/'work/freewheel-contact/strip-spring-study.json').read_text());initial_strip=strip_data['rows'][0]
sv,sf=geometry(initial_strip['points'],strip_data['fit']['widthM'],strip_data['fit']['thicknessM'])
ri=.056;r=.00625;rho=ri+r;alpha=math.radians(7);distance=r+rho*cos(alpha)
def pocket_boundary(a):
    d=math.degrees(a)
    if -13<=d<=8:return distance/cos(a-alpha)
    if d< -13:
        f=(d+15)/2;return (ri+.002)*(1-f)+distance/cos(math.radians(-13)-alpha)*f
    f=(d-8)/7;return distance/cos(math.radians(8)-alpha)*(1-f)+(ri+.002)*f
for key,x in zip(['front_reactor','rear_reactor'],FIT['freewheelRowX']):
    parent=groups[key];count=1440;vs=[]
    for xx in [x-.012,x+.012]:
        for inside in [False,True]:
            for j in range(count):
                a=-pi/12+2*pi*j/count;local=(a+pi/12)%(pi/6)-pi/12;R=pocket_boundary(local) if inside else .084
                vs.append((xx,R*cos(a),R*sin(a)))
    fs=[]
    for j in range(count):
        k=(j+1)%count;fs += [(j,k,count+k,count+j),(2*count+j,3*count+j,3*count+k,2*count+k),(j,2*count+j,2*count+k,k),(count+j,count+k,3*count+k,3*count+j)]
    race=mesh('CA_'+key+'_outer_race',vs,fs,STEEL,parent);race['catalogPart']='535-1501088-01'
    sign=1 if x>0 else -1
    ring('CA_'+key+'_thrust_ring',.084,.0565,.002,(x+sign*.013,0,0),STEEL,parent,n=144)
    # Fitted radial mounting sleeve, with the race bore and fluid-side clearance retained.
    sleeve=lathe('CA_'+key+'_hub_sleeve',[(sign*.003,.084),(sign*.003,.0875),(sign*.027,.0925),(sign*.027,.084)],(0,0,0),REACTOR,parent,n=144,closed=True)
    sleeve['fitLimit']='Reactor/race mount geometry and original splines still unverified.'
    for j in range(12):
        a=j*pi/6;cell=empty(f'CA_{key}_cell_{j:02d}',parent,rx=a)
        roller=cylinder(f'CA_{key}_roller_{j:02d}',r,.022,(x,rho,0),STEEL,cell,n=96);roller['catalogPart']='0000-1709202'
        spring=mesh(f'CA_{key}_strip_{j:02d}',[(xx+x,y,z) for xx,y,z in sv],sf,SPRING,cell);spring['catalogPart']='535-1501092';spring['state']='Initial fitted static equilibrium; no freewheel dynamics.'
# All editable geometry is closed; cylinder pole duplicates are explicitly welded.
for ob in bpy.data.objects:
    # Three.js animation/property binding strips periods from node names.
    # Author portable names so browser lookup retains exact native identity.
    ob.name=ob.name.replace('.','_')
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-10);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-11);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),(ob.name,'open mesh');assert bm.calc_volume()>0,(ob.name,'volume')
    bm.to_mesh(ob.data);bm.free()
    if not ob.get('blade'):
        for f in ob.data.polygons:f.use_smooth=abs(f.normal.x)<.999
notes={'fit':FIT,'sourceTopology':{k:v['connection'] for k,v in groups.items() if 'connection' in v},
       'notComplete':['Factory blade geometry/counts and installation','Actual fluid torque map and both reactor releases','Lockup hydraulic seals, spline/fastener fits and force integration','Bearing and pump-drive hardware','Whole-vehicle and browser final realism acceptance'],
       'sourceImages':['000-3024.jpg','catalog-converter-pump-reactors.gif'],'meshCount':sum(o.type=='MESH' for o in bpy.data.objects)}
for filename in notes['sourceImages']:
    im=bpy.data.images.load(str(ROOT/'work/reference-docs/transmission'/filename));im.pack();im.use_fake_user=True
bpy.data.texts.new('CONVERTER_SOURCE_AND_LIMITS').write(json.dumps(notes,ensure_ascii=False,indent=2))
path=ROOT/'outputs/MAZ543A_Converter_FourWheelAssembly.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
(ROOT/'work/transmission/converter-four-wheel-assembly.json').write_text(json.dumps(notes,indent=2),encoding='utf8')
print(json.dumps({'saved':str(path),'meshes':notes['meshCount'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}),flush=True)

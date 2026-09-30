"""MAZ 1973 figs.42/43: two roller freewheels on one fixed inner race.
Dimensions, roller count and wedge angle are fitted; static contact study only.
Does not overwrite the transmission, vehicle masters or runtime assets.
"""
import bpy,bmesh,math,json,ast,sys
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
ROOT=Path(__file__).resolve().parents[1];REG=[];root=None
def tag(o,part,source='',role='internal',**kw):
    o['converterPart']=part;o['converterRole']=role;o['sourceId']='MAZ 1973 figs.42/43'
    o['dimensionStatus']='Fitted reconstruction; roller count, wedge angle and all dimensions unmeasured.'
    REG.append(o.name);return o
tree=ast.parse((ROOT/'scripts/blender-d12.py').read_text())
names={'C','empty','mat','mesh','prism','box','lathe','cylinder','ring','pipe'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'converter_helpers','exec'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
root=empty('S543_CONVERTER_FREEWHEELS');root['partId']='drive'
STEEL=mat('CV_ground_races',(.31,.33,.35),.95,.25)
DARK=mat('CV_outer_races',(.11,.13,.15),.90,.37)
BRONZE=mat('CV_spring_steel',(.21,.18,.12),.85,.35)
FIT={'innerRadius':.056,'rollerRadius':.006,'boreRadius':.031,'outerRadius':.084,
     'rollerCount':12,'wedgeAngle':7*pi/180,'releaseAngle':-3*pi/180,
     'rowX':[-.014,.014],'raceWidth':.019,'rollerLength':.016,
     'springWireRadius':.000175,'springRadius':.0012,'springTurns':5,'springBaseZ':-.014}
ri=FIT['innerRadius'];r=FIT['rollerRadius'];rho=ri+r;alpha=FIT['wedgeAngle'];d=r+rho*cos(alpha)
inner=lathe('CV_shared_fixed_inner_race',[(-.032,FIT['boreRadius']),(-.032,ri),(.032,ri),(.032,FIT['boreRadius'])],(0,0,0),STEEL,root,closed=True,n=192)
inner['sharedBy']='front and rear reactor freewheel';inner['sourcePartNumberInFig42']=13
# One machined support flange, separate from the common inner race.
D=json.loads((ROOT/'work/transmission/converter-freewheel-support.json').read_text());n=len(D['points'])
vs=[(x,y,z) for x in [.032,.040] for y,z in D['points']]
fs=[tuple(reversed(f)) for f in D['caps']]+[tuple(v+n for v in f) for f in D['caps']]
for loop in D['rings']:
    for a,b in zip(loop,loop[1:]+loop[:1]):fs.append((a,b,b+n,a+n))
support=mesh('CV_fixed_reactor_support',vs,fs,DARK,root)
for j in range(6):
    a=j*pi/3
    cylinder('CV_support_bolt_shank_'+str(j),.0025,.008,(.036,.072*cos(a),.072*sin(a)),STEEL,root,n=32)
    cylinder('CV_support_bolt_head_'+str(j),.004,.003,(.0415,.072*cos(a),.072*sin(a)),STEEL,root,n=6)
def inner_profile(theta):
    # Continuous polygon boundary: a real planar wedge, deep end and web.
    a=theta*180/pi
    if -13<=a<=8:return d/cos(theta-alpha)
    if a< -13:
        q=(a+15)/2;return (ri+.002)*(1-q)+(d/cos(-13*pi/180-alpha))*q
    q=(a-8)/7;return (d/cos(8*pi/180-alpha))*(1-q)+(ri+.002)*q
def race(name,x,parent):
    count=FIT['rollerCount']*120;vs=[]
    for xx in [x-FIT['raceWidth']/2,x+FIT['raceWidth']/2]:
        for outside in [True,False]:
            for k in range(count):
                a=-pi/12+2*pi*k/count;local=((a+pi/12)%(pi/6))-pi/12
                radius=FIT['outerRadius'] if outside else inner_profile(local)
                vs.append((xx,radius*cos(a),radius*sin(a)))
    fs=[]
    for k in range(count):
        n=(k+1)%count
        fs += [(k,n,count+n,count+k),(2*count+k,3*count+k,3*count+n,2*count+n),
               (k,2*count+k,2*count+n,n),(count+k,count+n,3*count+n,3*count+k)]
    ob=mesh(name,vs,fs,DARK,parent);ob['wedgePlaneDistanceM']=d;return ob
def raw_spring_points(x,beta,tipOffset=0):
    start=Vector((x,rho,FIT['springBaseZ']));end=Vector((x,rho*cos(beta),rho*sin(beta)-r-tipOffset))
    axis=end-start;length=axis.length;axis.normalize();u=Vector((1,0,0));v=axis.cross(u).normalized()
    baseLength=-r-FIT['springBaseZ'];turn=2*pi*FIT['springTurns']
    radius=sqrt(FIT['springRadius']**2+(baseLength**2-length**2)/turn**2)
    pts=[];segments=160;sides=10;wire=FIT['springWireRadius']
    for i in range(segments+1):
        t=i/segments;a=turn*t;radial=cos(a)*u+sin(a)*v
        tangent=(length*axis+turn*radius*(-sin(a)*u+cos(a)*v)).normalized()
        normal=tangent.cross(radial).normalized();centre=start+length*t*axis+radius*radial
        for j in range(sides):
            b=2*pi*j/sides;pts.append(tuple(centre+wire*(cos(b)*radial+sin(b)*normal)))
    faces=[]
    for i in range(segments):
        for j in range(sides):
            k=i*sides+j;n=i*sides+(j+1)%sides;faces.append((k,n,n+sides,k+sides))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple(segments*sides+j for j in range(sides))])
    return pts,faces,length,radius
from functools import lru_cache
@lru_cache(None)
def spring_points(x,beta):
    # Seat the actual wire skin against the roller, not the helix centreline.
    # Moving only the coil's terminal plane keeps its fixed support point and
    # ideal centreline length. A 1-micrometre separation resolves mesh tangency.
    cy,cz=rho*cos(beta),rho*sin(beta)
    def clearance(data):
        pts,faces,_,_=data;minimum=float('inf')
        for f in faces:
            # All chords cover the convex projected face, including the actual
            # triangulation diagonals. The entire spring is behind the roller.
            for i,a in enumerate(f):
                for b in f[i+1:]:
                    ay,az=pts[a][1]-cy,pts[a][2]-cz;dy,dz=pts[b][1]-pts[a][1],pts[b][2]-pts[a][2]
                    q=max(0,min(1,-(ay*dy+az*dz)/max(1e-30,dy*dy+dz*dz)))
                    minimum=min(minimum,math.hypot(ay+q*dy,az+q*dz)-r)
        return minimum
    lo,hi=0,.001
    assert clearance(raw_spring_points(x,beta,hi))>1e-6
    for _ in range(22):
        mid=(lo+hi)/2
        if clearance(raw_spring_points(x,beta,mid))<1e-6:lo=mid
        else:hi=mid
    return raw_spring_points(x,beta,hi)
for row,x in zip(['front','rear'],FIT['rowX']):
    outer=empty('CV_'+row+'_outer',root);outer['sourcePartNumberInFig42']=53
    race('CV_'+row+'_wedged_outer_race',x,outer)
    for side in [-1,1]:
        ring(f'CV_{row}_retainer_{side}',.084,.0565,.0015,(x+side*.0105,0,0),STEEL,outer,n=144)
    for j in range(FIT['rollerCount']):
        angle=j*pi/6;cell=empty(f'CV_{row}_pocket_{j}',outer,rx=angle)
        roller=cylinder(f'CV_{row}_roller_{j}',r,FIT['rollerLength'],(0,0,0),STEEL,cell,n=128)
        roller['sourcePartNumberInFig42']=54
        vs,fs,_,_=spring_points(x,0);spring=mesh(f'CV_{row}_engagement_spring_{j}',vs,fs,BRONZE,cell,smooth=True)
        spring.shape_key_add(name='Basis');release=spring.shape_key_add(name='Released')
        rv,_,_,_=spring_points(x,FIT['releaseAngle'])
        for vertex,p in zip(release.data,rv):vertex.co=C(p)
        # These endpoint reference poses are geometric only, not a fluid-driven
        # or contact-force simulation. Whole assembly rotation remains unbaked.
        for frame,beta,key in [(0,0,0),(60,FIT['releaseAngle'],1),(120,0,0)]:
            roller.location=C((x,rho*cos(beta),rho*sin(beta)));roller.keyframe_insert('location',frame=frame)
            release.value=key;release.keyframe_insert('value',frame=frame)
root['fit']=json.dumps(FIT);root['motionStatus']='Discrete locked/released geometric inspection states, not continuous running animation. No reactor fluid torque, roller friction/contact dynamics, strength or factory geometry acceptance.'
for ob in bpy.data.objects:
    for animated in [ob,ob.data.shape_keys if ob.type=='MESH' else None]:
        if animated is None or not animated.animation_data or not animated.animation_data.action:continue
        for curve in animated.animation_data.action.fcurves:
            for key in curve.keyframe_points:key.interpolation='CONSTANT'
for ob in bpy.data.objects:
    if ob.type!='MESH' or ob.data.shape_keys:continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-9)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-10)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    # Ground planar ends must not share the smooth radial shading; otherwise
    # cylindrical rollers and the annular race misleadingly look spherical.
    for face in ob.data.polygons:
        if abs(face.normal.x)>.999:face.use_smooth=False
for filename in ['000-3024.jpg','000-0687.jpg']:
    im=bpy.data.images.load(str(ROOT/'work/reference-docs/transmission'/filename));im.pack();im.use_fake_user=True
text=bpy.data.texts.new('CV_READ_ME');text.write(root['motionStatus']+'\nTwo separate outer races on one fixed inner race per original figs.42/43. Roller count 12 per row, all dimensions and 7-degree wedge are fitted. Spring endpoints preserve ideal helix centreline length; the two states use constant interpolation because interpolating endpoint meshes would not produce physical spring motion. Actual wire skin is seated with 1-micrometre numerical separation from the roller. This component is not yet installed in the vehicle or browser.\n')
scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=120;scene.render.fps=60;scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_Freewheels.blend'))
(ROOT/'outputs/converter-freewheel-build.json').write_text(json.dumps({'parts':len(REG),'fit':FIT,'sourceImage':'000-0687.jpg','limits':text.as_string()},indent=2),encoding='utf8')
print('CONVERTER FREEWHEELS BUILT',len(REG),flush=True)

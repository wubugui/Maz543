"""Native 543 fan-drive Cardan reconstruction. Separate inspection module until
vehicle mounting is measured; no synthetic installed closure is asserted.
"""
import bpy,bmesh,json,math,sys,ast
from pathlib import Path
from math import sin,cos,pi,sqrt
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cooling_interfaces import build_flange
from cardan_references import annotate,pack_sheets
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
REG=[];root=None
tree=ast.parse((ROOT/'scripts/blender-d12.py').read_text())
names={'C','empty','mat','tag','mesh','prism','box','lathe','cylinder','ring','pipe'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'cardan_helpers','exec'))
root=empty('S543_CARDAN');root['partId']='cooling';root['inspectionOnly']=True
root['dimensionStatus']='408-family cap envelope sourced; 543 suffix equivalence, fork/spline dimensions and vehicle mounting unverified.'
DATA=json.loads((ROOT/'work/cardan-poses.json').read_text());S=DATA['spec']
STEEL=mat('CJ_forged_steel',(.105,.119,.124),.88,.38)
POLISH=mat('CJ_ground_bearing_steel',(.30,.32,.33),.94,.24)
RUBBER=mat('CJ_seal_rubber',(.013,.017,.016),.02,.80)
def mark(o,part,role='internal'):
    o['cardanRole']=role;o['cardanPart']=part;o['sourceId']='MAZ catalog 13.5; MCB 2017 pp.7,24'
    o['dimensionStatus']='28 mm cup, 73 mm cross, 42.5 mm groove span from 408 family; remaining dimensions fitted.'
    return o
def B(name,size,pos,parent,edge=.001):return mark(box(name,size,pos,STEEL,parent,edge=edge),name)
def L(name,profile,parent,material=POLISH,axis='x',role='internal'):
    return mark(lathe(name,profile,(0,0,0),material,parent,axis=axis,n=64,closed=True),name,role)
def boolean(ob,cut,operation='DIFFERENCE'):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob
    mod=ob.modifiers.new('Forged union' if operation=='UNION' else 'Machined passage','BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=cut
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
def apply(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');return bpy.context.object
def finish(ob,width=.0006):
    mod=ob.modifiers.new('Forged fillets and machined edge breaks','BEVEL');mod.width=width;mod.segments=3
    mod=ob.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    return ob
def fork(name,parent,tail,with_flange):
    # Rounded eye and tapered arm are one profile, with a true bearing bore.
    outline=[(-.044,-.014),(-.026,-.020)]+[(.022*cos(-2*pi/3+j*4*pi/3/64),.022*sin(-2*pi/3+j*4*pi/3/64)) for j in range(65)]+[(-.026,.020),(-.044,.014)]
    objects=[]
    for side in [-1,1]:
        points=[(tail*x,z) for x,z in outline]
        # prism axis y maps (u,v) onto (x,z).
        o=mark(prism(name+'_ear_'+str(side),points,side*.02875-.00675,side*.02875+.00675,STEEL,parent,axis='y',edge=0),'Fork forged ear','yoke');objects.append(o)
    bridge=apply(B(name+'_bridge',(.009,.071,.028),(-tail*.040,0,0),parent,0));objects.append(bridge)
    body=objects[0]
    for o in objects[1:]:boolean(body,o,'UNION')
    if with_flange:
        f=build_flange(name+'_flange',parent,STEEL,*sorted([-tail*.050,-tail*.042]),.021)
        f=apply(f);boolean(body,f,'UNION')
    cut=cylinder('TEMP_eye_bore',.01401,.10,(0,0,0),STEEL,parent,axis='y',n=64);boolean(body,cut)
    if with_flange:
        cut=cylinder('TEMP_nut_register',.021,.020,(-tail*.043,0,0),STEEL,parent,n=64);boolean(body,cut)
    body.name=name;mark(finish(body),'543-1308606 flange fork' if with_flange else '543-1308603-B / 543-1308598-B spline fork','yoke')
    return body
def spline(name,parent,start,end,female=False):
    n=S['splineTeeth'];section=[]
    # Fitted straight splines, with distinct lands, flank faces and roots.
    for j in range(n):
        for f,r in [(-.5,.0085),(-.28,.0085),(-.17,.0105),(.17,.0105),(.28,.0085)]:
            a=(j+f)*2*pi/n;section.append(((r+(.00015 if female else 0))*cos(a),(r+(.00015 if female else 0))*sin(a)))
    vs=[];fs=[];n=len(section)
    for x in [start,end]:
        vs.extend((x,y,z) for y,z in section)
        # Match the inner profile's polar angles. An independently uniform
        # outside ring twists cap quads across the spline bore at tooth roots.
        vs.extend((x,.0165*y/math.hypot(y,z),.0165*z/math.hypot(y,z)) for y,z in section) if female else None
    if female:
        for j in range(n):
            k=(j+1)%n;fs += [(j,j+2*n,k+2*n,k),(j+n,k+n,k+3*n,j+3*n),(j,k,k+n,j+n),(j+2*n,j+3*n,k+3*n,k+2*n)]
    else:
        fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    o=mark(mesh(name,vs,fs,POLISH,parent,edge=.00008),'Fitted 12-tooth sliding spline','spline');o['fittedSplineTeeth']=S['splineTeeth'];return o
def spider(name,parent):
    parts=[apply(B(name+'_forged_centre',(.018,.026,.026),(0,0,0),parent,.005))]
    for axis in ['y','z']:parts.append(cylinder(name+'_journal_'+axis,.008,.070,(0,0,0),POLISH,parent,axis=axis,n=64))
    body=parts[0]
    for o in parts[1:]:boolean(body,o,'UNION')
    finish(body,.0008);body=apply(body)
    for axis in ['y','z']:boolean(body,cylinder('TEMP_grease_gallery',.0014,.082,(0,0,0),STEEL,parent,axis=axis,n=24))
    boolean(body,cylinder('TEMP_grease_inlet',.002,.022,(.004,0,0),STEEL,parent,n=24))
    body.name=name;mark(body,'408-2201026-02 cross; envelope from 408-2201025 family')
    mark(cylinder(name+'_grease_hex',.0045,.004,(.0105,0,0),POLISH,parent,n=6),'Grease nipple')
    L(name+'_grease_nipple',[(.0125,.0025),(.016,.0025),(.019,.0014),(.020,.0014),(.020,0),(.0125,0)],parent)
def cap(name,parent,side):
    profile=[(.018,.0114),(.018,.014),(.02075,.014),(.02075,.01325),(.02175,.01325),(.02175,.014),(.0365,.014),(.0365,0),(.035,0),(.035,.0105),(.0203,.0105),(.0203,.0114)]
    o=L(name,[(side*d,r) for d,r in profile],parent,axis='y',role='cover');o['cardanPart']='704902-K6 reference cup'
    L(name+'_seal',[(side*d,r) for d,r in [(.0181,.008),(.0181,.01135),(.0201,.01135),(.0201,.008)]],parent,RUBBER,'y','seal')
    # Open retaining ring in the external cup groove; not a closed washer.
    vs=[];fs=[];n=64
    for d in [.0208,.0217]:
        for r in [.0133,.0148]:
            for j in range(n):a=.30+j*(2*pi-.60)/(n-1);vs.append((r*cos(a),side*d,r*sin(a)))
    for j in range(n-1):fs.extend([(j,j+1,n+j+1,n+j),(2*n+j,3*n+j,3*n+j+1,2*n+j+1),(j,2*n+j,2*n+j+1,j+1),(n+j,n+j+1,3*n+j+1,3*n+j)])
    fs.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
    mark(mesh(name+'_circlip',vs,fs,STEEL,parent,edge=.00008),'400-2201043 retaining ring','clip')
for end in range(2):
    flange=empty(f'CJ_flange_{end}',root);shaft=empty(f'CJ_shaft_{end}',root);crossroot=empty(f'CJ_cross_{end}',root)
    fork(f'CJ_flange_fork_{end}',flange,1 if end==0 else -1,True)
    fork(f'CJ_sliding_fork_{end}',shaft,-1 if end==0 else 1,False)
    if end==0:
        L('CJ_male_neck',[(.035,0),(.035,.013),(.050,.013),(.054,.0105),(.065,.0105),(.065,0)],shaft)
        spline('CJ_male_spline',shaft,.053,S['maleEnd'])
    else:
        spline('CJ_female_spline',shaft,-S['femaleReach'],-.037,True)
    spider(f'CJ_spider_{end}',crossroot)
    for kind,parent in [('flange',flange),('shaft',shaft)]:
        for side in [-1,1]:
            cap(f'CJ_cap_{end}_{kind}_{side}',parent,side)
            holder=empty(f'CJ_needles_{end}_{kind}_{side}',parent)
            for j in range(S['rollerCount']):
                roller=empty(f'CJ_roller_{end}_{kind}_{side}_{j}',holder)
                mark(cylinder(f'CJ_needle_{end}_{kind}_{side}_{j}',S['rollerRadius'],S['rollerLength'],(0,0,0),POLISH,roller,axis='y',n=16),'Fitted full-complement needle roller')
for o in root.children_recursive:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.edges.ensure_lookup_table()
    sharp=[e.calc_face_angle(0)>.52 for e in bm.edges];bm.free()
    for edge,value in zip(o.data.edges,sharp):edge.use_edge_sharp=value
    for face in o.data.polygons:
        face.use_smooth=max(abs(v) for v in face.normal)<.99999
        if o.get('cardanRole')=='spline':
            radii=[math.hypot(o.data.vertices[v].co.y,o.data.vertices[v].co.z) for v in face.vertices]
            face.use_smooth=min(radii)>.0164 and max(abs(v) for v in face.normal)<.99999
for f in DATA['frames']:
    for name,p in f['pose'].items():
        o=bpy.data.objects[name];o.location=C(p['p']);q=p['q'];o.rotation_mode='QUATERNION';o.rotation_quaternion=(q[3],q[0],-q[2],q[1])
        o.keyframe_insert(data_path='location',frame=f['frame']);o.keyframe_insert(data_path='rotation_quaternion',frame=f['frame'])
for o in root.children_recursive:
    if o.animation_data:
        previous=None
        # Component interpolation needs continuous quaternion signs.
        # Pose sampling is dense; hemisphere correction is performed below.
        action=o.animation_data.action
        rotation=[fc for fc in action.fcurves if fc.data_path=='rotation_quaternion']
        for k in range(len(rotation[0].keyframe_points)):
            q=[fc.keyframe_points[k].co.y for fc in rotation]
            if previous and sum(a*b for a,b in zip(q,previous))<0:
                q=[-v for v in q]
                for fc,v in zip(rotation,q):fc.keyframe_points[k].co.y=v
            previous=q
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=600;scene.render.fps=60;scene.frame_set(0);scene.unit_settings.system='METRIC'
collection=bpy.data.collections.new('S543_CARDAN_INSPECTION');scene.collection.children.link(collection)
for o in [root]+list(root.children_recursive):
    for old in list(o.users_collection):old.objects.unlink(o)
    collection.objects.link(o)
report=[{'name':o.name,'part':o.get('cardanPart'),'role':o.get('cardanRole'),'source':o.get('sourceId'),'dimensions':o.get('dimensionStatus')} for o in root.children_recursive if o.type=='MESH']
report=annotate(root)
pack_sheets()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.clip_start=.0001;space.region_3d.view_distance=.70
            space.region_3d.view_location=C((.12,0,.04));space.region_3d.view_rotation=(-C((-.28,.28,.57))).to_track_quat('-Z','Y');space.region_3d.view_perspective='PERSP'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cardan_Master.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in root.children_recursive:
    if o.type=='MESH':o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in root.children_recursive if o.type=='MESH');bpy.ops.object.convert(target='MESH')
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-cardan.glb'),export_format='GLB',use_selection=True,export_yup=True,export_extras=True,export_animations=False,export_apply=True,export_draco_mesh_compression_enable=True)
print('CARDAN_NATIVE',len(report),'meshes',len(DATA['frames'][0]['pose']),'joints',flush=True)

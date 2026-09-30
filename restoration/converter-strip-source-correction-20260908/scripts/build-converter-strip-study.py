"""Saved source-guided curved-strip/contact study, no prescribed spin animation."""
import bpy,bmesh,json,math,sys,ast
from math import sin,cos,pi,sqrt
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_strip_mesh import geometry
DATA=json.loads((ROOT/'work/freewheel-contact/strip-spring-study.json').read_text());FIT=DATA['fit'];REG=[];root=None
def tag(o,*a,**kw):REG.append(o.name);return o
tree=ast.parse((ROOT/'scripts/blender-d12.py').read_text());names={'C','empty','mat','mesh','lathe','cylinder'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'helpers','exec'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
root=empty('S543_CURVED_STRIP_STUDY');root['status']='Quasistatic prescribed roller-centre study. Not installed in the vehicle or freewheel contact solver.'
root['source']='1973 fig.43 callout 4; 2008 543/7310 catalog pump/reactor callout 25. Curved strip interpreted from drawings, precise outline and seating unmeasured.'
STEEL=mat('CS_ground_roller',(.31,.33,.35),.9,.27);CAST=mat('CS_race_section',(.10,.14,.16),.8,.38);SPRING=mat('CS_curved_strip',(.34,.27,.15),.83,.34)
r=FIT['rollerRadiusM'];ri=.056;rho=ri+r;alpha=math.radians(7);d=r+rho*math.cos(alpha)
def boundary(a):
    degrees=math.degrees(a)
    if -13<=degrees<=8:return d/math.cos(a-alpha)
    if degrees< -13:
        t=(degrees+15)/2;return (ri+.002)*(1-t)+(d/math.cos(math.radians(-13)-alpha))*t
    t=(degrees-8)/7;return (d/math.cos(math.radians(8)-alpha))*(1-t)+(ri+.002)*t
def sector(name,inner,outer):
    points=[];count=241
    for x in [-.012,.012]:
        for fun in [inner,outer]:
            for j in range(count):
                a=math.radians(-15+30*j/(count-1));R=fun(a);points.append((x,R*math.cos(a),R*math.sin(a)))
    faces=[]
    for j in range(count-1):
        k=j+1;faces.extend([(j,k,count+k,count+j),(2*count+j,3*count+j,3*count+k,2*count+k),(j,2*count+j,2*count+k,k),(count+j,count+k,3*count+k,3*count+j)])
    for j in [0,count-1]:faces.append((j,count+j,3*count+j,2*count+j))
    return mesh(name,points,faces,CAST,root)
sector('CS_outer_pocket',boundary,lambda a:.084);sector('CS_fixed_inner_section',lambda a:.052,lambda a:ri)
roller=cylinder('CS_roller_12_5x22',r,FIT['rollerLengthM'],(0,0,0),STEEL,root,n=256)
anchor=DATA['restPoints'][0]
def relative(vertices):return [(x,y-anchor[0],z-anchor[1]) for x,y,z in vertices]
vertices,faces=geometry(DATA['rows'][0]['points'],FIT['widthM'],FIT['thicknessM']);strip=mesh('CS_curved_strip',relative(vertices),faces,SPRING,root);strip.location=C((0,*anchor))
strip.shape_key_add(name='Basis');strip.data.shape_keys.use_relative=False
for i,row in enumerate(DATA['rows']):
    if i:
        block=strip.shape_key_add(name=f'Equilibrium_{i:02d}');vertices,_=geometry(row['points'],FIT['widthM'],FIT['thicknessM'])
        for v,p in zip(block.data,relative(vertices)):v.co=C(p)
    else:block=strip.data.shape_keys.key_blocks[0]
    block.interpolation='KEY_LINEAR';strip.data.shape_keys.eval_time=block.frame;strip.data.shape_keys.keyframe_insert('eval_time',frame=i)
    roller.location=C((0,*row['centre']));roller.keyframe_insert('location',frame=i)
    for name,value in [('beta_rad',row['beta']),('spring_force_N',row['forceN']),('spring_energy_J',row['energyJ']),('incremental_stress_Pa',row['maximumIncrementalBendingStressPa'])]:root[name]=value;root.keyframe_insert(data_path='["'+name+'"]',frame=i)
for ob in bpy.data.objects:
    if ob.type=='MESH':
        bm=bmesh.new();bm.from_mesh(ob.data)
        if not ob.data.shape_keys:
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-9);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-10)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
        for face in ob.data.polygons:face.use_smooth=abs(face.normal.x)<.999
    animated=[ob,ob.data.shape_keys if ob.type=='MESH' else None]
    for item in animated:
        if item and item.animation_data:
            for curve in item.animation_data.action.fcurves:
                for key in curve.keyframe_points:key.interpolation='CONSTANT'
text=bpy.data.texts.new('CURVED_STRIP_SOURCE_AND_LIMITS');text.write(root['source']+'\n'+DATA['limits']+'\n26 independent equilibrium frames, no temporal interpolation or roller spin claim. Linear elastic material fit can predict stresses beyond real yield; strength is unaccepted. Old helical-spring force results are not transferable.\n')
im=bpy.data.images.load(str(ROOT/'work/reference-docs/transmission/000-0687.jpg'));im.pack();im.use_fake_user=True
scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=len(DATA['rows'])-1;scene.render.fps=1;scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_CurvedStripStudy.blend'),compress=True)
print('SAVED CURVED STRIP STUDY',len(DATA['rows']),'equilibria',len(strip.data.vertices),'strip vertices',flush=True)

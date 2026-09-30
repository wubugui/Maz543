"""Native MAZ twin-fan / electromagnetic clutch and radiator reconstruction.
Original figs.27,30,31 establish architecture; dimensions and gearing remain fitted.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'scripts/blender-d12.py').read_text(encoding='utf-8')
exec(compile(source[:source.index('# Split aluminium')],str(ROOT/'scripts/blender-d12.py'),'exec'))
from mathutils import Matrix
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
DATA=json.loads((ROOT/'work/cooling-poses.json').read_text());S=DATA['spec'];root=empty('S543_COOLING');root['partId']='cooling'
root['scope']='MAZ twin cooling fans; measured dimensions, gear teeth and complete passages remain open'
def ct(o,part=None,role='cooling-internal',source='MAZ-1973-F31'):
    if o.name.startswith('COOL_blade_bolt_'):role='fan-fastener'
    if role.startswith('radiator') or role=='shutter':source='MAZ-1973-F27'
    if role=='drive-pending':source='MAZ-1973-F30'
    o['coolingPart']=part or o.name;o['coolingRole']=role;o['sourceId']=source
    o['dimensionStatus']='Source topology; all local dimensions, fan/gear curves and shaft ratio fitted';return o
def E(name,parent=root,pos=(0,0,0)):return ct(empty(name,parent,pos))
def R(name,r,inside,length,pos,material=POLISH,parent=root,axis='x',role='cooling-internal'):
    return ct(ring(name,r,inside,length,pos,material,parent,axis,n=64),role=role)
def B(name,size,pos,material=CAST,parent=root,edge=.002,role='cooling-internal'):
    return ct(box(name,size,pos,material,parent,edge=edge),role=role)
def CY(name,r,length,pos,material=POLISH,parent=root,axis='x',n=48,role='cooling-internal'):
    return ct(cylinder(name,r,length,pos,material,parent,axis,n),role=role)
def rod_between(name,a,b,r,material=STEEL,parent=root,role='cooling-internal'):
    a=Vector(a);b=Vector(b);o=CY(name,r,(b-a).length,(0,0,0),material,parent,role=role);o.location=C((a+b)/2);o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((1,0,0)).rotation_difference(C(b-a).normalized());return o
def bolt_at(name,p,parent=root,axis='x',r=.005):
    CY(name+'_head',r,.006,p,STEEL,parent,axis,6)
    R(name+'_washer',r*1.3,r*.6,.0015,p,POLISH,parent,axis)
fanmat=mat('COOL_fan_cast_aluminium',(.22,.24,.22),.82,.42)
black=mat('COOL_radiator_black',(.021,.027,.023),.55,.62)
copper=mat('COOL_enamelled_copper',(.22,.071,.025),.68,.36)
friction=mat('COOL_cast_iron_friction',(.048,.046,.042),.64,.52)
resin=mat('COOL_textolite',(.07,.041,.025),.08,.62)
# Separate water/oil cores; actual flattened tubes and thin cooling plates.
core=E('COOL_radiator');core['coolingRole']='radiator'
for y in [1.205,1.905]:B('COOL_water_tank_'+str(y),(.145,.095,1.16),(-5.265,y,0),black,core,.010,'radiator')
for z in [-.608,.608]:B('COOL_core_side_'+str(z),(.175,.82,.038),(-5.265,1.555,z),PAINT,core,.004,'radiator')
for z in [-.58,.58]:
    for y in [1.18,1.93]:bolt_at(f'COOL_core_bolt_{z}_{y}',(-5.16,y,z),core)
for row in range(3):
  for j in range(56):
    z=-.565+j*.02055
    # Sixteen-sided flattened oval tube, open with 0.45 mm wall.
    center=C((-5.315+row*.05,1.555,z));o=R(f'COOL_water_tube_{row}_{j}',.006,.00555,.607,(-5.315+row*.05,1.555,z),black,core,'y','radiator')
    for v in o.data.vertices:v.co.x=center.x+(v.co.x-center.x)*1.7;v.co.y=center.y+(v.co.y-center.y)*.42
for j in range(92):B(f'COOL_core_fin_{j}',(.139,.00035,1.15),(-5.265,1.252+j*.0066,0),black,core,0,'radiator')
# Fitted three-pass partition locations, partitioned upper/lower tanks remain a
# visual approximation until tank section drawings can be measured.
for z in [-.193,.193]:B(f'COOL_tank_partition_{z}',(.120,.078,.002),(-5.265,1.905,z),BRONZE,core,0,'radiator-internal')
oil=E('COOL_oil_core')
for j in range(35):B(f'COOL_oil_fin_{j}',(.10,.0004,1.12),(-5.265,1.06+j*.0032,0),black,oil,0,'radiator')
for j in range(8):B(f'COOL_oil_flat_tube_{j}',(.012,.108,.021),(-5.265,1.112,-.51+j*.145),black,oil,.001,'radiator')
# Manually linked radiator shutters, independent of the protective front grille.
for j in range(12):
    p=DATA['frames'][0]['pose'][f'COOL_shutter_{j}']['p'];sh=E(f'COOL_shutter_{j}',root,p)
    B(f'COOL_shutter_leaf_{j}',(.004,.638,.1068),(0,0,0),PAINT,sh,.001,'shutter')
    CY(f'COOL_shutter_spindle_{j}',.003,.672,(0,0,0),STEEL,sh,'y',24,'shutter')
    B(f'COOL_shutter_crank_{j}',(.040,.004,.009),(.014,-.345,0),STEEL,sh,.001,'shutter')
link=E('COOL_shutter_link_joint');B('COOL_shutter_link',(.009,.006,1.21),(0,0,0),STEEL,link,.001,'shutter')
for j in range(12):CY(f'COOL_shutter_link_pin_{j}',.0025,.010,(0,0,-.585+j*.1064),POLISH,link,'y',16,'shutter')
# Fan gearbox output shaft, needle bearings, electromagnet, armature, slip-ring
# contacts and spring are distinct parts with their original motion ownership.
for i,side in enumerate([1,-1]):
    z=side*S['fanPosition'][2];mount=E(f'COOL_fan_mount_{i}',root,(S['fanPosition'][0],S['fanPosition'][1],z))
    fan=E(f'COOL_fan_{i}',mount);arm=E(f'COOL_armature_{i}',mount)
    R(f'COOL_shroud_{i}',S['fanRadius']+.014,S['fanRadius']+.006,.125,(-.005,0,0),black,mount,role='shroud')
    for a in [pi/4,3*pi/4,5*pi/4,7*pi/4]:rod_between(f'COOL_shroud_stay_{i}_{a}',(.129,.07*cos(a),.07*sin(a)),(.0525,.302*cos(a),.302*sin(a)),.008,STEEL,mount,'shroud')
    CY(f'COOL_output_shaft_{i}',.018,.22,(.068,0,0),POLISH,arm)
    R(f'COOL_armature_flange_{i}',.087,.018,.007,(-.035,0,0),STEEL,arm)
    R(f'COOL_armature_plate_{i}',.104,.019,.006,(-.027,0,0),STEEL,arm)
    R(f'COOL_friction_ring_{i}',.101,.064,.005,(-.020,0,0),friction,fan)
    # U-shaped annular magnet body and windings around its core.
    ct(lathe(f'COOL_magnet_{i}',[(-.0219,.029),(-.0219,.105),(.031,.105),(.031,.091),(-.008,.091),(-.008,.044),(.031,.044),(.031,.029)],(0,0,0),STEEL,fan,n=96,closed=True),role='clutch-cover')
    for k in range(10):R(f'COOL_coil_turn_{i}_{k}',.086,.049,.0025,(-.004+k*.0031,0,0),copper,fan)
    R(f'COOL_insulating_ring_{i}',.106,.069,.004,(.035,0,0),resin,fan)
    R(f'COOL_contact_ring_{i}',.098,.084,.002,(.038,0,0),BRONZE,fan)
    for j,a in enumerate([-.45,.45]):
      brush=E(f'COOL_brush_joint_{i}_{j}',mount)
      p=(.049,.09*cos(a),.09*sin(a));B(f'COOL_brush_{i}_{a}',(.02,.007,.008),p,RUBBER,brush,.0006)
      B(f'COOL_brush_holder_{i}_{a}',(.023,.012,.014),(.061,p[1],p[2]),resin,mount,.001)
    B(f'COOL_ground_brush_{i}',(.02,.010,.010),(.187,0,0),RUBBER,mount,.001)
    for k,x in enumerate([.007,.027]):
      R(f'COOL_needle_inner_race_{i}_{k}',.0196,.018,.014,(x,0,0),POLISH,arm)
      R(f'COOL_needle_outer_race_{i}_{k}',.029,.0244,.014,(x,0,0),STEEL,fan,role='bearing-cover')
      for j in range(24):
        joint=E(f'COOL_needle_joint_{i}_{k}_{j}',mount);CY(f'COOL_needle_{i}_{k}_{j}',.0024,.011,(0,0,0),POLISH,joint,n=20)
    spring=[(t/160*.022,.026*cos(t/160*10*pi),.026*sin(t/160*10*pi)) for t in range(161)]
    spring_joint=E(f'COOL_spring_{i}',mount);ct(pipe(f'COOL_release_spring_{i}',spring,.0018,STEEL,spring_joint))
    R(f'COOL_gearcase_{i}',.072,.061,.13,(.129,0,0),CAST,mount,role='housing')
    for x in [.078,.185]:R(f'COOL_output_bearing_{i}_{x}',.032,.018,.015,(x,0,0),POLISH,mount)
    CY(f'COOL_rear_cover_{i}',.070,.010,(.2,0,0),CAST,mount,role='housing')
    for j in range(6):
      a=j*pi/3;bolt_at(f'COOL_cover_bolt_{i}_{j}',(.208,.059*cos(a),.059*sin(a)),mount)
    # Twelve twisted airfoil sheets from original blade count; sections fitted.
    for j in range(12):
      vs=[];fs=[];N=18;M=12;a=j*pi/6
      for surface in [-1,1]:
       for k in range(N+1):
        t=k/N;r=.100+t*(S['fanRadius']-.100);chord=.077-.019*t;pitch=.54-.25*t
        for l in range(M+1):
          q=l/M;u=(q-.5)*chord;thick=surface*.0018*sin(pi*q)+.003*sin(pi*q)
          axial=.013+u*sin(pitch)+thick*cos(pitch);az=a+(.016*t+u*cos(pitch))/r
          vs.append((axial,r*cos(az),r*sin(az)))
      count=(N+1)*(M+1)
      for k in range(N):
       for l in range(M):
        q=k*(M+1)+l;fs +=[(q,q+1,q+M+2,q+M+1),(q+count,q+count+M+1,q+count+M+2,q+count+1)]
      for k in range(N):
       for l in [0,M]:q=k*(M+1)+l;fs.append((q,q+M+1,q+count+M+1,q+count))
      for k in [0,N]:
       for l in range(M):q=k*(M+1)+l;fs.append((q,q+count,q+count+1,q+1))
      ct(mesh(f'COOL_fan_blade_{i}_{j}',vs,fs,fanmat,fan,smooth=True),part='Twelve-blade aluminium impeller',role='fan-blade')
      for dr in [0,.014]:bolt_at(f'COOL_blade_bolt_{i}_{j}_{dr}',(.044,(.107+dr)*cos(a),(.107+dr)*sin(a)),fan,r=.004)
    # Fitted open Cardan line. Its detailed bevel meshes and universal-joint
    # velocity constraints are explicitly pending; never label this a solved train.
    lower=(-4.82,1.39,side*.055);upper=(-4.89,1.52,z)
    rod_between(f'COOL_cardan_{i}',lower,upper,.015,STEEL,root,'drive-pending')
    for k,p in enumerate([lower,upper]):
      CY(f'COOL_cardan_cross_{i}_{k}',.011,.060,p,STEEL,root,'x',32,'drive-pending')
      CY(f'COOL_cardan_cross2_{i}_{k}',.011,.060,p,STEEL,root,'y',32,'drive-pending')
    B(f'COOL_support_leg_{i}',(.075,.25,.045),(-4.89,1.30,z),CAST,root,.009,'housing')
    ct(pipe(f'COOL_gear_oil_line_{i}',[(-4.85,1.31,0),(-4.91,1.43,z),(-4.85,1.61,z)],.004,STEEL,root),role='drive-pending')
# Lower drive casing and crank coupling aligned with the new installed crank.
R('COOL_lower_drive_housing',.096,.078,.13,(-4.82,1.39,0),CAST,root,role='housing')
CY('COOL_crank_torsion',.013,.18,(-4.74,1.39,0),STEEL,root,role='drive-pending')
for j in range(8):a=j*pi/4;bolt_at(f'COOL_lower_mount_{j}',(-4.745,1.39+.085*cos(a),.085*sin(a)),root)
# Main hoses connect to the rebuilt pump and both existing exhaust-jacket exits.
for s in [-1,1]:
    ct(pipe(f'COOL_hot_hose_{s}',[(-3.52,1.9,s*.37),(-4.22,2.04,s*.41),(-4.91,1.97,s*.43),(-5.26,1.92,s*.44)],.022,RUBBER,root),role='pipe',source='MAZ-1973-F27')
ct(pipe('COOL_return_hose',[(-5.26,1.19,0),(-5.13,1.10,0),(-4.95,.905,0),(-4.814,.905,0)],.022,RUBBER,root),role='pipe',source='MAZ-1973-F27')
CY('COOL_expansion_tank',.071,.23,(-4.65,2.12,.42),CAST,root,'y',64,'housing')
CY('COOL_expansion_cap',.039,.023,(-4.65,2.248,.42),STEEL,root,'y',12,'housing')
ct(pipe('COOL_vent_line',[(-4.65,2.13,.42),(-4.9,2.04,.42),(-5.26,1.96,.44)],.004,RUBBER,root),role='pipe',source='MAZ-1973-F27')
exec(compile((ROOT/'scripts/cooling-lower-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/cooling-lower-detail.py'),'exec'))
exec(compile((ROOT/'scripts/cooling-upper-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/cooling-upper-detail.py'),'exec'))
exec(compile((ROOT/'scripts/cooling-clutch-spring.py').read_text().split("if __name__")[0],str(ROOT/'scripts/cooling-clutch-spring.py'),'exec'));update_springs()
for o in bpy.data.objects:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.edges.ensure_lookup_table();sharp=[e.calc_face_angle(0)>.52 for e in bm.edges];bm.free()
    for edge,val in zip(o.data.edges,sharp):edge.use_edge_sharp=val
    for f in o.data.polygons:
        if max(abs(v) for v in f.normal)>.99999:f.use_smooth=False
col=bpy.data.collections.new('S543_COOLING');bpy.context.scene.collection.children.link(col)
from d12_asset import engine_descendants
for o in [root]+engine_descendants(root):
    for old in list(o.users_collection):old.objects.unlink(o)
    col.objects.link(o)
# Bake the same causal start/coast sequence used by the engine and web.
for name,q in DATA['frames'][0]['pose'].items():
    o=bpy.data.objects[name];o.location=C(q['p']);o.rotation_euler=(q['rx'],0,q.get('ry',0))
    for f in DATA['frames']:
        p=f['pose'][name];o.location=C(p['p']);o.rotation_euler=(p['rx'],0,p.get('ry',0));o.scale=(p.get('sx',1),1,1)
        o.keyframe_insert(data_path='location',frame=f['frame']);o.keyframe_insert(data_path='rotation_euler',frame=f['frame']);o.keyframe_insert(data_path='scale',frame=f['frame'])
    for fc in o.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='LINEAR'
from cooling_spring_geometry import bake_springs
bake_springs(DATA['frames'],S)
scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=600;scene.render.fps=60;scene.frame_set(0);scene.unit_settings.system='METRIC'
exec(compile((ROOT/'scripts/cooling-lower-surfaces.py').read_text(encoding='utf-8'),str(ROOT/'scripts/cooling-lower-surfaces.py'),'exec'))
from cooling_references import attach as attach_cooling_references
attach_cooling_references(root)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'),compress=True)
report=[{'name':o.name,'role':o.get('coolingRole'),'source':o.get('sourceId'),'dimensions':o.get('dimensionStatus')} for o in engine_descendants(root) if o.type in ['MESH','CURVE']]
(ROOT/'outputs/cooling-parts-register.json').write_text(json.dumps(report,indent=2))
# Batch only static siblings with identical visibility semantics.
bpy.ops.object.select_all(action='DESELECT')
for o in engine_descendants(root):
    if o.type in ['MESH','CURVE'] and not o.get('parametricSpring'):o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in engine_descendants(root) if o.type=='MESH');bpy.ops.object.convert(target='MESH')
for holder in [root]+[o for o in engine_descendants(root) if o.type=='EMPTY']:
    batches={}
    for o in holder.children:
        if o.type=='MESH' and not o.get('parametricSpring'):batches.setdefault((o.data.materials[0].name,o.get('coolingRole')),[]).append(o)
    for key,objects in batches.items():
        if len(objects)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=holder.name+'_'+key[0]+'_'+key[1];o['detail_meshes']=len(objects)
bpy.ops.object.select_all(action='DESELECT')
for o in [root]+engine_descendants(root):o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-cooling.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_morph=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16)
print('COOLING_NATIVE_AND_GLB',len(report),flush=True)

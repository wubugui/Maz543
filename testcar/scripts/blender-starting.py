"""Editable C5 inertia drive and MZN-2 gear pump from original component sections.
Dimensions, tooth form, unpictured motor rotors and installation remain reconstructed.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Reuse established metric mesh/lathe/pipe primitives; no generic imported engine.
source=(ROOT/'scripts/blender-d12.py').read_text(encoding='utf-8')
exec(compile(source[:source.index('# Split aluminium')],str(ROOT/'scripts/blender-d12.py'),'exec'))
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
REG=[];ACTIVE_SOURCE='C5-F122'
def tag(o,part,source='C5-F122',role='internal',confidence='section-guided topology; all dimensions reconstructed'):
    source=ACTIVE_SOURCE if source in ['D12-F14','KMZ-525A','C5-F122'] else source
    o['startingPart']=part;o['sourceId']=source;o['dimensionStatus']=confidence;o['startingRole']=role
    REG.append({'node':o.name,'part':part,'source':source,'role':role,'dimensions':confidence});return o
SPEC=json.loads((ROOT/'work/starting-poses.json').read_text())['spec']
root=empty('S543_STARTING');root['partId']='starting';root['startingSpec']=json.dumps(SPEC);root['revision']=4
c5=empty('C5_STARTER',root,SPEC['starterPosition']);c5['mount']='engine-local; vehicle right side'
rotor=empty('C5_rotor',c5);drive=empty('C5_drive',c5);pinion=empty('C5_pinion',c5)
COPPER=mat('Starting_contact_copper',(.30,.13,.045),.85,.37)
FIBRE=mat('Starting_friction_fibre',(.12,.082,.037),.05,.84)

def gear(name,teeth,module,width,bore,parent,pos=(0,0,0),role='internal'):
    # Involute flanks, 20 degree reconstructed pressure angle. The original
    # pinion tooth count is 11; ring count, pitch and profiles are not measured.
    key='c5-pinion' if name=='C5_11_tooth_pinion' else 'c5-ring' if name=='C5_flywheel_involute_ring' else 'mzn-gear'
    data=json.loads((ROOT/('work/'+key+'-profile.json')).read_text());points=data['sectionVertices'];n=len(points);outer=data['outerCount']
    vs=[(x,y,z) for x in [-width/2,width/2] for y,z in points];fs=[]
    for tri in data['capTriangles']:fs.extend([tuple(reversed(tri)),tuple(i+n for i in tri)])
    for lo,hi in [(0,outer),(outer,n)]:
        for j in range(lo,hi):q=lo+(j-lo+1)%(hi-lo);fs.append((j,q,q+n,j+n))
    ob=mesh(name,vs,fs,POLISH,parent,smooth=False,source=ACTIVE_SOURCE,role=role);ob.location=C(pos)
    ob['toothCount']=teeth;ob['moduleStatus']='reconstructed';return ob

def spring(name,x0,x1,r,wire,turns,parent):
    pts=[(x0+(x1-x0)*i/192,r*cos(i/192*turns*2*pi),r*sin(i/192*turns*2*pi)) for i in range(193)]
    return pipe(name,pts,wire,STEEL,parent)

# C5 stator enclosure, removable brush end, drive nose with open output bore.
lathe('C5_motor_yoke',[(-.178,.064),(-.174,.086),(-.163,.088),(.082,.088),(.096,.083),(.096,.064)],(0,0,0),PAINT,c5,n=80,closed=True,role='cover',source='C5-2S-PHOTO')
lathe('C5_rear_end_cover',[(-.195,.021),(-.195,.054),(-.183,.079),(-.170,.083),(-.165,.072),(-.182,.050),(-.182,.021)],(0,0,0),COVER,c5,n=64,closed=True,role='cover',source='C5-2S-PHOTO')
lathe('C5_drive_nose',[ (.092,.070),(.097,.084),(.153,.077),(.180,.059),(.242,.059),(.269,.038),(.272,.024),(.257,.017),(.242,.020),(.226,.047),(.163,.047),(.14,.064),(.092,.064)],(0,0,0),COVER,c5,n=80,closed=True,role='cover')
for x in [-.165,.082]:ring('C5_yoke_band_'+str(x),.090,.087,.014,(x,0,0),STEEL,c5,role='cover',source='C5-2S-PHOTO')
for k in range(4):
    a=k*pi/2+pi/4;y=.066*cos(a);z=.066*sin(a)
    cylinder('C5_tie_rod_'+str(k),.003,.29,(-.03,y,z),STEEL,c5,n=16,source='C5-2S-PHOTO')
    bolt('C5_rear_nut_'+str(k),(-.196,y,z),c5,'x',.005,role='cover')
for k in range(8):
    a=k*pi/4;o=box('C5_end_reinforcement_'+str(k),(.013,.034,.008),(-.182,.054,0),COVER,c5,.002,role='cover');o.rotation_euler.x=a
# The unpictured electric armature/windings are explicitly left as an envelope;
# do not invent a pole, brush or commutator count from another starter model.
cylinder('C5_armature_envelope_UNMEASURED',.052,.228,(-.031,0,0),STEEL,rotor,n=64,source='C5-MOTOR-ENVELOPE')
cylinder('C5_armature_shaft',.0115,.407,(.024,0,0),POLISH,rotor,n=40)
for x in [-.175,.084,.228]:ring('C5_shaft_bearing_'+str(x),.024,.0116,.016,(x,0,0),BRONZE,c5)
# Four-start spline is an explicitly fitted visual parameter. Lead equals the
# numerical lead so relative sleeve rotation and axial displacement agree.
for k in range(4):
    vs=[];fs=[]
    for i in range(161):
        x=.094+i/160*.184;a=x/SPEC['helixLead']*2*pi+k*pi/2
        for da,r in [(-.12,.0115),(-.10,.0142),(.10,.0142),(.12,.0115)]:vs.append((x,r*cos(a+da),r*sin(a+da)))
    for i in range(160):
        for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    fs.extend([(3,2,1,0),(640,641,642,643)])
    mesh('C5_helical_spline_'+str(k),vs,fs,POLISH,rotor,smooth=True)
# Fig.122 numbered parts: spring, cups, compliant washers, pressure ring,
# friction pairs, bushes, retaining rings and tail shaft remain separate meshes.
spring('C5_buffer_spring_1',.083,.112,.020,.0023,5,drive)
lathe('C5_cup_2',[(.106,.018),(.106,.042),(.113,.045),(.143,.045),(.143,.041),(.114,.039),(.114,.018)],(0,0,0),STEEL,drive,n=48,closed=True)
for k in range(3):
    ring('C5_compliant_washer_3_'+str(k),.039,.020,.0017,(.116+k*.003,0,0),FIBRE,drive)
ring('C5_pressure_ring_4',.041,.019,.004,(.126,0,0),STEEL,drive)
for k in range(4):
    ring('C5_friction_washer_5_'+str(k),.040,.020,.002,(.130+k*.0045,0,0),FIBRE,drive)
    ring('C5_friction_washer_17_'+str(k),.039,.019,.002,(.132+k*.0045,0,0),POLISH,pinion)
ring('C5_bush_6',.019,.0145,.045,(.130,0,0),BRONZE,drive)
ring('C5_washer_7',.042,.018,.003,(.150,0,0),POLISH,drive)
lathe('C5_cup_8',[(.143,.047),(.156,.047),(.163,.031),(.162,.018),(.154,.018),(.151,.041),(.143,.041)],(0,0,0),STEEL,pinion,n=64,closed=True)
ring('C5_washer_9',.029,.015,.003,(.165,0,0),POLISH,pinion)
returnSpring=empty('C5_return_spring',c5,(.192,0,0));spring('C5_spring_10',0,.10,.009,.0015,9,returnSpring)
ring('C5_circlip_11',.016,.012,.0017,(.330,0,0),STEEL,pinion)
cylinder('C5_stop_disk_12',.016,.003,(.334,0,0),STEEL,pinion)
ring('C5_tailshaft_13',.017,.0105,.172,(.229,0,0),POLISH,pinion)
ring('C5_bush_14',.015,.0117,.030,(.309,0,0),BRONZE,pinion)
ring('C5_sleeve_15',.022,.018,.063,(.186,0,0),STEEL,pinion)
box('C5_key_16',(.043,.004,.006),(.130,.015,0),STEEL,drive,.0004)
for s in [-1,1]:
    ob=ring('C5_half_ring_18_'+str(s),.018,.014,.003,(.101,0,0),STEEL,drive)
    # Preserve split halves as real topology, not overlapping full rings.
    bm=bmesh.new();bm.from_mesh(ob.data);verts=[v for v in bm.verts if v.co.z*s<0];bmesh.ops.delete(bm,geom=verts,context='VERTS');bm.to_mesh(ob.data);bm.free()
gear('C5_11_tooth_pinion',11,SPEC['module'],SPEC['gearWidth'],.012,pinion,(.291,0,0))
for z in [-.051,.051]:
    box('C5_mount_foot_'+str(z),(.087,.026,.034),(.080,-.085,z),COVER,c5,.003,role='visible')
    bolt('C5_mount_bolt_'+str(z),(.080,-.106,z),c5,'y',.006,role='visible')
ring('C5_lifting_eye',.016,.010,.005,(-.030,.105,0),STEEL,c5,'z',32,role='visible',source='C5-2S-PHOTO')
cylinder('C5_power_insulator',.019,.021,(-.126,.093,0),RUBBER,c5,'y',role='visible',source='C5-2S-PHOTO')
cylinder('C5_power_terminal',.008,.022,(-.126,.108,0),COPPER,c5,'y',n=6,role='visible',source='C5-2S-PHOTO')
pipe('C5_terminal_boot',[(-.126,.119,0),(-.124,.137,0),(-.092,.143,0),(-.041,.136,0)],.011,RUBBER,c5,role='visible',source='C5-2S-PHOTO')
fly=empty('C5_FLYWHEEL_RING',root,(.669,.07,0));gear('C5_flywheel_involute_ring',132,SPEC['module'],.031,.298,fly,role='visible')
# MZN is a chassis-mounted component; browser/native attachment keeps it out
# of the engine mount hierarchy. Its coordinates are a fit pending an A photo.
ACTIVE_SOURCE='MZN-F24';pump=empty('MZN_PREOIL',root);pump['mount']='right frame rail; coordinates fitted'
pm=empty('MZN_rotor',pump);pg=empty('MZN_driven',pump,(0,.034,0))
lathe('MN1_motor_case',[(-.228,.027),(-.222,.055),(-.206,.062),(-.062,.062),(-.048,.057),(-.037,.044),(-.037,.029),(-.050,.048),(-.20,.050),(-.217,.025)],(0,0,0),PAINT,pump,n=64,closed=True,role='cover',source='MZN-PHOTO')
ring('MN1_rear_band',.064,.061,.027,(-.206,0,0),STEEL,pump,role='cover',source='MZN-PHOTO')
cylinder('MN1_rotor_envelope_UNMEASURED',.035,.136,(-.139,0,0),STEEL,pm,source='MN1-MOTOR-ENVELOPE',role='envelope')
cylinder('MN1_rotor_shaft',.008,.215,(-.090,0,0),POLISH,pm)
exec(compile((ROOT/'scripts/starting-motor-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/starting-motor-detail.py'),'exec'))
ring('MZN_coupling_3',.015,.0085,.025,(-.039,0,0),STEEL,pm)
for k in range(12):
    a=k/12*2*pi;o=box('MZN_coupling_spline_'+str(k),(.022,.003,.003),(-.040,.015,0),POLISH,pm,.0003);o.rotation_euler.x=a
for y in [0,.034]:
    ring('MZN_oil_seal_5_'+str(y),.015,.008,.006,(-.004,y,0),RUBBER,pump)
    ring('MZN_shaft_bush_'+str(y),.012,.008,.008,(.020,y,0),BRONZE,pump)
gear('MZN_drive_gear_7',12,.034/12,.024,.008,pm,(.014,0,0))
gear('MZN_driven_gear_6',12,.034/12,.024,.008,pg,(.014,0,0))
cylinder('MZN_driven_shaft',.0078,.070,(.005,0,0),POLISH,pg)
# A real dual bore pump body with continuous peripheral wall and separate cap.
poly=[]
for cy,start in [(.034,-pi/2),(0,pi/2)]:
    for j in range(33):
        a=start+j*pi/32;poly.append((cy+.032*cos(a),.032*sin(a)))
body=prism('MZN_pump_casting_4',poly,-.025,.031,CAST,pump,edge=.001,role='cover')
for y in [0,.034]:
    cut=cylinder('MZN_cavity_tool',.0203,.08,(.01,y,0),CAST,pump,n=64)
    bpy.context.view_layer.objects.active=body;mod=body.modifiers.new('Genuine gear chamber','BOOLEAN');mod.object=cut;mod.operation='DIFFERENCE';bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
cover=prism('MZN_pump_cover_8',poly,.032,.039,CAST,pump,edge=.001,role='cover')
for y,z in [(-.018,-.021),(-.018,.021),(.052,-.021),(.052,.021)]:bolt('MZN_cap_fastener_'+str((y,z)),(.043,y,z),pump,'x',.004,role='cover')
# Separate fluid systems: the jacket and two coolant necks never merge into
# the inlet/outlet oil ports. The section shows this lateral heated cavity.
ring('MZN_coolant_jacket_A',.014,.009,.086,(.002,.017,.043),CAST,pump,n=48,role='visible')
for s in [-1,1]:
    pipe('MZN_coolant_neck_'+str(s),[(s*.043,.017,.043),(s*.050,.018,.043),(s*.052,.040,.043)],.007,CAST,pump,role='visible')
    ring('MZN_oil_port_'+str(s),.012,.006,.022,(.010,.017,s*.041),CAST,pump,'z',n=6,role='visible')
for k in range(4):
    a=k*pi/2+pi/4;y=.049*cos(a);z=.049*sin(a)
    cylinder('MN1_tie_rod_'+str(k),.0025,.174,(-.131,y,z),STEEL,pump,n=16,role='visible',source='MZN-PHOTO')
    bolt('MN1_tie_nut_'+str(k),(-.224,y,z),pump,'x',.004,role='visible')
for x in [-.18,-.07]:
    box('MZN_cradle_'+str(x),(.035,.014,.116),(x,-.065,0),STEEL,pump,.002,role='visible',source='MZN-MOUNT-FIT')
    for z in [-.046,.046]:bolt('MZN_cradle_bolt_'+str((x,z)),(x,-.074,z),pump,'y',.004,role='visible')
# Exclude temporary boolean tools from the final part register.
REG=[r for r in REG if bpy.data.objects.get(r['node'])]
# Lathed cylindrical walls are smooth; machined shoulders and annular end faces
# keep split normals. Smoothing across those corners makes solid metal look soft.
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    for edge in bm.edges:
        if len(edge.link_faces)==2 and edge.calc_face_angle()>.52:edge.smooth=False
    bm.to_mesh(ob.data);bm.free()
from suspension_asset import descendants
collection=bpy.data.collections.new('S543_STARTING');bpy.context.scene.collection.children.link(collection)
for ob in [root]+descendants(root):
    for cc in list(ob.users_collection):cc.objects.unlink(ob)
    collection.objects.link(ob)
poses=json.loads((ROOT/'work/starting-poses.json').read_text());scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=poses['frames'][-1]['frame'];scene.render.fps=60
for f in poses['frames']:
    for name,p in f['pose'].items():
        ob=bpy.data.objects.get(name)
        if ob:
            ob.location=C(p['p']);ob.rotation_euler.x=p['rx'];ob.scale.x=p.get('sx',1)
            for channel in ['location','rotation_euler','scale']:ob.keyframe_insert(channel,frame=f['frame'])
scene.frame_set(0)
refs=bpy.data.collections.new('STARTING_REFERENCES');scene.collection.children.link(refs)
for path in ['1973-c5-drive-fig122.jpg','1973-mzn2-fig24.jpg','07-c5-2s-starter.jpg','08-mzn2-mn1-prelubrication.jpg','motor-internals/candidate-mn1-6020.jpg','motor-internals/candidate-mn1-6022.jpg','motor-internals/c5-2s-full-section-native.png','source-text/1977-c5-installation-p338-339.webp']:
    im=bpy.data.images.load(str(ROOT.parent/'external/maz543-references/starting'/path));im.pack();ob=bpy.data.objects.new('REF_'+path,None);refs.objects.link(ob);ob.empty_display_type='IMAGE';ob.data=im;ob.hide_render=True;ob.hide_viewport=True
notes=bpy.data.texts.new('STARTING_SOURCE_AND_LIMITS');notes.write((ROOT/'docs/STARTING_REFERENCE_REGISTER.md').read_text(encoding='utf-8'))
scene.unit_settings.system='METRIC'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MAZ543A_Starting_Master.blend'),compress=True)
(OUT/'starting-parts-register.json').write_text(json.dumps(REG,indent=2),encoding='utf-8')
# Individual native pieces remain editable; apply modifiers before web batching.
bpy.ops.object.select_all(action='DESELECT');pieces=[o for o in descendants(root) if o.type in ['MESH','CURVE']]
for o in pieces:o.select_set(True)
bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.convert(target='MESH')
for holder in [root]+[o for o in descendants(root) if o.type=='EMPTY']:
    batches={}
    for ob in holder.children:
        if ob.type=='MESH':batches.setdefault((ob.data.materials[0].name,ob.get('startingRole')),[]).append(ob)
    for key,batch in batches.items():
        if len(batch)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for ob in batch:ob.select_set(True)
        bpy.context.view_layer.objects.active=batch[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=holder.name+'_'+key[0]+'_'+str(key[1]);ob['detail_meshes']=len(batch);ob['startingRole']=key[1]
bpy.ops.object.select_all(action='DESELECT')
for ob in [root]+descendants(root):
    ob.select_set(True)
    if ob.type=='MESH':
        tri=ob.modifiers.new('Web tangent triangulation','TRIANGULATE');tri.min_vertices=5
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-starting.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
print('STARTING_EXPORTED',len(REG),flush=True)

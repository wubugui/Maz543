"""Source-guided wood-case/three-four-chamber battery study, never installed.

Only native primitives, curves and Boolean/Bevel modifiers create geometry.
Overall published envelope is retained as a reference gauge; internal and
component dimensions are FITTED and omitted covers prevent assembly acceptance.
"""
import bpy,bmesh,math,json,hashlib,itertools
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-12st70-structure-20261001';OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='12ST70_FAMILY_STRUCTURE_STUDY';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.;scene.unit_settings.length_unit='MILLIMETERS'
root=bpy.data.objects.new('BATTERY_STRUCTURE_NOT_VEHICLE_INSTALLATION',None);scene.collection.objects.link(root)
root['status']='UNACCEPTED_STRUCTURE_STUDY; NO_VEHICLE_INSTALLATION'
root['revision_caveat']='1977 p206 prose says12-ST-70; fig128 label says12ST-70M.1983 guide gives common structural description and same nominal envelope; exact production batch not resolved.'
root['source1977']='https://drive.google.com/file/d/1quwh1UlmlDyw-WHAIPwLYbylRmNDXUr1/view?usp=drivesdk p206 fig128'
root['source1983']='https://www.compancommand.com/literatura/Avtomob/Akkum_Batarei_1983.pdf PDF pp5,11'
root['published_nominal_envelope_m']=[.587,.238,.239]
root['calibration']='Component sizes, wall thickness, can spacing, cap and link profiles, lug holes and shades FITTED. Reference gauge does not certify the incomplete assembly dimensions.'
root['unmodeled']='Exact plate packs/separators and their count; electrolyte; copper inserts; protective terminal hood; pressed-wood top cover; exact carrying hardware; vehicle battery box and four-unit installation.'
parts=[];tools=[];register=[]
def material(name,color,metal=0,rough=.4):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;return m
wood=material('Acid-resistant dark lacquer on wood | finish fitted',(.028,.022,.017),0,.45)
ebonite=material('Ebonite four-chamber tanks | documented family',(.018,.022,.024),0,.34)
lead=material('Lead connectors | copper inserts unmodeled',(.25,.26,.25),.72,.42)
steel=material('Steel case bands | fitted thickness',(.10,.12,.13),.85,.34)
plugmat=material('Dark filler plugs | exact cap revision unconfirmed',(.025,.029,.03),0,.39)
def tag(o,role,source,detail):
    o.parent=root;o['role']=role;o['source']=source;o['dimension_status']='FITTED';o['detail']=detail;parts.append(o);register.append({'name':o.name,'role':role,'source':source,'detail':detail,'dimensions':'FITTED'});return o
def cube(name,size,loc,mat=None,bevel=0,role=None,detail=''):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    if bevel:m=o.modifiers.new('Native small edge break fitted','BEVEL');m.width=bevel;m.segments=3
    if role:tag(o,role,'1977 fig128;1983 p11',detail)
    return o
def cylinder(name,r,depth,loc,mat=None,axis='Z',role=None,detail=''):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name
    if axis=='X':o.rotation_euler.y=math.pi/2
    if mat:o.data.materials.append(mat)
    if role:tag(o,role,'1977 fig128;1983 p11',detail)
    return o
def boolean(o,cutter,operation='DIFFERENCE'):
    m=o.modifiers.new('Native exact '+operation,'BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=cutter;cutter.hide_render=True;cutter.hide_set(True);cutter.display_type='WIRE';cutter.parent=root;cutter['construction_only']=True;tools.append(cutter)
def edge_break(o,width=.0007):
    m=o.modifiers.new('Native edge break fitted','BEVEL');m.width=width;m.segments=2
def welded_curve(o):
    name=o.name
    src=o.copy();src.data=o.data.copy();src.name='SOURCE_CURVE_'+name;scene.collection.objects.link(src);src.parent=root;src.hide_render=True;src.hide_set(True);src['construction_only']=True
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object
    mod=o.modifiers.new('Native Weld curve cap and profile seams','WELD');mod.merge_threshold=1e-7
    o['editable_curve_source']=src.name
    return o
L,W,H,t=.565,.230,.2175,.008
cube('WOOD_bottom',(L,W,t),(0,0,t/2),wood,.0007,'wood_case','Five-board layout is a reconstruction, not factory joinery')
for sign in [-1,1]:
    cube('WOOD_long_side_'+str(sign),(L,t,H-t),(0,sign*(W-t)/2,(H+t)/2),wood,.0007,'wood_case','Documented wood case, coating BT-783; finish shade fitted')
    cube('WOOD_end_'+str(sign),(t,W-2*t,H-t),(sign*(L-t)/2,0,(H+t)/2),wood,.0007,'wood_case','End board; attachment and carrying hardware unresolved')
innerL=L-2*t;gap=.016;tankL=(innerL-2*gap)/3;tankW=W-2*t-.002;tankH=.198;wall=.003;floor=.005
cell_centres={};tanks=[]
for block in range(3):
    x=(block-1)*(tankL+gap)
    tank=cube(f'EBONITE_block_{block+1}_FOUR_CHAMBERS',(tankL,tankW,tankH),(x,0,t+tankH/2),ebonite,0,'four_chamber_tank','1983 explicitly specifies three four-chamber ebonite tanks, not12 separate pots');tanks.append(tank)
    cw=(tankW-3*wall)/2;cl=(tankL-3*wall)/2
    for ix,iy in itertools.product(range(2),repeat=2):
        cx=x+(-1 if ix==0 else 1)*(cl+wall)/2;cy=(-1 if iy==0 else 1)*(cw+wall)/2
        cut=cube(f'TOOL_block{block+1}_chamber{ix}_{iy}',(cl,cw,tankH-floor+.006),(cx,cy,t+floor+(tankH-floor+.006)/2))
        boolean(tank,cut)
        cell_centres[(block*2+ix,iy)]=(cx,cy)
    edge_break(tank,.0005)
for i in range(2):
    x=(-.5 if i==0 else .5)*(tankL+gap)
    band=cube('STEEL_tie_band_'+str(i+1),(.010,W+.003,H+.003),(x,0,H/2),steel,0,'steel_band','Two steel bands pass between the three tanks; clamp force/joinery unmodeled')
    cut=cube('TOOL_band_inside_'+str(i+1),(.014,W+.0004,H+.0004),(x,0,H/2));boolean(band,cut);edge_break(band,.0003)
lids=[];plugs=[];posts={};lidZ=t+tankH+.003
path=[(i,0) for i in range(6)]+[(i,1) for i in reversed(range(6))]
for order,key in enumerate(path):
    cx,cy=cell_centres[key];direction=1 if key[1]==0 else -1;cell=order+1
    lid=cube(f'CELL_{cell:02d}_separate_lid',(cl+wall*.6,cw+wall*.6,.006),(cx,cy,lidZ),ebonite,0,'cell_lid','Separate cell closure; sealing details unresolved');lids.append(lid)
    hole=cylinder(f'TOOL_cell{cell}_fill_opening',.0085,.016,(cx,cy,lidZ));boolean(lid,hole)
    for polarity,dx in [('negative',-.022*direction),('positive',.022*direction)]:
        cut=cylinder(f'TOOL_cell{cell}_{polarity}_feedthrough',.0066,.016,(cx+dx,cy,lidZ));boolean(lid,cut)
        post=cylinder(f'CELL_{cell:02d}_{polarity}_post',.006,.017,(cx+dx,cy,lidZ+.004),lead,role='lead_post',detail='Documented post; copper insert and hermetic feedthrough not modeled')
        posts[(cell,polarity)]=(cx+dx,cy,lidZ+.0125)
    edge_break(lid,.0005)
    plug=cylinder(f'CELL_{cell:02d}_filler_plug',.011,.016,(cx,cy,lidZ+.011),plugmat,role='filler_plug',detail='Twelve ports; cap profile, thread and vent revision not calibrated');plugs.append(plug)
    edge_break(plug,.0008)
links=[]
def capsule_link(name,a,b,role='series_link'):
    av,bv=Vector(a),Vector(b);d=bv-av;mid=(av+bv)/2
    cu=bpy.data.curves.new(name+'_profile','CURVE');cu.dimensions='2D';cu.fill_mode='BOTH';cu.extrude=.002;cu.bevel_depth=.0004;cu.bevel_resolution=2
    spline=cu.splines.new('POLY');pts=[];radius=.010
    for center,start in [(d.length/2,-math.pi/2),(-d.length/2,math.pi/2)]:
        for j in range(17):
            ang=start+j*math.pi/16;pts.append((center+radius*math.cos(ang),radius*math.sin(ang),0,1))
    spline.points.add(len(pts)-1)
    for p,co in zip(spline.points,pts):p.co=co
    spline.use_cyclic_u=True;o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.location=mid;o.rotation_euler.z=math.atan2(d.y,d.x);cu.materials.append(lead)
    o=welded_curve(o);tag(o,role,'1977 p206;1983 fig12','Fitted welded link envelope; exact weld/copper insert geometry not modeled');return o
for cell in range(1,12):links.append(capsule_link(f'SERIES_LINK_{cell:02d}_{cell+1:02d}',posts[(cell,'positive')],posts[(cell+1,'negative')]))
for index,(cell,polarity) in enumerate([(1,'negative'),(12,'positive')]):
    cx,cy,_=posts[(cell,polarity)];loc=(-L/2-.0065,cy,.191)
    lug=cube('FRONT_'+polarity+'_terminal_lug',(.009,.031,.029),loc,lead,0,'front_terminal','Front-wall bolt-hole lug documented; dimensions and bolted attachment fitted')
    cut=cylinder('TOOL_'+polarity+'_lug_bolt_hole',.0055,.025,loc,axis='X');boolean(lug,cut);edge_break(lug,.001)
    cu=bpy.data.curves.new(polarity+'_front_lead_curve','CURVE');cu.dimensions='3D';cu.bevel_depth=.004;cu.bevel_resolution=3;cu.use_fill_caps=True
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(2)
    for p,co in zip(sp.bezier_points,[posts[(cell,polarity)],(-L/2-.0065,cy,lidZ+.009),(-L/2-.0065,cy,.2055)]):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(polarity+'_front_lead',cu);scene.collection.objects.link(ob);cu.materials.append(lead);ob=welded_curve(ob);tag(ob,'front_lead','1977 p206','Routing fitted; geometry may require weld/contact refinement')
for label in ['PROTECTIVE_TERMINAL_HOOD_UNMODELED','PRESSED_WOOD_TOP_COVER_UNMODELED','PLATE_PACKS_AND_SEPARATORS_UNMODELED']:
    ob=bpy.data.objects.new(label,None);scene.collection.objects.link(ob);ob.parent=root;ob['status']='DOCUMENTED_BUT_UNMODELED; not a geometric part'
gauge=cube('REFERENCE_ONLY_587x238x239mm',(.587,.238,.239),(0,0,.118));gauge.display_type='WIRE';gauge.hide_render=True;gauge['status']='Published complete-unit envelope reference; incomplete modeled assembly does not claim exact fit';gauge.parent=root
metadata={key:(value.to_list() if hasattr(value,'to_list') else value) for key,value in root.items()}
note=bpy.data.texts.new('READ_ME_BATTERY_STUDY');note.write(json.dumps(metadata,ensure_ascii=False,indent=2))
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.use_motion_blur=False
scene.render.resolution_x=1400;scene.render.resolution_y=950;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
world=bpy.data.worlds.new('Battery review world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.19,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.world=world
bpy.ops.object.camera_add(location=(-.83,-.67,.61));cam=bpy.context.object;focus=Vector((0,0,.11));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.84;scene.camera=cam
for loc,energy,size in [((-.4,-.3,1.1),100,.8),((.3,.6,.7),80,.7)]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(focus-light.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
topology=[]
for o in parts:
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.normal_update()
    topology.append({'name':o.name,'vertices':len(me.vertices),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume_m3':bm.calc_volume(signed=True)})
    bm.free();ev.to_mesh_clear()
graph={'cells':list(range(1,13)),'series_links':[[i,i+1] for i in range(1,12)],'front_terminals':{'negative_cell':1,'positive_cell':12},'nominal_complete_unit_voltage_v':24,'nominal_complete_unit_capacity_Ah':70,'four_vehicle_units_parallel_capacity_Ah':280,'scope':'Documented logical topology, not electrochemical or circuit simulation validation'}
(OUT/'parts-register.json').write_text(json.dumps(register,indent=2));(OUT/'build-audit.json').write_text(json.dumps({'status':'UNACCEPTED_STRUCTURE_STUDY','reference_metadata':metadata,'topology':topology,'graph':graph,'unmodeled':[o.name for o in bpy.data.objects if o.type=='EMPTY' and o.get('status','').startswith('DOCUMENTED')]},ensure_ascii=False,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'12ST70_Family_Structure_Study.blend'),compress=True)
render_records=[]
for name in ['structure-exterior','three-four-chamber-layout']:
    hidden=[]
    if name=='three-four-chamber-layout':
        for o in parts:
            if o.name in ['WOOD_long_side_-1','WOOD_end_-1'] or o['role'] in {'cell_lid','filler_plug','lead_post','series_link','front_terminal','front_lead'}:
                o.hide_render=True;hidden.append(o.name)
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    render_records.append({'file':name+'.png','hidden_for_structural_inspection':hidden,'camera_matrix_world':[list(r) for r in cam.matrix_world]})
(OUT/'render-provenance.json').write_text(json.dumps({'engine':'Actual Cycles CPU,48samples,4threads','records':render_records,'not_vehicle_installation':True,'all16VehicleGates':'OPEN'},indent=2))
print('BATTERY_STUDY_BUILT',len(parts),'parts','topology_failures',sum(t['non_manifold_edges']>0 or t['signed_volume_m3']<=0 for t in topology),flush=True)

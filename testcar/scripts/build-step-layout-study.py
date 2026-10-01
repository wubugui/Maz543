#!/usr/bin/env python3
"""Independent MAZ step layout: native primitives + editable modifiers/curves.
No vehicle is loaded. No .blend or GLB is saved. All metric dimensions are
inherited model datums or fitted study choices, never factory measurements.
Replay with official Blender 4.5.13 --background --factory-startup --threads 2
--python build-step-layout-study.py -- --repo /path/Maz543 --out /outside/repo/run
--view oblique|elevation. Every output directory must be new.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
from collections import Counter
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

START=time.time()
args=argparse.ArgumentParser()
args.add_argument('--repo',type=Path,required=True)
args.add_argument('--out',type=Path,required=True)
args.add_argument('--view',choices=['oblique','elevation'],required=True)
a=args.parse_args(sys.argv[sys.argv.index('--')+1:])
a.repo=a.repo.resolve(); a.out=a.out.resolve()
assert not a.out.is_relative_to(a.repo), 'Outputs must stay outside repository'
a.out.mkdir(parents=True,exist_ok=False)
report_path=a.out/'layout-report.json'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def write(d): report_path.write_text(json.dumps(d,indent=2)+'\n')
SCRIPT_SHA=sha(__file__)
write({'status':'IN_PROGRESS','script_sha256':SCRIPT_SHA,'view':a.view})
assert bpy.app.version[:3]==(4,5,13),bpy.app.version_string
INPUTS={
 'native_assembly':('testcar/work/cloud-native-step-assembly-20261001/native-assembly-report.json','e8b4781c1d05fc0a539e9b52ed84226c16fcc057eec9fa20627f8feb75dc4e17'),
 'seed_lookup':('testcar/work/cloud-native-step-assembly-20261001/seed-lookup/result.json','cae418844706387c1bb84bc719ee2996159b2371f728c7db5bc9a7d2d611cef7'),
 'source_model':('testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend','8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'),
 'topology_provenance':('testcar/reference/cab-step-primary-topology-20261001.json','8edcf765400b3a7c684a6eb7461427a11472aff9a42f8e572b2f878ff26addad'),
}
input_reads={}
for k,(rel,expected) in INPUTS.items():
    p=a.repo/rel; actual=sha(p)
    assert actual==expected,(k,actual,expected)
    input_reads[k]={'path':rel,'sha256':actual,'bytes':p.stat().st_size}
inv=json.loads((a.repo/INPUTS['native_assembly'][0]).read_text())
byname={o['name']:o for o in inv['objects']}
sill=byname['BL_Cab_-1_side_monocoque']['bounds_world_m'][0][2]
assert abs(sill-1.1200000047683716)<1e-12
# Parameters keep metric assumptions in one editable location.
P={
 'x_frame':[-5.15,-2.95],
 'y_center':1.52,'width':0.12,'z_frame_center':0.90,
 'frame_rect_section_width':0.014,'frame_rect_section_height':0.047,
 'frame_bevel_display_fit':0.002,
 'x_stations':[-5.12,-4.035,-2.98],
 'tread_x':[[-5.10,-4.12],[-3.95,-3.00]],
 'z_tread_center':0.928,'tread_thickness':0.009,
 'station_z_bottom':0.9235,'station_z_top':1.105,
 'interface_size':[0.080,0.16,0.014],
 'interface_center_z':1.101,
 'guide_radius_display_only':0.0015,
 'sill_min_z_inherited':sill,
}
PARAMETER_PROVENANCE={
 'x_frame':'Fitted outer extent using legacy platform bounds -5.15/-2.95 as placement leads, not hardpoints',
 'y_center':'Inherited lower-step/tread model center at +Y 1.52 m; one side only',
 'width':'Inherited nominal existing native tread extent 0.12 m; no factory width claim',
 'z_frame_center':'Inherited existing native lower-step curve centerline around 0.90 m',
 'frame_rect_section_width':'Fitted visualization/space envelope, not verified section',
 'frame_rect_section_height':'Fitted 0.047 m envelope reaches inherited tread underside at 0.9235 m',
 'frame_bevel_display_fit':'Fitted edge treatment for readability, not manufacturing radius',
 'x_stations':'Fitted end/center/end stations; middle -4.035 m is midpoint of legacy tread-region gap, not original hardpoint',
 'tread_x':'Fitted extents near two legacy placement leads; deliberately separate by 0.17 m; not factory measurements',
 'z_tread_center':'Inherited current tread center 0.928 m, not tread top or factory datum',
 'tread_thickness':'Inherited existing native tread envelope thickness about 0.009 m, simple envelope only',
 'station_z_bottom':'Fitted guide starts at frame top/tread underside, no joint construction',
 'station_z_top':'Fitted centerline end below sill with intentionally unclaimed interface gap',
 'interface_size':'Fitted wire envelope for unknown upper interface, not bracket dimensions',
 'interface_center_z':'Fitted position below sill; no actual mounting contact',
 'guide_radius_display_only':'Graphic line weight only; explicitly not support diameter',
 'sill_min_z_inherited':'Exact recorded fixed side-sill minimum Z from current native inventory; reference plane only, no sill surface imported',
}
assert set(P)==set(PARAMETER_PROVENANCE)
# Explicit factory-empty study. Never load/append/link an existing vehicle.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.name='Independent layout study - not installed'
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0
scene['scope']='ONE SIDE; fitted layout; two tread regions; three support stations; no physical attachment claim'
col_model=bpy.data.collections.new('01_Fitted_layout_envelopes'); scene.collection.children.link(col_model)
col_guides=bpy.data.collections.new('02_Support_centerlines_and_interface_envelopes'); scene.collection.children.link(col_guides)
col_tools=bpy.data.collections.new('03_Editable_native_boolean_tools'); scene.collection.children.link(col_tools)
col_anno=bpy.data.collections.new('04_Nonphysical_annotations'); scene.collection.children.link(col_anno)
col_setup=bpy.data.collections.new('05_View_and_lighting'); scene.collection.children.link(col_setup)
def put(obj,col):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    col.objects.link(obj)
    return obj

def mat(name,color,metal=0,rough=.6,emission=False):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=rough
    if emission:
        # Pure native emission for graphic annotations: no illumination-dependent washout.
        nodes=m.node_tree.nodes;nodes.clear()
        out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value=(*color,1);em.inputs['Strength'].default_value=1
        m.node_tree.links.new(em.outputs['Emission'],out.inputs['Surface'])
    return m
frame_mat=mat('Fitted lower frame - neutral blue',(.05,.19,.26),.15)
tread_mat=mat('Tread region envelopes - not a tread pattern',(.15,.46,.53),.05)
guide_mat=mat('Orange unknown station centerlines - graphic only',(.95,.30,.035),emission=True)
interface_mat=mat('Cyan unknown interface envelope - graphic only',(.0,.55,.68),emission=True)
ink=mat('Annotation ink',(.010,.018,.026),emission=True)
muted=mat('Annotation secondary',(.035,.045,.060),emission=True)
interface_ink=mat('Interface legend ink',(.0,.11,.17),emission=True)
guide_ink=mat('Centerline legend ink',(.27,.045,.003),emission=True)
sill_mat=mat('Inherited sill datum line',(.27,.33,.40),emission=True)

def cube(name,center,dims,material,col):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    o=put(bpy.context.object,col); o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:o.data.materials.append(material)
    o['dimension_status']='FITTED OR INHERITED MODEL ENVELOPE; NOT FACTORY'
    return o

def line(name,points,material,col,radius=.0015,cyclic=False):
    c=bpy.data.curves.new(name+'_editable_path','CURVE');c.dimensions='3D'
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=cyclic;c.bevel_depth=radius;c.bevel_resolution=1;c.use_fill_caps=True
    o=bpy.data.objects.new(name,c);col.objects.link(o);c.materials.append(material)
    o['not_physical']='CENTERLINE/INTERFACE GRAPHIC; NO MATERIAL OR SECTION CLAIM'
    return o

xmin,xmax=P['x_frame']; yc=P['y_center']; width=P['width']; fw=P['frame_rect_section_width']; fh=P['frame_rect_section_height']; fz=P['z_frame_center']
base=cube('FRAME__connected_lower_envelope',(sum(P['x_frame'])/2,yc-width/2+fw/2,fz),(xmax-xmin,fw,fh),frame_mat,col_model)
parts=[cube('TOOL__outer_longitudinal_rail',(sum(P['x_frame'])/2,yc+width/2-fw/2,fz),(xmax-xmin,fw,fh),None,col_tools)]
for i,x in enumerate(P['x_stations']):
    parts.append(cube(f'TOOL__transverse_station_{i+1}',(x,yc,fz),(fw,width,fh),None,col_tools))
for o in parts:
    mod=base.modifiers.new('Editable native union '+o.name,'BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=o
    o.hide_render=True;o.hide_set(True);o.display_type='WIRE'
bevel=base.modifiers.new('Fitted edge softening only','BEVEL');bevel.width=P['frame_bevel_display_fit'];bevel.segments=3
bevel.affect='EDGES'
base['interpretation']='One connected lower frame; rectangular envelope is fitted, not a verified cross-section'
treads=[]
for i,(xa,xb) in enumerate(P['tread_x']):
    t=cube(f'TREAD_REGION_{i+1}__plain_envelope',((xa+xb)/2,yc,P['z_tread_center']),(xb-xa,width,P['tread_thickness']),tread_mat,col_model)
    t['not_pattern']='No tread perforations, holes or groove count inferred'
    treads.append(t)
# Three station groups: dashed centerlines deliberately cannot read as a real rod/cable.
station_groups=[]
for i,x in enumerate(P['x_stations']):
    grp=bpy.data.objects.new(f'STATION_{i+1}__UNKNOWN_SUPPORT',None);col_guides.objects.link(grp)
    grp['role']='Shared middle station' if i==1 else 'End station'
    grp['material_flexibility_joints']='UNKNOWN'
    for j in range(5):
        z0=P['station_z_bottom']+(P['station_z_top']-P['station_z_bottom'])*j/5
        z1=z0+(P['station_z_top']-P['station_z_bottom'])*.65/5
        o=line(f'S{i+1}_centerline_dash_{j}',[(x,yc,z0),(x,yc,z1)],guide_mat,col_guides)
        o.parent=grp
    sx,sy,sz=P['interface_size'];zc=P['interface_center_z']
    for z in (zc-sz/2,zc+sz/2):
        o=line(f'S{i+1}_interface_envelope_z_{z}',[(x-sx/2,yc-sy/2,z),(x+sx/2,yc-sy/2,z),(x+sx/2,yc+sy/2,z),(x-sx/2,yc+sy/2,z)],interface_mat,col_guides,cyclic=True);o.parent=grp
    for xx in (x-sx/2,x+sx/2):
        for yy in (yc-sy/2,yc+sy/2):
            o=line(f'S{i+1}_interface_envelope_edge_{xx}_{yy}',[(xx,yy,zc-sz/2),(xx,yy,zc+sz/2)],interface_mat,col_guides);o.parent=grp
    station_groups.append(grp)
# Datum is an annotation, not a replacement or approximation of actual body geometry.
line('DATUM_ONLY__recorded_sill_minimum',[(xmin-.08,yc,sill),(xmax+.08,yc,sill)],sill_mat,col_anno,.001)

# Native Cycles renders, explicit color management and lighting.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
scene.cycles.use_denoising=True;scene.cycles.seed=0
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=0.0;scene.view_settings.gamma=1.0
scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.78,.83,.86,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);col_setup.objects.link(o);o.location=loc;aim(o,(-4.05,1.52,.94));return o
area('Large soft key',(-4.6,-.2,3.7),180,3)
area('Soft fill',(-2.8,3.6,2.6),80,2)
camdata=bpy.data.cameras.new('Study orthographic camera');cam=bpy.data.objects.new('Study orthographic camera',camdata);col_setup.objects.link(cam)
camdata.type='ORTHO';camdata.ortho_scale=2.72
cam.location=(-4.18,-1.5,2.20) if a.view=='oblique' else (-4.05,-1.5,1.00)
aim(cam,(-4.05,1.52,1.00));scene.camera=cam
# Camera-facing native annotation planes: text is not composited/raster-edited.
def text(name,body,xy,size=.037,material=ink):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size;c.space_line=1.15;c.align_x='LEFT';c.align_y='TOP_BASELINE'
    o=bpy.data.objects.new(name,c);col_anno.objects.link(o);c.materials.append(material)
    o.rotation_euler=cam.rotation_euler
    o.location=cam.matrix_world@Vector((xy[0],xy[1],-1))
    return o
bpy.context.view_layer.update()
text('Title','MAZ CAB STEP / INDEPENDENT LAYOUT',(-1.26,.71),.050)
text('Subtitle','ONE SIDE  |  TWO TREAD REGIONS  |  THREE SUPPORT STATIONS',(-1.26,.61),.027,muted)
text('View descriptor',('OBLIQUE NATIVE VIEW' if a.view=='oblique' else 'SIDE ELEVATION / Z DATUM CHECK')+'  /  ALL DIMENSIONS FITTED OR INHERITED',(-1.26,.52),.025,muted)
text('Top guide legend','CYAN: UNKNOWN UPPER INTERFACE ENVELOPES',(-1.26,.36),.027,interface_ink)
text('Station legend','ORANGE: SUPPORT CENTERLINES ONLY; MATERIAL / SECTION / JOINTS UNKNOWN',(-1.26,.30),.023,guide_ink)
text('Sill label','SILL DATUM Z = 1.120 m',(-1.26,.21),.025,muted)
text('Below view details','TREAD 1: 0.980 m     |     0.170 m GAP     |     TREAD 2: 0.950 m',(-1.26,-.25),.029)
text('Frame dimensions','CONNECTED LOWER FRAME: 2.200 m x 0.120 m    /    tread center Z = 0.928 m',(-1.26,-.32),.025,muted)
text('Station positions','FITTED X STATIONS: -5.120 / -4.035 / -2.980 m  (middle station shared)',(-1.26,-.39),.025,muted)
text('Main limit','LAYOUT STUDY ONLY. NOT INSTALLED. NOT FACTORY-DIMENSION VERIFIED.',(-1.26,-.53),.028)
text('Gate limit','No hardpoints, flexibility, fasteners or strength asserted. All 16 vehicle gates remain OPEN.',(-1.26,-.60),.024,muted)
text('Source note','Topology: inspected historical figs 92/93 + later catalog 27. No 1977 batch applicability established.',(-1.26,-.68),.023,muted)
text('One side note','Native Blender 4.5.13 / Cycles CPU2 / AgX, exposure 0, gamma 1. Original vehicle never loaded.',(-1.26,-.75),.021,muted)
bpy.context.view_layer.update()

def evaluated_summary(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
    try:
        vv=[ev.matrix_world@v.co for v in me.vertices]
        bounds=[[min(v[k] for v in vv) for k in range(3)],[max(v[k] for v in vv) for k in range(3)]]
        adj=[set() for _ in vv]
        counts=Counter()
        for p in me.polygons:
            idx=list(p.vertices)
            for j in range(len(idx)):
                edge=tuple(sorted((idx[j],idx[(j+1)%len(idx)])))
                counts[edge]+=1;adj[edge[0]].add(edge[1]);adj[edge[1]].add(edge[0])
        seen=set();components=[]
        for j in range(len(vv)):
            if j in seen:continue
            todo=[j];seen.add(j);n=0
            while todo:
                q=todo.pop();n+=1
                for u in adj[q]:
                    if u not in seen:seen.add(u);todo.append(u)
            components.append(n)
        projected=[world_to_camera_view(scene,cam,v) for v in vv]
        return {'name':o.name,'type':o.type,'evaluated_vertices':len(vv),'evaluated_faces':len(me.polygons),
          'bounds_world_m':bounds,'connected_components':len(components),'edge_incidence_not_two':sum(v!=2 for v in counts.values()),
          'in_camera_frame':all(0.03<p.x<.97 and .03<p.y<.97 and p.z>0 for p in projected),
          'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
    finally:ev.to_mesh_clear()

summary=[evaluated_summary(o) for o in [base]+treads]
guide_summary=[evaluated_summary(o) for o in col_guides.objects if o.type=='CURVE']
max_layout_z=max(s['bounds_world_m'][1][2] for s in summary+guide_summary)
frame_bounds=summary[0]['bounds_world_m'];tread_bounds=[s['bounds_world_m'] for s in summary[1:]]
margin=sill-max_layout_z;gap=tread_bounds[1][0][0]-tread_bounds[0][1][0]
def layout_predicate(tread_count,stations,separation,maxz):
    return tread_count==2 and len(stations)==3 and stations==sorted(set(stations)) and separation>0 and maxz<sill
controls={
 'one_solid_deck_rejected':not layout_predicate(1,P['x_stations'],0,max_layout_z),
 'four_stations_rejected':not layout_predicate(2,P['x_stations']+[-2.5],gap,max_layout_z),
 'above_sill_rejected':not layout_predicate(2,P['x_stations'],gap,sill+.0001),
 'overlapping_tread_regions_rejected':not layout_predicate(2,P['x_stations'],-.01,max_layout_z),
}
checks={
 'native_lower_frame_one_closed_component':summary[0]['connected_components']==1 and summary[0]['edge_incidence_not_two']==0,
 'two_separate_closed_tread_envelopes':len(treads)==2 and all(s['connected_components']==1 and s['edge_incidence_not_two']==0 for s in summary[1:]),
 'positive_inter_region_gap':gap>.16999,
 'three_unique_station_groups':len(station_groups)==3,
 'middle_station_between_tread_regions':tread_bounds[0][1][0]<P['x_stations'][1]<tread_bounds[1][0][0],
 'station_order_inside_lower_frame':xmin<min(P['x_stations'])<P['x_stations'][1]<max(P['x_stations'])<xmax,
 'all_study_geometry_below_sill_datum':margin>.009,
 'inherited_tread_center_and_width_preserved':all(abs((b[1][2]+b[0][2])/2-.928)<2e-6 and abs(b[1][1]-b[0][1]-.12)<2e-6 for b in tread_bounds),
 'fitted_frame_bounds':abs(frame_bounds[0][0]-xmin)<2e-6 and abs(frame_bounds[1][0]-xmax)<2e-6,
 'native_model_geometry_fully_in_frame':all(s['in_camera_frame'] for s in summary+guide_summary),
 'predicate_negative_controls':all(controls.values()),
}
assert all(checks.values()),checks
before_render={o.name:(tuple(o.matrix_world[i][j] for i in range(4) for j in range(4)),o.data.name) for o in list(col_model.objects)+list(col_guides.objects) if o.data}
image_path=a.out/(a.view+'.png');scene.render.filepath=str(image_path)
bpy.ops.render.render(write_still=True)
after_render={o.name:(tuple(o.matrix_world[i][j] for i in range(4) for j in range(4)),o.data.name) for o in list(col_model.objects)+list(col_guides.objects) if o.data}
checks['model_matrices_data_identity_unchanged_by_render']=before_render==after_render
checks['source_model_byte_identical']=sha(a.repo/INPUTS['source_model'][0])==INPUTS['source_model'][1]
checks['script_byte_identical_during_run']=sha(__file__)==SCRIPT_SHA
assert all(checks.values()),checks
report={
 'status':'INDEPENDENT_NATIVE_LAYOUT_CHECKS_PASS_NOT_INSTALLATION_OR_ACCEPTANCE',
 'view':a.view,'blender_version':bpy.app.version_string,'script_sha256':SCRIPT_SHA,'inputs':input_reads,
 'params_m':P,'parameter_provenance':PARAMETER_PROVENANCE,
 'model_objects':summary,'guide_object_count':len(guide_summary),'station_count':len(station_groups),
 'numeric_checks':checks,'predicate_controls':controls,
 'measurements':{'frame_bounds_m':frame_bounds,'tread_bounds_m':tread_bounds,'inter_region_gap_m':gap,
   'max_study_geometry_z_m':max_layout_z,'sill_minimum_z_m':sill,'below_sill_placement_margin_m':margin,
   'station_spacing_m':[P['x_stations'][i+1]-P['x_stations'][i] for i in range(2)]},
 'render':{'engine':scene.render.engine,'device':'CPU','threads':2,'samples':32,'resolution':[1600,1000],
   'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma,
   'path':image_path.name,'sha256':sha(image_path),'bytes':image_path.stat().st_size,
   'camera_world_matrix':[list(row) for row in cam.matrix_world],'orthographic_scale':camdata.ortho_scale},
 'seconds_script':time.time()-START,'source_model_loaded':False,'source_saved':False,'new_blend_or_glb_saved':False,
 'original_parts_moved_hidden_deleted_reparented':False,
 'existing_six_closed_contact_pairs':'UNCHANGED OPEN; not tested or repaired by this separate scene',
 'whole_vehicle_gates':'ALL 16 OPEN',
 'limits':[
   'Editable native reconstruction script only; scene lives in memory, no new native asset published',
   'Curve line weights and interface boxes are graphics, not real cable/rod/bracket geometry',
   'Frame/tread regions are fitted simple envelopes, no material/section/perforation/fabrication specification',
   'Positive below-sill margin is only chosen datum placement, not physical attachment or clearance to actual body',
   'No vehicle or door geometry loaded; no continuous-motion, whole-vehicle, browser or strength acceptance',
   '1973 attribution from host, no title page/colophon inspected; 1977 MAZ-543A applicability not established',
   'Later 2008 fasteners and part revision not copied; diagram93 cable label belongs to cab tilt',
   'One side only; no symmetry assertion',
 ],
}
write(report)
print('LAYOUT_REPORT',json.dumps({'status':report['status'],'view':a.view,'checks':checks,'measurements':report['measurements']}))

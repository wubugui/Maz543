"""Fit the source-traced panel study to the existing dashboard proxy anchors.

This is an explicitly fitted installation candidate, not factory metrology.
Superseded proxy geometry is archived, not deleted. Seats, steering and the
production files are not modified. Use native Separate, never manual mesh edits.
"""
import argparse,bpy,hashlib,json,math,numpy as np
from collections import Counter
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True)
ap.add_argument('--anchor',choices=['body-centre','rear-face'],default='rear-face')
args=ap.parse_args(__import__('sys').argv[__import__('sys').argv.index('--')+1:])
src=Path(args.input).resolve();out=Path(args.output).resolve();assert not out.exists()
study=ROOT/'outputs/cloud-cab-panel-study-20261001/study.blend'
assert hashlib.sha256(study.read_bytes()).hexdigest()=='d6a5e8ab83202ac9368acda79fdd41120a62bdce2ebbf23728852d20183beda3'
expected=next(r for r in json.loads((src.parent/'build-report.json').read_text()) if r['file']==src.name)
source_hash=hashlib.sha256(src.read_bytes()).hexdigest();assert source_hash==expected['candidate_sha256']
bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()

def signature(o):
    h=hashlib.sha256();m=o.data
    if o.type=='MESH':
        a=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',a);h.update(a.tobytes())
        a=np.empty(len(m.loops),dtype=np.int32);m.loops.foreach_get('vertex_index',a);h.update(a.tobytes())
        for prop in ('loop_start','loop_total','material_index'):
            a=np.empty(len(m.polygons),dtype=np.int32);m.polygons.foreach_get(prop,a);h.update(a.tobytes())
        for uv in m.uv_layers:
            a=np.empty(len(uv.uv)*2,dtype=np.float32);uv.uv.foreach_get('vector',a);h.update(a.tobytes())
    return {'geometry_uv':h.hexdigest(),'matrix':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render}

before={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH'}
images_before={i.name for i in bpy.data.images}
def faces(o):
    m=o.data;result=Counter()
    for p in m.polygons:
        corners=[tuple(m.vertices[m.loops[i].vertex_index].co)+tuple(x for uv in m.uv_layers for x in uv.uv[i].vector) for i in p.loop_indices]
        key=(p.material_index,min(tuple(corners[i:]+corners[:i]) for i in range(len(corners))))
        result[key]+=1
    return result
old_dashboard_faces=faces(bpy.data.objects['cab_0064'])
def seat_bases(o):
    result=[];m=o.data
    for x in (-4.45,-3.38):
        for y in (-1.025,1.025):
            ids={v.index for v in m.vertices if all(abs((o.matrix_world@v.co)[k]-c)<=r+3e-6 for k,c,r in [(0,x,.23),(1,y,.23),(2,1.6,.125)])}
            polys=[p for p in m.polygons if set(p.vertices)<=ids]
            assert len(ids)==900 and len(polys)==300,(x,y,len(ids),len(polys))
            data=[]
            for p in polys:
                corners=[tuple(o.matrix_world@m.vertices[m.loops[i].vertex_index].co)+tuple(v for uv in m.uv_layers for v in uv.uv[i].vector) for i in p.loop_indices]
                data.append((m.materials[p.material_index].name,min(tuple(corners[i:]+corners[:i]) for i in range(len(corners)))))
            digest=hashlib.sha256(json.dumps(sorted(data),separators=(',',':')).encode()).hexdigest()
            result.append({'legacy_seat_centre':[x,y,1.6],'vertices':len(ids),'faces':len(polys),'world_geometry_uv_material_sha256':digest})
    return result
seats_before=seat_bases(bpy.data.objects['cab_0064'])
archive=bpy.data.collections.new('BL Panel Fit — superseded original proxies / retained')
bpy.context.scene.collection.children.link(archive)
archived=[]
def retain_hidden(o,reason):
    o.hide_render=True;o.hide_set(True);archive.objects.link(o)
    o['review_replacement_reason']=reason;o['retained_original_geometry']=True
    archived.append(o.name)

for name,count in [('cab_0066',2072),('cab_0067',6174),('cab_0068',2072)]:
    o=bpy.data.objects[name];assert len(o.data.vertices)==count,(name,len(o.data.vertices))
    assert all(-4.80<(o.matrix_world@v.co).x<-4.73 and 1.87<(o.matrix_world@v.co).z<2.11 for v in o.data.vertices),name
    retain_hidden(o,'Fourteen old generic seven-per-cab instrument proxies replaced by distinct source-traced panels')

# The original green merged mesh also contains seats. Separate ONLY the two
# dashboard blocks, bounded well in front of every seat-base vertex.
o=bpy.data.objects['cab_0064'];selected=[v.index for v in o.data.vertices if (o.matrix_world@v.co).x < -4.78]
assert len(selected)==1800,len(selected)
assert not o.modifiers and len(o.data.vertices)==5400
selected_set=set(selected)
assert all(not(set(p.vertices)&selected_set) or set(p.vertices)<=selected_set for p in o.data.polygons)
old_objects=set(bpy.data.objects)
bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
for v in o.data.vertices:v.select=v.index in selected_set
for e in o.data.edges:e.select=all(i in selected_set for i in e.vertices)
for p in o.data.polygons:p.select=all(i in selected_set for i in p.vertices)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
created=set(bpy.data.objects)-old_objects;assert len(created)==1
old_panel=created.pop();old_panel.name='BL_PanelFit_original_dashboard_blocks_retained'
assert len(old_panel.data.vertices)==1800 and len(old_panel.data.polygons)==600
assert len(o.data.vertices)==3600 and len(o.data.polygons)==1200
assert all((old_panel.matrix_world@v.co).x < -4.78 for v in old_panel.data.vertices)
assert all((o.matrix_world@v.co).x >= -4.78 for v in o.data.vertices)
assert not o.hide_render and o.matrix_world==old_panel.matrix_world
retain_hidden(old_panel,'Two fitted solid dashboard blocks replaced by separate thin sheet and instrument-body studies')
assert faces(o)+faces(old_panel)==old_dashboard_faces,'Original face-corner geometry and UVs must remain accounted for'
seats_after=seat_bases(o);assert seats_after==seats_before

collections=['01 LEFT CAB — Fig101 layout study','02 RIGHT CAB — Fig102 auxiliary panel','90 EDITABLE SOURCE CURVES — hidden','91 LEFT THROUGH-HOLE CUTTERS — hidden','92 RIGHT THROUGH-HOLE CUTTERS — hidden','93 AUXILIARY BOOLEAN CUTTERS — hidden']
with bpy.data.libraries.load(str(study),link=False) as (available,loaded):
    assert all(n in available.collections for n in collections)
    loaded.collections=collections
for c in loaded.collections:
    if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
cab=bpy.data.objects['cab']
# Local panel +X is driver-right, +Y up, +Z towards the driver.
axes=Matrix(((0,0,1),(1,0,0),(0,1,0)))
rotation=Matrix.Rotation(.15,3,'Y')@axes
placements=[]
for name,side_y in [('LEFT DISPLAY ROOT — not vehicle datum',-1.025),('RIGHT DISPLAY ROOT — not vehicle datum',1.025)]:
    root=bpy.data.objects[name];root.parent=cab
    pose=rotation.to_4x4();pose.translation=Vector((-4.93,side_y,1.98))
    if args.anchor=='rear-face':
        # Existing block has 0.25 m fore/aft depth. Its +X face points towards
        # the driver; a replacement sheet belongs on that face, not its centre.
        pose.translation += Matrix.Rotation(.15,3,'Y') @ Vector((.125,0,0))
    root.matrix_world=pose
    root['installation_status']='FITTED REVIEW ONLY; inherited dashboard proxy anchor, no factory hardpoint proof'
    placements.append({'root':name,'world_matrix':[list(r) for r in pose],'anchor_source':'Existing lib/maz543.ts 0.25 m deep dashboard block and tilt; not a factory dimension','anchor':args.anchor})
    for child in root.children_recursive:
        child['source_study_installed_in_vehicle']=bool(child.get('installed_in_vehicle',False))
        child['installed_in_vehicle']=True
        child['review_vehicle_fit']=True
        child['installation_acceptance']='OPEN — independent fitted review vehicle only'
bpy.context.view_layer.update()
changed=[]
for name,old in before.items():
    if name in {'cab_0064','cab_0066','cab_0067','cab_0068'}:continue
    if signature(bpy.data.objects[name])!=old:changed.append(name)
assert not changed,changed
assert {i.name for i in bpy.data.images}==images_before,'Study may not add image pixels'
for name in ('cab_0066','cab_0067','cab_0068'):
    after=signature(bpy.data.objects[name]);old=before[name]
    assert all(after[k]==old[k] for k in ('geometry_uv','matrix','parent'))
out.parent.mkdir(parents=True,exist_ok=True)
report={'source_sha256':source_hash,'study_sha256':hashlib.sha256(study.read_bytes()).hexdigest(),'status':'FITTED_INSTALLATION_CANDIDATE_NOT_ACCEPTED','file':out.name,'archived_originals':archived,'old_dashboard_vertices_separated':len(old_panel.data.vertices),'remaining_visible_seat_base_vertices':len(bpy.data.objects['cab_0064'].data.vertices),'seat_bases_before':seats_before,'seat_bases_after':seats_after,'unrelated_original_meshes_unchanged':len(before)-4,'placements':placements,'source_geometry_or_dimensions_newly_calibrated':False,'factory_mounts_and_installation':'OPEN','native_rest_clearance':'PENDING_FRESH_READBACK','existing_steering_column_seat_interference':'NOT_FIXED','all16VehicleGates':'OPEN'}
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
report['candidate_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();assert hashlib.sha256(src.read_bytes()).hexdigest()==source_hash
out.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n')
print('PANEL_FIT_SAVED',out,flush=True)

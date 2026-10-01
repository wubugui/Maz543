"""Fresh-process, per-vertex check of saved editable reference scenes."""
import bpy,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-suspension-installation-20261001'
SOURCE=ROOT/'outputs/MAZ543A_Suspension_Master.blend'
build=json.loads((OUT/'editable-scenes-build.json').read_text())
mapping=json.loads((OUT/'reference-mapping.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==build['source_sha256']
candidate=OUT/build['file'];assert sha(candidate)==build['sha256']
def world_vertices(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    pts=np.array([list(ev.matrix_world@v.co) for v in m.vertices],dtype=np.float64)
    m.calc_loop_triangles();triangles=np.array([tuple(t.vertices) for t in m.loop_triangles])
    ev.to_mesh_clear();return pts,triangles
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
reference={}
for index,row in enumerate(build['scenes']):
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    if index:
        for name,pose in mapping['measurements'][index-1]['pose'].items():
            o=bpy.data.objects[name];p=pose['p'];o.location=(p[0],-p[2],p[1]);o.rotation_euler.x=pose['rx']
    bpy.context.view_layer.update()
    reference[row['scene']]={name:world_vertices(bpy.data.objects[name]) for name in row['copied_source_parts']}
bpy.ops.wm.open_mainfile(filepath=str(candidate))
rows=[]
for row in build['scenes']:
    scene=bpy.data.scenes[row['scene']];bpy.context.window.scene=scene
    assert scene.unit_settings.system=='METRIC' and scene.unit_settings.scale_length==1. and scene.unit_settings.length_unit=='MILLIMETERS'
    parts={o['source_object_name']:o for o in scene.objects if 'source_object_name' in o}
    frames=[]
    for frame in [0,17]:
        scene.frame_set(frame);bpy.context.view_layer.update();comparisons=[]
        for name,(old,old_triangles) in reference[row['scene']].items():
            now,triangles=world_vertices(parts[name]);assert now.shape==old.shape
            maximum=float(np.max(np.linalg.norm(now-old,axis=1)))
            assert np.array_equal(triangles,old_triangles),(scene.name,name,'triangle topology')
            assert maximum<2e-6,(scene.name,name,maximum)
            comparisons.append({'source_object':name,'vertices':len(now),'max_world_vertex_difference_m':maximum,'triangles_identical':True})
        dg=bpy.context.evaluated_depsgraph_get()
        actual=parts['S543_0_lower'].evaluated_get(dg).matrix_world.translation.z-parts['S543_0_upright'].evaluated_get(dg).matrix_world.translation.z
        assert abs(actual-row['target_drop_m'])<2e-6,(scene.name,frame,actual,row['target_drop_m'])
        frames.append({'frame':frame,'actual_lower_head_drop_m':actual,'parts':comparisons})
    rows.append({'scene':scene.name,'target_drop_m':row['target_drop_m'],'frames':frames})
scene=bpy.data.scenes[build['scenes'][2]['scene']];bpy.context.window.scene=scene;scene.frame_set(17);bpy.context.view_layer.update()
scene.render.resolution_x=900;scene.render.resolution_y=825;scene.render.resolution_percentage=100
scene.cycles.samples=32;scene.render.filepath=str(OUT/'editable-reference-readback.png');bpy.ops.render.render(write_still=True)
parts={o['source_object_name']:o for o in scene.objects if 'source_object_name' in o}
dg=bpy.context.evaluated_depsgraph_get()
actual=parts['S543_0_lower'].evaluated_get(dg).matrix_world.translation.z-parts['S543_0_upright'].evaluated_get(dg).matrix_world.translation.z
assert abs(actual-.1385)<2e-6
assert sha(SOURCE)==build['source_sha256'];assert sha(candidate)==build['sha256']
report={'status':'SAVED_EDITABLE_REFERENCE_SCENES_VERIFIED; NOT_REPAIRED_ASSEMBLY','candidate_sha256':sha(candidate),'source_sha256':sha(SOURCE),
        'scenes':rows,'post_render_midpoint_drop_m':actual,'render_file':'editable-reference-readback.png','render_sha256':sha(OUT/'editable-reference-readback.png'),
        'original_archive_present':build['original_archive_scene'] in bpy.data.scenes,'source_and_candidate_files_unchanged_during_readback':True,
        'scope':'Four isolated copied scenes retain the actual source geometry at diagnostic poses, independent of old illustration animation. Stop contact, support adjustment, preload and whole-vehicle acceptance remain OPEN.'}
(OUT/'editable-scenes-readback.json').write_text(json.dumps(report,indent=2))
print('EDITABLE_REFERENCE_READBACK',len(rows),'scenes',sum(len(f['parts']) for r in rows for f in r['frames']),'object states',actual)

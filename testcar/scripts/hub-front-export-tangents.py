"""Preserve editable source; native triangulation of changed baked cab modifiers for correct tangent export."""
import bpy,os,json
from pathlib import Path
OUT=Path(os.environ['HUB_OUTPUT_DIR']);report={'scope':'Export-only native triangulation of the two changed baked cab surfaces','files':[]}
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);changed=[]
    if filename.endswith('Textured.blend'):
        for p in ['001','005']:
            o=bpy.data.objects[f'BL_Merged_cab_pivot_{p}_OD_green_aged_enamel'];m=o.modifiers.new('Export triangles for actual Boolean surface tangents','TRIANGULATE');m.quad_method='FIXED';m.ngon_method='BEAUTY';changed.append(o.name)
    report['files'].append({'file':filename,'nativeTriangulateModifiersAdded':changed,'limits':'No tangent removal or normal-map disable; editable master Boolean retained'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if filename.endswith('Textured.blend'):
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(o):
            while o:
                if o.name in excluded:return False
                o=o.parent
            return True
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        def descendants(o):
            for c in o.children:yield c;yield from descendants(c)
        bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        for o in descendants(root):
            if allowed(o):o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(OUT/'front-export-tangents-verification.json').write_text(json.dumps(report,indent=2))

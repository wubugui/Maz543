import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cooling_asset import attach_cooling
from d12_asset import engine_descendants
from starting_asset import is_starting_mesh
for name in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    path=ROOT/'outputs'/name;bpy.ops.wm.open_mainfile(filepath=str(path));attach_cooling();bpy.context.scene.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    if name.endswith('Textured.blend'):
        bpy.ops.object.select_all(action='DESELECT');vehicle=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        for o in [vehicle]+engine_descendants(vehicle):o.select_set(True)
        for n in ['D12A_525A','S543_SUSPENSION','S543_COOLING']:
            ob=bpy.data.objects.get(n)
            if ob:
                for o in [ob]+engine_descendants(ob):o.select_set(False)
        for o in engine_descendants(vehicle):
            if is_starting_mesh(o):o.select_set(False)
        bpy.context.view_layer.objects.active=vehicle
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-blender.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
print('COOLING_INSTALLED_ENGINE_MOUNT_CORRECTED',flush=True)

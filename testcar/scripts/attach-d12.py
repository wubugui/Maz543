import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import attach_engine,engine_descendants
from starting_asset import attach_starting,is_starting_mesh
for name in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    file=ROOT/'outputs'/name;bpy.ops.wm.open_mainfile(filepath=str(file));root=attach_engine()
    if (ROOT/'outputs/MAZ543A_Starting_Master.blend').exists():attach_starting()
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
    if name=='MAZ543A_Textured.blend':
        bpy.ops.object.select_all(action='DESELECT')
        vehicle=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        for obj in [vehicle]+engine_descendants(vehicle):obj.select_set(True)
        for obj in [root]+engine_descendants(root):obj.select_set(False)
        suspension=bpy.data.objects.get('S543_SUSPENSION')
        if suspension:
            for obj in [suspension]+engine_descendants(suspension):obj.select_set(False)
        cooling=bpy.data.objects.get('S543_COOLING')
        if cooling:
            for obj in [cooling]+engine_descendants(cooling):obj.select_set(False)
        for obj in engine_descendants(vehicle):
            if is_starting_mesh(obj):obj.select_set(False)
        bpy.context.view_layer.objects.active=vehicle
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
print('Native vehicle masters now contain the editable D12 module; body GLB excludes its separate download.')

"""Re-export the already batched triangle asset with complete tangent vectors.
The canonical native exporter also triangulates n-gons before future exports.
"""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'public/models/maz543a-suspension.glb'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(path))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'work/suspension-with-tangents.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_tangents=True,export_extras=True,export_animations=False,export_morph=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(ROOT/'work/suspension-with-tangents.glb').replace(path)
print('Complete tangent vectors exported from triangle geometry.',flush=True)

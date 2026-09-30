"""Finish an already baked body with portable tangent space, without rebaking."""
import bpy,bmesh,json,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Textured.blend'))
tree=ast.parse((ROOT/'scripts/blender-export.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['descendants','separate_module']],type_ignores=[]),'body_selection','exec'))
root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
objects=[o for o in descendants(root) if not separate_module(o)];processed=set();report=[]
for o in objects:
    if o.type!='MESH' or o.data.name in processed:continue
    processed.add(o.data.name);bm=bmesh.new();bm.from_mesh(o.data)
    faces=[f for f in bm.faces if len(f.verts)>4];count=len(faces)
    if count:bmesh.ops.triangulate(bm,faces=faces,quad_method='BEAUTY',ngon_method='BEAUTY');bm.to_mesh(o.data);o.data.update()
    bm.free()
    uses_normal=any(m and m.use_nodes and any(n.type=='BSDF_PRINCIPLED' and n.inputs['Normal'].is_linked for n in m.node_tree.nodes) for m in o.data.materials)
    if uses_normal:
        assert o.data.uv_layers.active,(o.name,'missing UV')
        o.data.calc_tangents(uvmap=o.data.uv_layers.active.name)
    report.append({'mesh':o.data.name,'triangulatedNgons':count,'normalMapped':uses_normal})
for filename in ['CAB_PHOTO_FIT_NOTES.md','COOLING_REFERENCE_NOTES.md']:
    text=bpy.data.texts.get(filename) or bpy.data.texts.new(filename);text.clear();text.write((ROOT/'docs'/filename).read_text(encoding='utf-8'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Textured.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in objects:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(ROOT/'outputs/body-tangent-verification.json').write_text(json.dumps(report,indent=2))
print('BODY_TANGENTS_EXPORTED',len(report),'meshes',sum(r['triangulatedNgons'] for r in report),'ngons',flush=True)

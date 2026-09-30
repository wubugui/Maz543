"""Explicit authored rubber PBR for new gasket/blade objects; preserve original atlas materials."""
import bpy,os,json
from pathlib import Path
OUT=Path(os.environ['HUB_OUTPUT_DIR']);report={'scope':'Repair white export fallback of only four new rubber objects','files':[]}
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0)
    mat=bpy.data.materials.new('MAZ543A_Front_window_rubber');mat.use_nodes=True;bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.008,.011,.009,1);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.78;mat.diffuse_color=(.008,.011,.009,1)
    changed=[]
    for side in [-1,1]:
        for suffix in ['windshield_gasket','wiper_blade']:
            o=bpy.data.objects[f'BL_Front_{suffix}_{side}'];o.data.materials.clear();o.data.materials.append(mat);changed.append(o.name)
    report['files'].append({'file':filename,'changedMaterialOnly':changed,'rgbaLinear':[.008,.011,.009,1],'metallic':0,'roughness':.78,'limits':'Photo tone fitted; factory composition/color calibration OPEN'})
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
(OUT/'front-rubber-material-verification.json').write_text(json.dumps(report,indent=2))

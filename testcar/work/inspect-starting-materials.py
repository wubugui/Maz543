import bpy
bpy.ops.wm.open_mainfile(filepath='D:/testcar/outputs/MAZ543A_Starting_Master.blend')
for name in ['MN1_field_coil_woven_insulation','MN1_pole_lamination_stack','Starting_contact_copper']:
 m=bpy.data.materials[name];b=m.node_tree.nodes.get('Principled BSDF');print(name,tuple(b.inputs['Base Color'].default_value),b.inputs['Metallic'].default_value,b.inputs['Roughness'].default_value)
print('Exposure',bpy.context.scene.view_settings.exposure)
print('Override',bpy.context.view_layer.material_override)

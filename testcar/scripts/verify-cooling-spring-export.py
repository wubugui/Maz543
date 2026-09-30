"""Compare decoded GLB morph geometry with the saved Blender source.

GLB weights come from the actual transpiled browser solver, not a Python
reimplementation. Mesh point order and split normals may differ after export.
"""
import bpy,json,sys
from pathlib import Path
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cooling_spring_geometry import apply_travel
spec=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']
samples=json.loads((ROOT/'work/spring-morph-samples.json').read_text())

def points(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    # Subtract the common object-origin translation before floating-point
    # subtraction. Retain all rotation and scale, in Blender's world axes.
    matrix=ev.matrix_world.to_3x3();result=[matrix@v.co for v in mesh.vertices]
    ev.to_mesh_clear();return result

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'))
bpy.context.scene.frame_set(0)
reference={}
for side in range(2):
    coil=bpy.data.objects[f'COOL_release_spring_{side}'];coil.data.shape_keys.animation_data_clear()
    for sample in samples:
        apply_travel(coil,spec,sample['travel']);bpy.context.view_layer.update()
        reference[side,sample['travel']]=points(coil)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/models/maz543a-cooling.glb'))
rows=[]
for side in range(2):
    coil=bpy.data.objects[f'COOL_release_spring_{side}'];assert coil.get('parametricSpring')
    assert coil.data.shape_keys is not None
    keys=coil.data.shape_keys.key_blocks
    for sample in samples:
        for key,value in zip(('Pitch','Radius'),sample['weights']):keys[key].value=value
        bpy.context.view_layer.update();actual=points(coil);expected=reference[side,sample['travel']]
        tree=KDTree(len(expected))
        for i,p in enumerate(expected):tree.insert(p,i)
        tree.balance();error=max(tree.find(p)[2] for p in actual)
        reverse=KDTree(len(actual))
        for i,p in enumerate(actual):reverse.insert(p,i)
        reverse.balance();error=max(error,max(reverse.find(p)[2] for p in expected))
        assert error<2e-6,(side,sample,error)
        rows.append(dict(side=side,travelMM=sample['travel']*1000,webWeights=sample['weights'],nativeVertices=len(expected),decodedVertices=len(actual),maxSurfaceDistanceMM=error*1000))
report={'samples':rows,'limits':'Decoded exported mesh point set comparison at five travel positions per side, using web-solver weights. Does not prove elastic stress, original spring dimensions, all continuous poses or complete clutch acceptance.'}
(ROOT/'outputs/cooling-spring-export-verification.json').write_text(json.dumps(report,indent=2))
print('COOLING_SPRING_EXPORT',json.dumps(report),flush=True)

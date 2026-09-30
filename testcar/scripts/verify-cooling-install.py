"""Validate installed native transforms against shared generated pose data."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cooling_spring_geometry import weights
spec=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']
engine=json.loads((ROOT/'work/starting-engine-poses.json').read_text())
starting=json.loads((ROOT/'work/starting-poses.json').read_text())['frames']
cooling=json.loads((ROOT/'work/cooling-poses.json').read_text())['frames']
reports=[]
for file in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/file));max_position=0;max_angle=0;max_scale=0;max_morph=0
    for j in range(0,601,30):
        bpy.context.scene.frame_set(j)
        for data in [engine,starting,cooling]:
            for n,p in data[j]['pose'].items():
                o=bpy.data.objects[n];target=Vector((p['p'][0],-p['p'][2],p['p'][1]))
                max_position=max(max_position,(o.location-target).length)
                max_angle=max(max_angle,abs(o.rotation_euler.x-p['rx']),abs(o.rotation_euler.z-p.get('ry',0)))
                max_scale=max(max_scale,abs(o.scale.x-p.get('sx',1)),abs(o.scale.z-p.get('sy',1)))
        for side in range(2):
            keys=bpy.data.objects[f'COOL_release_spring_{side}'].data.shape_keys.key_blocks
            target=weights(spec,cooling[j]['pose'][f'COOL_spring_{side}']['springTravel'])
            max_morph=max(max_morph,*(abs(keys[name].value-value) for name,value in zip(('Pitch','Radius'),target)))
    assert max_morph<2e-6,(file,max_morph)
    mount=bpy.data.objects['engine'].location;assert (mount-Vector((-4.05,0,1.32))).length<1e-6
    assert max_position<2e-6 and max_angle<.0002 and max_scale<2e-6,(file,max_position,max_angle,max_scale)
    reports.append({'file':file,'engineMount':list(mount),'frames':21,'jointsPerFrame':sum(len(x[0]['pose']) for x in [engine,starting,cooling]),'maxPositionError':max_position,'maxAngleError':max_angle,'maxScaleError':max_scale,'maxSpringMorphWeightError':max_morph})
(ROOT/'outputs/cooling-installed-verification.json').write_text(json.dumps(reports,indent=2));print('COOLING_INSTALLED_PARITY',reports,flush=True)

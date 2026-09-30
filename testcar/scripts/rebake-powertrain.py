"""Update existing native poses after a solver change, without rebuilding meshes."""
import bpy,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cooling_spring_geometry import bake_springs
cooling_spec=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']
starting=json.loads((ROOT/'work/starting-poses.json').read_text())['frames']
cooling=json.loads((ROOT/'work/cooling-poses.json').read_text())['frames']
engine=json.loads((ROOT/'work/starting-engine-poses.json').read_text())
cardan=json.loads((ROOT/'work/cardan-poses.json').read_text())['frames']

def bake(frames):
    for name,p0 in frames[0]['pose'].items():
        o=bpy.data.objects[name];o.animation_data_clear()
        action=bpy.data.actions.new('Shared causal sequence '+name)
        slot=action.slots.new(id_type='OBJECT',name=name);o.animation_data_create().action=action;o.animation_data.action_slot=slot
        o.location=(p0['p'][0],-p0['p'][2],p0['p'][1]);o.scale=(p0.get('sx',1),1,p0.get('sy',1))
        tracks=[('location',i,[f['pose'][name]['p'][j]*sign for f in frames]) for i,j,sign in [(0,0,1),(1,2,-1),(2,1,1)]]
        if 'q' in p0:
            qs=[]
            for f in frames:
                q=f['pose'][name]['q'];q=[q[3],q[0],-q[2],q[1]]
                if qs and sum(a*b for a,b in zip(q,qs[-1]))<0:q=[-a for a in q]
                qs.append(q)
            o.rotation_mode='QUATERNION';o.rotation_quaternion=qs[0]
            tracks += [('rotation_quaternion',i,[q[i] for q in qs]) for i in range(4)]
        else:
            o.rotation_mode='XYZ';o.rotation_euler=(p0['rx'],0,p0.get('ry',0))
            tracks += [('rotation_euler',0,[f['pose'][name]['rx'] for f in frames]),('rotation_euler',2,[f['pose'][name].get('ry',0) for f in frames])]
        tracks += [('scale',i,[f['pose'][name].get(key,1) for f in frames]) for i,key in [(0,'sx'),(2,'sy')]]
        for channel,index,values in tracks:
            if max(values)-min(values)<1e-12:continue
            fc=action.fcurves.new(data_path=channel,index=index);fc.keyframe_points.add(len(frames))
            fc.keyframe_points.foreach_set('co',[v for f,x in zip(frames,values) for v in (f['frame'],x)])
            for k in fc.keyframe_points:k.interpolation='LINEAR'
            fc.update()

files=[('MAZ543A_Starting_Master.blend',[starting]),('MAZ543A_Cooling_Master.blend',[cooling]),
       ('MAZ543A_Cardan_Master.blend',[cardan]),('MAZ543A_Master.blend',[starting,engine,cooling]),
       ('MAZ543A_Textured.blend',[starting,engine,cooling])]
for filename,sequences in files:
    path=ROOT/'outputs'/filename;bpy.ops.wm.open_mainfile(filepath=str(path))
    if '--refresh-cooling' in sys.argv and filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
        sys.path.insert(0,str(ROOT/'scripts'))
        from cooling_asset import attach_cooling
        attach_cooling()
    for seq in sequences:bake(seq)
    if cooling in sequences:bake_springs(cooling,cooling_spec)
    scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=600;scene.render.fps=60;scene.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    print('POWERTRAIN_POSES_UPDATED',filename,flush=True)

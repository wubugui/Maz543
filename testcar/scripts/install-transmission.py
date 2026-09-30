"""Replace the obsolete planetary seed in the two native vehicle masters.
The module's separate 6 rad/s inspection sequence is not imposed on the vehicle:
installed native masters retain a documented neutral reference pose until their
complete road-drive sequence is rebaked from a coupled vehicle solver.
"""
import bpy,json,shutil,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/MAZ543A_Transmission.blend'
BACKUP=ROOT.parent/'restoration/planetary-core-20260908/native-originals'
BACKUP.mkdir(parents=True,exist_ok=True)
D=json.loads((ROOT/'work/transmission/poses.json').read_text());reports=[]
legacy=['drive_0002','drive_pivot_002','drive_pivot_007','drive_pivot_012']
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    path=ROOT/'outputs'/filename
    if not (BACKUP/filename).exists():shutil.copy2(path,BACKUP/filename)
    bpy.ops.wm.open_mainfile(filepath=str(path));drive=bpy.data.objects.get('drive');assert drive
    old=bpy.data.objects.get('S543_TRANSMISSION')
    if old:
        for ob in list(old.children_recursive)+[old]:bpy.data.objects.remove(ob,do_unlink=True)
    removed=[]
    for name in legacy:
        ob=bpy.data.objects.get(name)
        if ob:
            assert ob.parent==drive,(name,'unexpected parent')
            removed.extend(x.name for x in ob.children_recursive);removed.append(ob.name)
            for child in list(ob.children_recursive)+[ob]:bpy.data.objects.remove(child,do_unlink=True)
    with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
        dst.objects=list(src.objects);dst.images=list(src.images)
    for ob in dst.objects:
        if ob.name not in bpy.context.scene.objects:bpy.context.collection.objects.link(ob)
        ob.animation_data_clear()
        if ob.type=='MESH' and ob.data.shape_keys:
            ob.data.shape_keys.animation_data_clear()
            for key in ob.data.shape_keys.key_blocks:key.value=0
    root=bpy.data.objects['S543_TRANSMISSION'];root.parent=drive
    p=D['spec']['position'];root.location=(p[0],-p[2],p[1])
    for name,pose in D['samples'][0]['pose'].items():
        ob=bpy.data.objects[name]
        if ob.rotation_mode=='QUATERNION':ob.rotation_quaternion=(math.cos(pose['rx']/2),math.sin(pose['rx']/2),0,0)
        else:ob.rotation_euler.x=pose['rx']
        if 'p' in pose:ob.location=(pose['p'][0],-pose['p'][2],pose['p'][1])
    root['nativeVehiclePose']='Neutral reference only; interactive gearing lives in the browser and source module inspection sequence.'
    bpy.context.scene.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    reports.append({'file':filename,'removedNodes':removed,'newNodes':len(root.children_recursive)+1,'position':list(root.location),'nativePose':'neutral reference; full vehicle road-drive sequence still open'})
(ROOT/'outputs/transmission-installation.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))

"""Attach the latest independent starting module without rebaking engine keys."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from suspension_asset import descendants

def attach_starting():
 for n in ['C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','S543_STARTING','STARTING_ENGINE_MOUNT']:
  old=bpy.data.objects.get(n)
  if old:
   for ob in reversed([old]+descendants(old)):bpy.data.objects.remove(ob,do_unlink=True)
 old=bpy.data.collections.get('S543_STARTING')
 if old:bpy.data.collections.remove(old)
 with bpy.data.libraries.load(str(ROOT/'outputs/MAZ543A_Starting_Master.blend'),link=False) as (src,dst):dst.collections=['S543_STARTING']
 col=dst.collections[0];bpy.context.scene.collection.children.link(col);root=next(o for o in col.objects if o.name=='S543_STARTING')
 root.parent=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];root.location=(0,0,0)
 anchor=bpy.data.objects.new('STARTING_ENGINE_MOUNT',None);col.objects.link(anchor);anchor.parent=bpy.data.objects['engine']
 for n in ['C5_STARTER','C5_FLYWHEEL_RING']:bpy.data.objects[n].parent=anchor
 p=json.loads((ROOT/'work/starting-poses.json').read_text())['spec']['pumpPosition'];bpy.data.objects['MZN_PREOIL'].location=(p[0],-p[2],p[1])
 return root

def is_starting_mesh(obj):
 while obj:
  if obj.name in ['S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT']:return True
  obj=obj.parent
 return False

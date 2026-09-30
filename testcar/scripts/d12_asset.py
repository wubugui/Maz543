"""Append the editable engine to a vehicle blend while exporting it separately."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def engine_descendants(root):
    result=[]
    for child in root.children:result.append(child);result+=engine_descendants(child)
    return result
def attach_engine():
    path=ROOT/'outputs/D12A525A_Engine_Master.blend'
    if not path.exists():return None
    holder=bpy.data.objects.get('engine')
    if not holder:raise RuntimeError('Vehicle has no engine mounting transform')
    for child in reversed(engine_descendants(holder)):bpy.data.objects.remove(child,do_unlink=True)
    old=bpy.data.collections.get('D12_ENGINE')
    if old:bpy.data.collections.remove(old)
    with bpy.data.libraries.load(str(path),link=False) as (source,target):
        target.collections=['D12_ENGINE']
    collection=target.collections[0];bpy.context.scene.collection.children.link(collection)
    root=next(o for o in collection.objects if o.name=='D12A_525A')
    root.parent=holder;root.location=(0,0,0);root.rotation_euler=(0,0,0)
    return root
def is_engine_mesh(obj):
    cursor=obj
    while cursor:
        if cursor.name=='D12A_525A':return True
        cursor=cursor.parent
    return False

"""Install independently downloaded cooling geometry and correct engine mounting."""
import bpy,bmesh,json
from pathlib import Path
from d12_asset import engine_descendants
ROOT=Path(__file__).resolve().parents[1]
def attach_cooling():
    holder=bpy.data.objects['cooling'];bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    if not holder.get('coolingMigrated'):
        for ob in list(engine_descendants(holder)):
            if ob.type=='MESH':
                bm=bmesh.new();bm.from_mesh(ob.data)
                remove=[f for f in bm.faces if not (max((ob.matrix_world@v.co).x for v in f.verts)<-2.5 or min((ob.matrix_world@v.co).x for v in f.verts)>-.58)]
                bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
                if bm.faces:
                    bm.to_mesh(ob.data);ob['coolingLegacyAux']=True
                else:bpy.data.objects.remove(ob,do_unlink=True)
                bm.free()
        for ob in reversed(engine_descendants(holder)):
            if ob.type=='EMPTY' and not ob.children:bpy.data.objects.remove(ob,do_unlink=True)
        holder['coolingMigrated']=True
    old=bpy.data.objects.get('S543_COOLING')
    if old:
        for ob in reversed([old]+engine_descendants(old)):bpy.data.objects.remove(ob,do_unlink=True)
    col=bpy.data.collections.get('S543_COOLING')
    if col:bpy.data.collections.remove(col)
    with bpy.data.libraries.load(str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'),link=False) as (src,dst):dst.collections=['S543_COOLING']
    col=dst.collections[0];bpy.context.scene.collection.children.link(col);root=next(o for o in col.objects if o.name=='S543_COOLING');root.parent=holder;root.location=(0,0,0)
    engine=bpy.data.objects['engine'];p=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']['enginePosition']
    engine.location=(p[0],-p[2],p[1]);engine['base']=p;engine['mountStatus']='Between-cab location corrected from original MAZ layout; exact coordinates fitted'
    return root

"""Check actual evaluated boolean geometry, not script labels or a manifest."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Master.blend'))
depsgraph=bpy.context.evaluated_depsgraph_get()
def C(x,y,z):return Vector((x,-z,y))
results=[]
for side in [-1,1]:
    skin=bpy.data.objects[f'BL_Cab_{side}_side_monocoque'].evaluated_get(depsgraph)
    inverse=skin.matrix_world.inverted()
    for door,x in [('front',-4.49),('rear',-3.56)]:
        for height in [1.65,2.2]:
            origin=inverse@C(x,height,side*1.8)
            direction=inverse.to_3x3()@C(0,0,-side)
            hit=skin.ray_cast(origin,direction.normalized(),distance=.65)[0]
            assert not hit,f'Solid side skin blocks {side} {door} doorway at {height}m'
            results.append({'side':side,'door':door,'height_m':height,'opening':'clear'})
    origin=inverse@C(-5.15,1.55,side*1.8)
    direction=inverse.to_3x3()@C(0,0,-side)
    assert skin.ray_cast(origin,direction.normalized(),distance=.65)[0],f'Entire cab skin missing on side {side}'
(ROOT/'outputs/cab-aperture-verification.json').write_text(json.dumps(results,indent=2))
print('Verified four real doorways at eight sample rays, and both remaining side skins.')

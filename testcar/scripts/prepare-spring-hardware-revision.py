"""Rebuild only shared large-clutch hardware inside temporary native geometry."""
import bpy,bmesh,math,json,ast,sys
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
target=ROOT/'work/transmission/rotary-geometry.blend';bpy.ops.wm.open_mainfile(filepath=str(target))
DATA=json.loads((ROOT/'work/transmission/poses.json').read_text(encoding='utf-8'));REG=[];root=bpy.data.objects['S543_TRANSMISSION']
STEEL=bpy.data.materials['TX_ground_steel'];FORGED=bpy.data.materials['TX_forged_steel']
def tag(ob,part,source='',role='internal',**kw):
    ob['transmissionPart']=part;ob['transmissionRole']=role;ob['sourceId']='MAZ 1973 figs.42/44';REG.append(ob.name);return ob
for filename,names in [('blender-d12.py',{'C','empty','mesh','prism','box','lathe','cylinder','ring','pipe'}),('transmission-rotary-feed.py',{'remove_tx','bore_tx','drill_cutter','axial_hole'})]:
    tree=ast.parse((ROOT/'scripts'/filename).read_text(encoding='utf-8'))
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),filename,'exec'))
exec(compile((ROOT/'scripts/transmission-spring-hardware.py').read_text(encoding='utf-8'),'transmission-spring-hardware.py','exec'))
bpy.ops.wm.save_as_mainfile(filepath=str(target));print('Rebuilt large-clutch hardware templates in temporary geometry',flush=True)

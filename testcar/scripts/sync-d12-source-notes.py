"""Keep reference and reconstruction boundaries inside all editable masters."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['D12A525A_Engine_Master.blend','MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 path=ROOT/'outputs'/name;bpy.ops.wm.open_mainfile(filepath=str(path))
 for textname,source in [('D12_REFERENCE_AND_SCOPE','docs/D12_REFERENCE_REGISTER.md'),('D12_TIMING_SOURCES','docs/D12_TIMING_SOURCE_NOTES.md'),('D12_WATER_PUMP_SOURCES','docs/D12_WATER_PUMP_NOTES.md')]:
  text=bpy.data.texts.get(textname) or bpy.data.texts.new(textname);text.clear();text.write((ROOT/source).read_text(encoding='utf-8'))
 text=bpy.data.texts.get('D12_TIMING_LAYOUT') or bpy.data.texts.new('D12_TIMING_LAYOUT');text.clear();text.write(json.dumps(json.loads((ROOT/'work/d12-poses.json').read_text())['timing'],indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
print('D12_SOURCE_NOTES_SYNCED',flush=True)

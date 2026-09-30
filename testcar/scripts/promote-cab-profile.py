"""Promote the verified photo-fit study; retain its unmeasured-dimension notes."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
check=json.loads((ROOT/'outputs/cab-profile-verification.json').read_text())
assert len(check['facades'])==2 and all(r['nonManifoldEdges']==0 for r in check['facades'])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_CabFit_Study.blend'))
note=bpy.data.texts.get('CAB_PHOTO_FIT_NOTES.md') or bpy.data.texts.new('CAB_PHOTO_FIT_NOTES.md')
note.clear();note.write((ROOT/'docs/CAB_PHOTO_FIT_NOTES.md').read_text(encoding='utf-8'))
image=bpy.data.images.load(str(ROOT/'work/reference-docs/MAZ543A-museum-front.jpg'),check_existing=True)
image.pack();image.use_fake_user=True
bpy.context.scene['cabFrontProfile']='Photo-fitted lower relief; exact dimensions and hidden wall profile unverified.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Master.blend'),compress=True)
print('CAB_PROFILE_PROMOTED_NATIVE',flush=True)

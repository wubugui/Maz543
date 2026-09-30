from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
target=ROOT.parent/'restoration/display-neutral-cache-20260909'
assert not target.exists(),target
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
notice='**最新：[静止整车缓存与悬挂零位]({link}) 已修正中性残力和透明双面材质版本造成的持续重绘。普通入口完整 8868 实例静止缓存有效，开门和悬挂激励可恢复绘制，240 Hz 求解保留。精确矩阵合批仍有 332 像素差，未默认启用；动态整车仍慢。完整 goal ACTIVE、16 项 OPEN，继续保精度优化及机械实现。**\n\n此前阶段：\n\n'
for name in guides:
 p=ROOT/name;text=p.read_text(encoding='utf8');head,rest=text.split('\n',1)
 link=('' if name.startswith('docs/') else 'docs/')+'DISPLAY_NEUTRAL_CACHE_20260909.md'
 p.write_text(head+'\n\n'+notice.format(link=link)+rest.lstrip('\n'),encoding='utf8')
files=guides+['docs/DISPLAY_NEUTRAL_CACHE_20260909.md','lib/displayFrameCache.ts','lib/shadowPoseProbe.ts','lib/exactBatchMatrices.ts','lib/displayBatches.ts','lib/vehicleViewport.ts','lib/suspension.ts','lib/compositedShadows.ts',
 'scripts/verify-exact-batch-matrices.mjs','scripts/verify-suspension-reference.mjs','scripts/verify-rendered-material-versions.mjs','scripts/verify-display-presentation.mjs','scripts/verify-mechanical-timeline.mjs','scripts/archive-display-neutral-stage.py',
 'outputs/render-performance-evidence/presentation-tests.json']
for folder in ['outputs/shadow-cache','outputs/exact-batch','outputs/suspension-reference','work/shadow-cache','work/exact-batch','work/suspension-reference']:
 files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/folder).glob('*')) if p.is_file())
assert len(set(files))==len(files)
for name in files:assert (ROOT/name).is_file(),name
target.mkdir(parents=True);rows=[]
for name in files:
 src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);sha=digest(src);assert digest(dst)==sha
 rows.append({'path':name,'bytes':src.stat().st_size,'sha256':sha})
report={'wholeGoal':'ACTIVE; all 16 gates OPEN','status':'Ordinary full-model exact idle cache restored; mechanical neutral reference corrected and tested; moving mechanisms retained. Exact-batch full pixels failed and not enabled. Dynamic whole rendering still slow; physical calibration remains open.','files':rows,'fileCount':len(rows),'totalBytes':sum(row['bytes'] for row in rows)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(target),'files':len(rows),'bytes':report['totalBytes']},indent=2))

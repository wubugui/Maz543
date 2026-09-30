from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];target=ROOT.parent/'restoration/worker-lifecycle-20260909'
assert not target.exists(),target
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
notice='**最新：[独立显示清理与故障恢复]({link}) 已修复初始化/运行异常的自有线程、画布、监听和请求清理，并通过浏览器内故障注入、同页完整重装和恢复后开门验证。全部 8868 实例、静止缓存、240 Hz 计算恢复，机械/导出/姿态源码未变。完整 Worker 仍为开发参数，动态整车仍慢。完整 goal ACTIVE、16 项 OPEN，继续保精度显示和机械实现。**\n\n此前阶段：\n\n'
for name in guides:
 p=ROOT/name;text=p.read_text(encoding='utf8');head,rest=text.split('\n',1);link=('' if name.startswith('docs/') else 'docs/')+'WORKER_LIFECYCLE_20260909.md'
 p.write_text(head+'\n\n'+notice.format(link=link)+rest.lstrip('\n'),encoding='utf8')
files=guides+['docs/WORKER_LIFECYCLE_20260909.md','lib/renderWorkerClient.ts','lib/viewportProtocol.ts','lib/viewport.worker.ts','lib/vehicleViewport.ts','components/vehicle-viewer.tsx','components/workshop.tsx',
 'scripts/verify-render-client-lifecycle.mjs','scripts/verify-viewport-worker-failures.mjs','scripts/verify-worker-lifecycle-integrity.py','scripts/summarize-worker-lifecycle-browser.py','scripts/archive-worker-lifecycle-stage.py']
for folder in ['outputs/worker-lifecycle','work/worker-lifecycle']:
 files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/folder).glob('*')) if p.is_file())
assert len(set(files))==len(files)
for name in files:assert (ROOT/name).is_file(),name
target.mkdir(parents=True);rows=[]
for name in files:
 src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);sha=digest(src);assert digest(dst)==sha
 rows.append({'path':name,'bytes':src.stat().st_size,'sha256':sha})
report={'wholeGoal':'ACTIVE; all 16 gates OPEN','status':'Owned resource rollback/fatal cleanup, synchronous startup fallback, explicit same-page full-model restart. Actual browser controlled-fault recovery passed. No mechanical/geometry/export fidelity reduction; dynamic rendering and default-worker/full-product acceptance remain open.','files':rows,'fileCount':len(rows),'totalBytes':sum(row['bytes'] for row in rows)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'directory':str(target),'files':len(rows),'bytes':report['totalBytes']},indent=2))

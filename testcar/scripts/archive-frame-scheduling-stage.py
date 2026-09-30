from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];target=ROOT.parent/'restoration/frame-scheduling-profile-20260909'
assert not target.exists(),target
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
notice='**最新：[完整逐帧计时与原生 Worker 动画帧]({link}) 已记录完整整车/运转传动的真实阶段耗时，并验证可选原生帧调度。传动样本帧间隔有所改善，整车仍慢；未降低几何、阴影、贴图或 240 Hz 求解。原生调度仍为开发参数，完整 Worker 默认发布门槛未通过。完整 goal ACTIVE，16 项 OPEN，继续实际绘制优化。**\n\n此前阶段：\n\n'
for name in guides:
 p=ROOT/name;text=p.read_text(encoding='utf8');head,rest=text.split('\n',1);link=('' if name.startswith('docs/') else 'docs/')+'FRAME_SCHEDULING_PROFILE_20260909.md'
 p.write_text(head+'\n\n'+notice.format(link=link)+rest.lstrip('\n'),encoding='utf8')
files=guides+['docs/FRAME_SCHEDULING_PROFILE_20260909.md','lib/framePhaseProfile.ts','lib/vehicleViewport.ts','lib/viewportEnvironment.ts','lib/workerViewportHost.ts','lib/viewport.worker.ts','lib/mechanics.worker.ts','lib/renderWorkerClient.ts','lib/viewportProtocol.ts',
 'scripts/verify-native-worker-frames.mjs','scripts/verify-worker-viewport-host.mjs','scripts/verify-direct-mechanics-channel.mjs','scripts/verify-frame-profile-integrity.py','scripts/summarize-frame-profile.py','scripts/archive-frame-scheduling-stage.py',
 'outputs/render-worker-evidence/host-tests.json','outputs/render-worker-evidence/direct-mechanics-tests.json']
for folder in ['outputs/frame-profile','work/frame-profile']:
 files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/folder).glob('*')) if p.is_file())
assert len(set(files))==len(files)
for name in files:assert (ROOT/name).is_file(),name
target.mkdir(parents=True);rows=[]
for name in files:
 src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);sha=digest(src);assert digest(dst)==sha
 rows.append({'path':name,'bytes':src.stat().st_size,'sha256':sha})
report={'wholeGoal':'ACTIVE; all 16 gates OPEN','status':'Finite real browser profile; optional native worker RAF; whole model remains slow; no reduction in source geometry or mechanical solver. Production browser and full worker default gates remain open.','files':rows,'fileCount':len(rows),'totalBytes':sum(row['bytes'] for row in rows)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'directory':str(target),'files':len(rows),'bytes':report['totalBytes']},indent=2))

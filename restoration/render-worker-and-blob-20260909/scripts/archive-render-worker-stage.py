from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];target=ROOT.parent/'restoration/render-worker-and-blob-20260909'
notice='**最新：[完整显示工作线程与无损封装]({link}) 已在开发入口装配完整模型并直连 240 Hz 机械计算，界面不再依赖绘制线程返回仪表；350 MB 整车 Blob 导出的全部二进制载荷与原封装一致。整车仍约 0.3–0.7 FPS，完整校验发现 698 个切线错误尚待追踪，独立显示未默认启用。完整 goal ACTIVE，16 项 OPEN，继续保精度优化。**\n\n此前阶段：\n\n'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
assert not target.exists(),target
for name in guides:
 path=ROOT/name;text=path.read_text(encoding='utf8');link=('' if name.startswith('docs/') else 'docs/')+'RENDER_WORKER_20260909.md'
 assert notice.format(link=link).split('\n')[0] not in text
 head,rest=text.split('\n',1);path.write_text(head+'\n\n'+notice.format(link=link)+rest.lstrip('\n'),encoding='utf8')
files=guides+['docs/RENDER_WORKER_20260909.md','components/vehicle-viewer.tsx','components/workshop.tsx',
 'lib/vehicleViewport.ts','lib/viewportEnvironment.ts','lib/viewportProtocol.ts','lib/workerViewportHost.ts','lib/viewport.worker.ts','lib/renderWorkerClient.ts',
 'lib/mechanics.worker.ts','lib/mechanicalTimeline.ts','lib/mechanics.ts','lib/starting.ts','lib/suspension.ts','lib/transmission.ts','lib/transmissionDynamics.ts','lib/transmissionHydraulics.ts','lib/cooling.ts',
 'lib/export-model.ts','lib/binaryGltfBlob.ts','lib/exportTransportProbe.ts','types/worker.d.ts',
 'scripts/verify-viewport-release.mjs','scripts/verify-worker-viewport-host.mjs','scripts/verify-direct-mechanics-channel.mjs','scripts/render-consumer-blocked.mjs','scripts/mechanics-worker-node.mjs','scripts/verify-mechanical-timeline.mjs','scripts/verify-render-worker-integrity.py','scripts/verify-binary-gltf-blob.mjs','scripts/validate-worker-export.mjs','scripts/compare-worker-exports.py','scripts/archive-render-worker-stage.py']
for folder in ['work/render-worker-refactor','outputs/render-worker-evidence']:
 files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/folder).glob('*')) if p.is_file())
files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'dist/client').rglob('*worker-*.js')))
assert len(set(files))==len(files)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
for name in files:assert (ROOT/name).is_file(),name
target.mkdir(parents=True);rows=[]
for name in files:
 src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);sha=digest(src);assert digest(dst)==sha
 rows.append({'path':name,'bytes':src.stat().st_size,'sha256':sha})
report={'stage':'Complete render worker and direct mechanical channel; lossless GLB Blob finalization','wholeGoal':'ACTIVE; all 16 gates OPEN','status':'Experimental render worker; full vehicle GPU remains slow; full export validation fails with 698 non-unit tangents. Blob payload matches original; not full acceptance.','files':rows,'fileCount':len(rows),'totalBytes':sum(row['bytes'] for row in rows)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'directory':str(target),'files':len(rows),'bytes':report['totalBytes']},indent=2))

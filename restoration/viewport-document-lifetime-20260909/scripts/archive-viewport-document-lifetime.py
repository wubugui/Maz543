from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
target=root.parent/'restoration/viewport-document-lifetime-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[文档退出资源清理]({prefix}VIEWPORT_DOCUMENT_LIFETIME_20260909.md) 已实际确认非 BFCache 的硬导航未执行 React cleanup，并在普通预览接入一次性 pagehide(false) 释放。主线程真实退出完成既有全部清理后，完整 8868 实例、静止缓存、240 Hz/零积压恢复；persisted=true 保留原状态。实验 Worker 硬导航已触发客户端清理，但没有取得完整释放回执。类型、构建和针对性生命周期测试通过，持续内存与动态帧率仍未解决。完整 goal ACTIVE、16 项 OPEN，继续保精度优化及完整机械目标。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['components/vehicle-viewer.tsx','lib/viewportDocumentLifetime.ts','lib/viewportLifecycleAudit.ts',
 'lib/renderWorkerClient.ts','lib/vehicleViewport.ts','scripts/verify-viewport-document-lifetime.mjs',
 'scripts/summarize-viewport-lifecycle.py','scripts/archive-viewport-document-lifetime.py',
 'docs/VIEWPORT_DOCUMENT_LIFETIME_20260909.md','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/viewport-lifecycle-audit','work/viewport-lifecycle-audit']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(row['bytes'] for row in rows),'files':rows,
 'verification':'Every copy byte-equal and SHA-256 recorded','limits':'Observed non-persisted main document now executes viewport cleanup. Does not prove sustained memory, worker hard-navigation disposal, real BFCache restoration, dynamic FPS or full mechanical product completion.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

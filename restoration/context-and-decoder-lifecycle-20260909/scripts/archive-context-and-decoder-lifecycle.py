from pathlib import Path
import hashlib,json,shutil

root=Path(__file__).resolve().parents[1]
target=root.parent/'restoration/context-and-decoder-lifecycle-20260909'
assert not target.exists(), 'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
    path=root/name
    link='' if name.startswith('docs/') else 'docs/'
    update=f'**最新：[解码器退出竞态]({link}OWNED_DRACO_LIFETIME_20260909.md) 已复现并修复延迟初始化/待解码/提交间隙的资源退出问题，实际普通预览恢复完整 8868 实例、静止缓存和 240 Hz 计算，类型与构建通过。此前巨大进程占用尚未全部归因。主线程/Worker 侧视及开门像素对照未通过，Worker、合批、分区阴影继续不默认启用；独立 Chrome 也为 Basic Render Driver，动态整车仍慢。完整 goal ACTIVE、16 项 OPEN，继续保精度显示优化及全部机械目标。**'
    content=path.read_text(encoding='utf8')
    if update not in content:
        lines=content.splitlines(keepends=True)
        path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')

files=guides+[
 'lib/contextFrameAudit.ts','lib/nativeModelError.ts','lib/ownedDracoLifetime.ts','lib/vehicleViewport.ts',
 'scripts/verify-context-audit-noise.mjs','scripts/compare-context-frame-audits.py',
 'scripts/verify-context-frame-integrity.py','scripts/verify-context-assets.py',
 'scripts/verify-owned-draco-lifetime.mjs','scripts/archive-context-and-decoder-lifecycle.py',
 'docs/CONTEXT_FRAME_AUDIT_20260909.md','docs/OWNED_DRACO_LIFETIME_20260909.md','docs/BROWSER_BACKEND_COMPARISON_20260909.md']
for folder in ['outputs/browser-backend-comparison','outputs/context-frame-audit','outputs/owned-draco-lifetime',
               'work/browser-backend-comparison','work/context-frame-audit','work/owned-draco-lifetime']:
    files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
    source=root/name; destination=target/name
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
    payload=source.read_bytes()
    assert destination.read_bytes()==payload,name
    rows.append({'file':name,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','files':rows,'count':len(rows),
 'bytes':sum(row['bytes'] for row in rows),'copyVerification':'Every file byte-equal and SHA-256 recorded',
 'limits':'Decoder lifecycle regression passed and complete ordinary app loaded. Cross-context pixel comparison failed. Whole-vehicle dynamic performance and full mechanical product goal remain unfinished.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':str(target),'files':report['count'],'bytes':report['bytes'],'verified':True}))

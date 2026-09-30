from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
target=root.parent/'restoration/context-draw-order-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[跨上下文固定源排序实验]({prefix}CONTEXT_DRAW_ORDER_20260909.md) 已记录完整绘制顺序，确认分配顺序随加载变化。受控固定源排序在侧视及右前门 99° 两组完整主线程/Worker 对照中，像素和绘制序列均相同；但与原排序仍有像素差，暂不默认启用。多次切换后进程私有占用约 5.6 GB，资源保留和动态性能仍待解决；全部模型/机械/质量保留，类型及构建通过。完整 goal ACTIVE、16 项 OPEN，继续显示优化和完整机械目标。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/contextFrameAudit.ts','lib/contextSourceOrder.ts','lib/vehicleViewport.ts',
 'scripts/compare-context-draw-order.py','scripts/verify-context-source-order.mjs','scripts/archive-context-draw-order.py',
 'docs/CONTEXT_DRAW_ORDER_20260909.md','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/context-draw-order','work/context-draw-order']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(row['bytes'] for row in rows),'files':rows,
 'verification':'Every copy byte-equal; SHA-256 recorded','limits':'Audit-only source ordering reproduced two complete poses across contexts. Baseline pixel preservation, persistent memory, dynamic performance and full product mechanics remain unproven.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1];target=root.parent/'restoration/render-target-timing-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[渲染目标命令与状态往返计时]({prefix}RENDER_TARGET_TIMING_20260909.md) 已在完整静止/侧视开门发动机运转帧核对，保留全部 9305/9306 调用与 21582915 三角形，像素差异均 0。当前 GPU 计时扩展不可用，Chromium finish 是 Flush，因此只报告完整对账的命令/状态往返墙钟时间，不冒充 GPU 时间。主颜色/透射/法线区间为后续重点；下一步在原通道上下文验证同一链接程序的精确深度快照。此前法线复用默认关闭、帧率问题未解决。类型/构建/生命周期及机械基线通过；完整 goal ACTIVE、16 项 OPEN。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/renderTargetTiming.ts','lib/vehicleViewport.ts','lib/compositedShadows.ts','lib/normalOcclusionCache.ts','scripts/verify-render-target-timing.mjs','scripts/summarize-render-target-timing.py','scripts/archive-render-target-timing.py','docs/RENDER_TARGET_TIMING_20260909.md','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/render-target-timing','work/render-target-timing']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(r['bytes'] for r in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'Finite intrusive diagnostic only. GPU completion not proven and timer extension unavailable. No draw reduction or FPS improvement in this stage; full product precision/mechanical/performance acceptance unfinished.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

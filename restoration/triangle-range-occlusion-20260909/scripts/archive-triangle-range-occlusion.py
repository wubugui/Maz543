from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1];target=root.parent/'restoration/triangle-range-occlusion-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
summary=json.loads((root/'outputs/triangle-range-occlusion/summary.json').read_text(encoding='utf8'));assert summary['passed']
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[原三角形范围遮挡]({prefix}TRIANGLE_RANGE_OCCLUSION_20260909.md) 已保留原顶点/索引/材质/程序及三角形顺序，10 个大网格仅增加 86400 字节 CPU 包围数据。静止/发动机/侧视开门额外省去约 30–148 万三角形，像素差 0，纵剖完整回退；固定重启索引/未对齐组/未知属性均回退。动态范围与整件对照见 summary，仍约一秒级，DEV 默认关闭，不能把节省数字当成流畅验收。类型、构建、范围/查询/提交/资源测试及机械基线通过。完整 goal ACTIVE、16 项 OPEN。下一步优先完整 Render Worker 的生产入口、标签/尺寸/拾取/剖切/跨上下文验收，改善普通界面的响应，再继续剩余显示代价。**'
 content=path.read_text(encoding='utf8');lines=content.splitlines(keepends=True)
 if update not in content:path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/triangleRangeProxies.ts','lib/originalProgramOcclusionCache.ts','lib/originalReplayDepthQueries.ts','lib/originalPassDepthReplay.ts','lib/vehicleViewport.ts','lib/conservativeRasterBounds.ts','lib/staticOccluderScene.ts','lib/normalOcclusionCache.ts','scripts/verify-triangle-range-proxies.mjs','scripts/verify-original-program-occlusion-cache.mjs','scripts/verify-original-replay-depth-queries.mjs','scripts/summarize-triangle-range-occlusion.py','scripts/archive-triangle-range-occlusion.py','docs/TRIANGLE_RANGE_OCCLUSION_20260909.md','outputs/original-program-occlusion-cache/tests.json','outputs/original-pass-depth-replay/query-tests.json','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/triangle-range-occlusion','work/triangle-range-occlusion']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(r['bytes'] for r in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'DEV original triangle-range submission reuse. Finite pixel and timing evidence; usable preview, default enable and full mechanical/product acceptance remain open.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

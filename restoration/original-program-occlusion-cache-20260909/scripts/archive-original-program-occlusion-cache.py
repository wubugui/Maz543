from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1];target=root.parent/'restoration/original-program-occlusion-cache-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
summary=json.loads((root/'outputs/original-program-occlusion-cache/summary.json').read_text(encoding='utf8'));assert summary['passed']
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[原程序提交位置的实际遮挡复用]({prefix}ORIGINAL_PROGRAM_OCCLUSION_CACHE_20260909.md) 已真实省去静止/发动机/侧视开门帧约 669–828 万三角形，三组像素差 0，纵剖保留原绘制。原程序选择、矩阵/uniform 更新、阴影和机械精度保留；只有控制通过且当前体仍被覆盖才省去 GL 提交。12 帧动态对照与计数见 summary，约一秒级帧间隔仍未解决可用性，DEV 默认关闭。类型、构建、资源/失效测试及机械基线通过；完整 goal ACTIVE、16 项 OPEN。继续默认主线程/更多功能验收及剩余显示代价优化。**'
 content=path.read_text(encoding='utf8');lines=content.splitlines(keepends=True)
 if update not in content:path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/originalProgramOcclusionCache.ts','lib/originalPassDepthReplay.ts','lib/originalReplayDepthQueries.ts','lib/normalOcclusionCache.ts','lib/vehicleViewport.ts','lib/staticOccluderScene.ts','lib/conservativeRasterBounds.ts','scripts/verify-original-program-occlusion-cache.mjs','scripts/verify-original-pass-depth-replay.mjs','scripts/verify-original-replay-depth-queries.mjs','scripts/summarize-original-program-occlusion-cache.py','scripts/archive-original-program-occlusion-cache.py','docs/ORIGINAL_PROGRAM_OCCLUSION_CACHE_20260909.md','outputs/context-frame-audit/source-integrity.json','outputs/original-pass-depth-replay/tests.json','outputs/original-pass-depth-replay/query-tests.json']
for folder in ['outputs/original-program-occlusion-cache','work/original-program-occlusion-cache']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(r['bytes'] for r in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'DEV actual original-program GL submission reuse. Finite pixels and dynamic evidence, not full feature, default enable or usable performance acceptance.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

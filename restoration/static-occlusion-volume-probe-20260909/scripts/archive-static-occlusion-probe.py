from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1];target=root.parent/'restoration/static-occlusion-volume-probe-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[静态车体深度与保守查询体]({prefix}STATIC_OCCLUSION_VOLUME_PROBE_20260909.md) 已在完整整车测得每通道约 330 万个潜在可省略三角形；排除 381 个运动遮挡体后潜力仍保留。关联角点修正了独立 z/w 范围过松的问题，静止/发动机/侧视开门控制查询通过，产品帧像素未改写。当前仅有限诊断，没有实际剔除或提速；下一步实现静态深度缓存、运动范围包含检查及各通道精度/像素验收。类型、构建、资源/范围测试及机械基线通过。完整 goal ACTIVE、16 项 OPEN。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/conservativeRasterBounds.ts','lib/staticOccluderScene.ts','lib/staticOcclusionProbe.ts','lib/vehicleViewport.ts','scripts/verify-conservative-raster-bounds.mjs','scripts/verify-static-occluder-scene.mjs','scripts/verify-static-occlusion-probe.mjs','scripts/summarize-static-occlusion-probe.py','scripts/archive-static-occlusion-probe.py','docs/STATIC_OCCLUSION_VOLUME_PROBE_20260909.md','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/static-occlusion-probe','work/static-occlusion-probe']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(row['bytes'] for row in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'Finite snapshot potential only; no product draw skipped and no sustained FPS improvement established. Complete product precision/performance/mechanical acceptance remains unfinished.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

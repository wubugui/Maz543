from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1];target=root.parent/'restoration/normal-occlusion-cache-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[静态深度证明的实际法线复用]({prefix}NORMAL_OCCLUSION_CACHE_20260909.md) 已接入 DEV 真实绘制，静止/发动机/侧视开门/纵剖同姿态比较均零像素差异，每帧可实际省去约 221–302 万个三角形。动态 12 帧与原始对照平均帧间隔均约 1.30 秒，尚无稳定提速，因此默认关闭。原颜色/透射/阴影和机械精度保留；下一步定位剩余通道代价并建立各自的精度证明。最终类型、构建、生命周期/范围测试及机械基线通过。完整 goal ACTIVE、16 项 OPEN。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/normalOcclusionCache.ts','lib/staticOccluderScene.ts','lib/conservativeRasterBounds.ts','lib/vehicleViewport.ts','lib/compositedShadows.ts','lib/framePhaseProfile.ts','scripts/verify-normal-occlusion-cache.mjs','scripts/verify-static-occluder-scene.mjs','scripts/verify-static-occlusion-probe.mjs','scripts/verify-conservative-raster-bounds.mjs','scripts/summarize-normal-occlusion-cache.py','scripts/archive-normal-occlusion-cache.py','docs/NORMAL_OCCLUSION_CACHE_20260909.md','outputs/context-frame-audit/source-integrity.json','outputs/static-occlusion-probe/scene-tests.json','outputs/static-occlusion-probe/lifecycle-tests.json']
for folder in ['outputs/normal-occlusion-cache','work/normal-occlusion-cache']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(r['bytes'] for r in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'Actual DEV normal-pass reuse only, default OFF. Tested frames equal but no stable FPS gain established. Complete mechanical/product/visual/performance acceptance remains unfinished.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

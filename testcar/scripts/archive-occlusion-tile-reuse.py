from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
target=root.parent/'restoration/occlusion-tile-reuse-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[保守空间遮挡依赖实验]({prefix}OCCLUSION_TILE_REUSE_20260909.md) 已覆盖原始 Float32 变换和弹簧 morph 范围，静态/发动机/侧视开门/一挡/纵剖均取得 0 像素差；预算溢出保留全部原绘制。动态仅省 0–152 draws，12 帧平均工作约 1126 ms，仍约 0.6–0.8 FPS，默认关闭。下一步调查静态车体提供遮挡证明，避免内部运动件使证明失效。类型、构建及机械/导出/显示配置基线通过。完整 goal ACTIVE、16 项 OPEN。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/conservativeRasterBounds.ts','lib/occlusionPrefixReuse.ts','lib/vehicleViewport.ts','lib/framePhaseProfile.ts','scripts/verify-conservative-raster-bounds.mjs','scripts/verify-occlusion-prefix-reuse.mjs','scripts/summarize-occlusion-tile-reuse.py','scripts/archive-occlusion-tile-reuse.py','docs/OCCLUSION_TILE_REUSE_20260909.md','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/occlusion-tile-reuse','work/occlusion-tile-reuse']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(row['bytes'] for row in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'DEV-only conservative spatial dependency experiment, dynamic savings inadequate. Complete product precision/performance/mechanical acceptance remains unfinished.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

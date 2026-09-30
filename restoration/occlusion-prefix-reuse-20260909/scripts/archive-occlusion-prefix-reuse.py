from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
target=root.parent/'restoration/occlusion-prefix-reuse-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[有序深度遮挡复用实验]({prefix}OCCLUSION_PREFIX_REUSE_20260909.md) 静态整帧 9305→3986 draws，发动机/开门/剖切均 0 像素差；但动态仅复用 0–1 次，仍约 0.8 FPS，保持默认关闭。最早变化的飞轮齿圈使几乎全部后续全前序证明失效；已避免每帧重复无效查询，下一步探索保守空间依赖。类型、构建及机械/导出/显示配置基线通过。完整 goal ACTIVE、16 项 OPEN。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/occlusionPrefixReuse.ts','lib/vehicleViewport.ts','scripts/verify-occlusion-prefix-reuse.mjs','scripts/archive-occlusion-prefix-reuse.py','docs/OCCLUSION_PREFIX_REUSE_20260909.md','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/occlusion-prefix-reuse','work/occlusion-prefix-reuse']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(row['bytes'] for row in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'DEV-only exact global depth-prefix reuse. Dynamic performance ineffective; full mechanical and browser product acceptance remain unfinished.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

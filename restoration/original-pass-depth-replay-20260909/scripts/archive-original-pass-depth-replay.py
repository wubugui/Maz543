from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1];target=root.parent/'restoration/original-pass-depth-replay-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[原链接程序深度重放与查询]({prefix}ORIGINAL_PASS_DEPTH_REPLAY_20260909.md) 已在静止、发动机及侧视开门帧完成原程序/矩阵/形变/控制/最终像素核对，三个通道各约 299–322 万三角形有潜在零采样证据；纵剖回退保留原绘制、像素差 0。错误的未上传查询几何样本已由控制拒绝并修复。此阶段没有实际剔除或提速，下一步接入跨帧证据失效及原几何提交。类型、构建、机械基线通过；完整 goal ACTIVE、16 项 OPEN。**'
 content=path.read_text(encoding='utf8');lines=content.splitlines(keepends=True)
 if update not in content:path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/originalPassDepthReplay.ts','lib/originalReplayDepthQueries.ts','lib/vehicleViewport.ts','lib/staticOccluderScene.ts','lib/conservativeRasterBounds.ts','scripts/verify-original-pass-depth-replay.mjs','scripts/verify-original-replay-depth-queries.mjs','scripts/summarize-original-depth-replay.py','scripts/archive-original-pass-depth-replay.py','docs/ORIGINAL_PASS_DEPTH_REPLAY_20260909.md','outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/original-pass-depth-replay','work/original-pass-depth-replay']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(r['bytes'] for r in rows),'files':rows,'verification':'Every copy byte-equal and SHA-256 recorded','limits':'Finite original-program snapshot and volume query proof only. No actual culling, cross-frame acceptance or stable FPS gain.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

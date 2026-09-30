from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
target=root.parent/'restoration/native-resource-retention-20260909'
assert not target.exists(),'Do not overwrite an immutable checkpoint'
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/ACCEPTANCE.md','docs/CONTINUATION_20260908.md']
for name in guides:
 path=root/name;prefix='' if name.startswith('docs/') else 'docs/'
 update=f'**最新：[原生资源引用核查]({prefix}NATIVE_RESOURCE_RETENTION_20260909.md) 已确认完整装配仅多持有 30 份替换几何、约 1.42 MB，现已释放，不能解释数 GB 占用。当前整车 2691 独立几何、418.7 MB 底层缓冲、67 材质、10 贴图保留，完整侧视像素与绘制序列和前档相同；隐藏内构/共享缓冲/导出验证、类型及构建通过。普通预览 8868 实例、静止缓存、240 Hz/零积压正常，动态帧率仍慢。完整 goal ACTIVE、16 项 OPEN，继续主要显示负载和完整机械目标。**'
 content=path.read_text(encoding='utf8')
 if update not in content:
  lines=content.splitlines(keepends=True);path.write_text(lines[0]+'\n'+update+'\n\n此前阶段：\n\n'+''.join(lines[1:]).lstrip('\n'),encoding='utf8')
files=guides+['lib/renderResources.ts','lib/vehicleViewport.ts','scripts/verify-native-resource-retention.mjs',
 'scripts/verify-native-resource-stage.py','scripts/archive-native-resource-retention.py','docs/NATIVE_RESOURCE_RETENTION_20260909.md',
 'outputs/context-frame-audit/source-integrity.json']
for folder in ['outputs/native-resource-retention','work/native-resource-retention']:
 files += [str(p.relative_to(root)).replace('\\','/') for p in (root/folder).rglob('*') if p.is_file()]
rows=[]
for name in sorted(set(files)):
 source=root/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 data=source.read_bytes();assert destination.read_bytes()==data,name
 rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','count':len(rows),'bytes':sum(row['bytes'] for row in rows),'files':rows,
 'verification':'Every copy byte-equal and SHA-256 recorded','limits':'Removed 1.42 MB of unreferenced geometry holdings; one full side frame remains pixel identical. Main multi-GB memory attribution, dynamic FPS and complete mechanical product goal remain unfinished.'}
(target/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'path':str(target),'count':report['count'],'bytes':report['bytes'],'verified':True}))

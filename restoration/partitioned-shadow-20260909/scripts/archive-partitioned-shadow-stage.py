from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
destination=root.parent/'restoration/partitioned-shadow-20260909'
assert destination.resolve().is_relative_to(root.parent.resolve())
if destination.exists():raise SystemExit('Refusing to overwrite archive')
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
for relative in guides:
    path=root/relative;content=path.read_text(encoding='utf-8');doc=('docs/' if '/' not in relative else '')+'PARTITIONED_SHADOW_EXPERIMENT_20260909.md'
    notice=('**最新：[静态/运动阴影分区实验]('+doc+') 已在完整发动机运行工况取得 0 像素差，'
      '1941 静态部件复用，381 运动部件更新；整帧 9305→7364 draws，仍约 0.6–0.7 FPS，暂不默认启用。'
      '额外影图估算 32 MiB，完整矩阵/变形及静态输入逐帧检查。此前原顺序合批也保持关闭。'
      '普通预览仍保留原完整阴影/静止帧缓存。goal ACTIVE、16 项 OPEN，继续显示性能和原车全部机械目标。**')
    if notice not in content:
        title,rest=content.split('\n',1);path.write_text(title+'\n\n'+notice+'\n\n此前阶段：\n'+rest,encoding='utf-8')
files=guides+['lib/partitionedShadowCache.ts','lib/directionalShadowCache.ts','lib/compositedShadows.ts','lib/vehicleViewport.ts',
 'scripts/verify-partitioned-shadow.mjs','scripts/verify-directional-shadow-cache.mjs','scripts/verify-partitioned-shadow-integrity.py',
 'scripts/summarize-partitioned-shadow.py','scripts/archive-partitioned-shadow-stage.py','docs/PARTITIONED_SHADOW_EXPERIMENT_20260909.md']
for directory in ['work/partitioned-shadow','outputs/partitioned-shadow']:
    files.extend(p.relative_to(root).as_posix() for p in (root/directory).rglob('*') if p.is_file())
assert (root/'outputs/partitioned-shadow/final-normal-ax.txt').is_file()
manifest=[]
for relative in sorted(set(files)):
    source=(root/relative).resolve();assert source.is_relative_to(root.resolve()) and source.is_file()
    target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    digest=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
    manifest.append({'path':relative,'bytes':source.stat().st_size,'sha256':digest})
report={'files':len(manifest),'bytes':sum(row['bytes'] for row in manifest),'sha256Verified':True,'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','manifest':manifest}
(destination/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key!='manifest'}))

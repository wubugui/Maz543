from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
destination=root.parent/'restoration/ordered-batches-20260909'
assert destination.resolve().is_relative_to(root.parent.resolve())
if destination.exists():raise SystemExit('Refusing to overwrite archive')
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
for relative in guides:
    path=root/relative;content=path.read_text(encoding='utf-8');doc=('docs/' if '/' not in relative else '')+'ORDERED_BATCH_EXPERIMENT_20260909.md'
    notice=('**最新：[原顺序合批实验]('+doc+') 已修正显示材质克隆排序、批内原始排序与视锥输入，并在完整整车取得 0 像素差。'
      '最终 486 实例 / 30 批次，缓冲从约 393 MB 降至 104 MB，预热配对耗时收益很小，仍仅开发参数启用。'
      '普通预览保留定向阴影缓存，全部部件/机械/导出不变。完整 goal ACTIVE、16 项 OPEN，继续实际性能与完整机械工作。**')
    if notice not in content:
        title,rest=content.split('\n',1);path.write_text(title+'\n\n'+notice+'\n\n此前阶段：\n'+rest,encoding='utf-8')
files=guides+['lib/orderedBatchDraws.ts','lib/displayBatches.ts','lib/exactBatchMatrices.ts','lib/vehicleViewport.ts',
  'scripts/verify-ordered-batches.mjs','scripts/verify-ordered-batches-integrity.py','scripts/summarize-ordered-batches.py',
  'scripts/archive-ordered-batches-stage.py','docs/ORDERED_BATCH_EXPERIMENT_20260909.md']
for directory in ['work/ordered-batches','outputs/ordered-batches']:
    files.extend(p.relative_to(root).as_posix() for p in (root/directory).rglob('*') if p.is_file())
assert (root/'outputs/ordered-batches/final-normal-ax.txt').is_file()
manifest=[]
for relative in sorted(set(files)):
    source=(root/relative).resolve();assert source.is_relative_to(root.resolve()) and source.is_file()
    target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    digest=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
    manifest.append({'path':relative,'bytes':source.stat().st_size,'sha256':digest})
report={'files':len(manifest),'bytes':sum(row['bytes'] for row in manifest),'sha256Verified':True,'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','manifest':manifest}
(destination/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key!='manifest'}))

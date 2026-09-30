from pathlib import Path
import hashlib,json,shutil

root=Path(__file__).resolve().parents[1]
destination=root.parent/'restoration/directional-shadow-cache-20260909'
assert destination.resolve().is_relative_to(root.parent.resolve())
if destination.exists():raise SystemExit('Refusing to overwrite existing archive')
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
for relative in guides:
    path=root/relative;content=path.read_text(encoding='utf-8')
    doc=('docs/' if '/' not in relative else '')+'DIRECTIONAL_SHADOW_CACHE_20260909.md'
    notice=('**最新：[定向光跨帧阴影复用]('+doc+') 已接入普通预览，逐项精确比较阴影输入；静止与侧视对照 0 像素差，'
      '复用时少 2322 次绘制、约 540 万三角形，开门变化恢复重绘。12 帧顺序样本平均间隔改善约 4.8%，'
      '动态整车仍慢；WebGPU 适配器当前不可用。全部机械/导出/姿态保留。完整 goal ACTIVE、16 项 OPEN，继续保精度优化与机械实现。**')
    if notice not in content:
        title,rest=content.split('\n',1);path.write_text(title+'\n\n'+notice+'\n\n此前阶段：\n'+rest,encoding='utf-8')
files=guides+['lib/directionalShadowCache.ts','lib/vehicleViewport.ts','scripts/verify-directional-shadow-cache.mjs',
  'scripts/verify-shadow-cache-integrity.py','scripts/summarize-shadow-cache.py','scripts/archive-directional-shadow-cache-stage.py',
  'docs/DIRECTIONAL_SHADOW_CACHE_20260909.md']
for directory in ['work/backend-probe','outputs/backend-probe','outputs/directional-shadow-cache','work/directional-shadow-cache']:
    files.extend(p.relative_to(root).as_posix() for p in (root/directory).rglob('*') if p.is_file())
assert (root/'outputs/directional-shadow-cache/final-normal-ax.txt').is_file()
manifest=[]
for relative in sorted(set(files)):
    source=(root/relative).resolve();assert source.is_relative_to(root.resolve()) and source.is_file()
    target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    digest=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
    manifest.append({'path':relative,'bytes':source.stat().st_size,'sha256':digest})
report={'files':len(manifest),'bytes':sum(row['bytes'] for row in manifest),'sha256Verified':True,'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','manifest':manifest}
(destination/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key!='manifest'}))

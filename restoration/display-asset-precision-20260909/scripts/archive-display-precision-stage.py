from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
target=ROOT.parent/'restoration/display-asset-precision-20260909'
assert not target.exists(),target
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
assets=json.loads((ROOT/'outputs/render-worker-evidence/host-tests.json').read_text())['nativeAssets']
for row in assets:
 row['currentSha256']=digest(ROOT/'public/models'/row['file'])
 assert row['currentSha256']==row['sha256'],row['file']
(ROOT/'outputs/tangent-audit/runtime-asset-integrity.json').write_text(json.dumps({'unchanged':True,'assets':assets},indent=2),encoding='utf8')
guides=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md']
notice='**最新：[显示资产精度与切线追踪]({link}) 已核实旧 Draco 量化造成细面/切线损失；实际整车导出保护性修正 616 个切线，82 个真实表面问题仍未通过。两件原生对象的零量化压缩保持全部三角形角点属性逐位相同，尚未替换运行时资产。整车仍约 0.5 FPS；完整 goal ACTIVE，16 项 OPEN，继续保精度显示优化和机械实现。**\n\n此前阶段：\n\n'
for name in guides:
 p=ROOT/name;text=p.read_text(encoding='utf8');head,rest=text.split('\n',1)
 link=('' if name.startswith('docs/') else 'docs/')+'DISPLAY_ASSET_PRECISION_20260909.md'
 p.write_text(head+'\n\n'+notice.format(link=link)+rest.lstrip('\n'),encoding='utf8')
files=guides+['docs/DISPLAY_ASSET_PRECISION_20260909.md','lib/exportTangents.ts','lib/export-model.ts','lib/binaryGltfBlob.ts',
 'scripts/audit-decoded-tangents.mjs','scripts/audit-native-tangents.py','scripts/verify-export-tangents.mjs','scripts/audit-full-export-tangent-repair.mjs',
 'scripts/export-lossless-samples.py','scripts/verify-lossless-draco.mjs','scripts/compare-worker-exports.py','scripts/validate-worker-export.mjs','scripts/verify-binary-gltf-blob.mjs','scripts/archive-display-precision-stage.py']
for folder in ['outputs/tangent-audit','work/tangent-audit']:
 files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/folder).glob('*')) if p.is_file() and p.suffix!='.cjs')
assert len(set(files))==len(files)
for name in files:assert (ROOT/name).is_file(),name
target.mkdir(parents=True);rows=[]
for name in files:
 src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);sha=digest(src);assert digest(dst)==sha
 rows.append({'path':name,'bytes':src.stat().st_size,'sha256':sha})
report={'wholeGoal':'ACTIVE; all 16 gates OPEN','status':'Whole preview still slow; actual export has 82 tangent errors. Two zero-quantization sample surfaces verified bit-exact; original runtime assets unchanged.','files':rows,'fileCount':len(rows),'totalBytes':sum(row['bytes'] for row in rows)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(target),'files':len(rows),'bytes':report['totalBytes']},indent=2))

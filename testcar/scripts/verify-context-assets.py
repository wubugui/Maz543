from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
baselinePath=root.parent/'restoration/simulation-clock-worker-20260909/outputs/simulation-worker-evidence/asset-integrity.json'
baseline=json.loads(baselinePath.read_text(encoding='utf8'))
assetRoot=(root/'public/models').resolve();rows=[]
for entry in baseline['nativeAssets']:
    path=(assetRoot/entry['file']).resolve();assert path.is_relative_to(assetRoot)
    with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    rows.append({'file':entry['file'],'bytes':path.stat().st_size,'sha256':digest,'matchesImmutableBaseline':digest==entry['sha256']})
report={'passed':all(row['matchesImmutableBaseline'] for row in rows),'baseline':str(baselinePath),'assets':rows}
(root/'outputs/context-frame-audit/asset-integrity.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2));assert report['passed']

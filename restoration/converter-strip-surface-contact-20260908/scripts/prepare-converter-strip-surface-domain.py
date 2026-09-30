"""Collect accepted full-surface states while retaining failed direct solves separately."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
direct=json.loads((ROOT/'work/freewheel-contact/strip-surface-domain.json').read_text());continued=json.loads((ROOT/'work/freewheel-contact/strip-surface-continuation.json').read_text())
rows=[{**r,'path':'direct'} for r in direct['rows'] if r['tipModelValid']]
for branch in continued['branches']:rows.extend({**r,'path':'incremental-static-loading'} for r in branch['accepted'])
report={'fit':direct['fit'],'rows':rows,'directFailures':[{'fraction':r['radialClearanceFraction'],'beta':r['betaRad'],'failure':r.get('failure')} for r in direct['rows'] if not r['tipModelValid']],
 'continuationFailures':[b['failure'] for b in continued['branches'] if b['failure']],
 'limits':'Accepted discrete static states only. Direct failure records retained. Native surface/body/self collision checks are required; no continuous-region or material acceptance.'}
(ROOT/'work/freewheel-contact/strip-surface-verified-domain.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'states':len(rows),'directFailures':len(report['directFailures']),'continuationFailures':report['continuationFailures']}))

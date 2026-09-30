"""Refinement at the newly discovered strip/wedge contact state."""
from pathlib import Path
import json
from converter_strip_spring import rest_curve
from converter_strip_pocket import PocketStripSpring
ROOT=Path(__file__).resolve().parents[1];d=json.loads((ROOT/'work/freewheel-contact/strip-pocket-domain.json').read_text());centre=d['rows'][-1]['centreM'];rows=[]
failures=[]
for scale in [1,2,4,8]:
    beam=PocketStripSpring(rest_curve(32*scale,12*scale))
    try:
        s=beam.solve(centre)
        rows.append({'segments':beam.n,'forceN':s['forceN'],'energyJ':s['energyJ'],'wedgeForceN':sum(c['forceN'] for c in s['wedgeContacts']),
          'minimumPlaneGapM':s['minimumWedgePlaneGapM'],'stableStiffnessNm':s['minimumConstrainedStiffnessNm']})
    except Exception as error:failures.append({'segments':beam.n,'failure':str(error)})
for row in rows:row['relativeForceDifferenceToFinestSolved']=abs(row['forceN']-rows[-1]['forceN'])/rows[-1]['forceN']
report={'centreM':centre,'rows':rows,'failures':failures,'limits':'Discretization comparison only. Does not establish original spring, clamped support, material or strength.'}
(ROOT/'outputs/converter-strip-pocket-refinement.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2),flush=True)
if failures:raise SystemExit(1)

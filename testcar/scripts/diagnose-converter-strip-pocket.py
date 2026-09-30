"""Constrained ribbon/wedge sweep; retains all failures instead of hiding them."""
from pathlib import Path
import json,numpy as np
from converter_strip_pocket import PocketStripSpring
from converter_strip_spring import rest_curve
ROOT=Path(__file__).resolve().parents[1];source=json.loads((ROOT/'work/freewheel-contact/strip-domain.json').read_text())
beam=PocketStripSpring(rest_curve(128,48));rows=[]
for old in source['rows']:
    row={k:v for k,v in old.items() if k not in ['solution','tipModelValid','failure']}
    try:
        r=beam.solve(old['centreM'],initial=old.get('solution',{}).get('angles'));row['solution']=r
        row['tipModelValid']=bool(r['minimumBeamCapsuleGapM']>=-1e-8 and (r['forceN']==0 or r['tipCapFacesRoller']>0) and r['minimumConstrainedStiffnessNm']>0 and r['minimumWedgePlaneGapM']>=-1e-10 and all(x['forceN']>=-1e-7 for x in r['wedgeContacts']))
    except Exception as error:row.update({'tipModelValid':False,'failure':str(error)})
    rows.append(row)
report={'fit':source['fit'],'rows':rows,'limits':'Fitted clamped spring, roller tip plus ribbon/wedge contact. Finite width, unknown material and seat require further acceptance. No continuous motion is implied.'}
(ROOT/'work/freewheel-contact/strip-pocket-domain.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'points':len(rows),'valid':sum(r['tipModelValid'] for r in rows),'failures':[r for r in rows if not r['tipModelValid']],
  'wedgeContacts':[{'beta':r['betaRad'],'radial':r['radialClearanceFraction'],'contacts':r['solution']['wedgeContacts'],'forceN':r['solution']['forceN'],'minGapM':r['solution']['minimumWedgePlaneGapM']} for r in rows if 'solution' in r and r['solution']['wedgeContacts']]},indent=2),flush=True)

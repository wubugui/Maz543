"""Compare pre-exit trajectory samples without rerunning either integrator."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
runs=[json.loads((ROOT/f'outputs/converter-strip-dynamics-{hz}hz-88segments-drive10.json').read_text()) for hz in [4000,8000]]
samples=[]
for time in [.5,.8,1.,1.01]:
    a,b=[min(run['rows'],key=lambda row:abs(row['time']-time)) for run in runs]
    assert abs(a['time']-time)<1e-9 and abs(b['time']-time)<1e-9
    samples.append({'time':time,'coarseOmega':a['v'][3],'fineOmega':b['v'][3],
      'relativeOmegaDifference':abs(a['v'][3]-b['v'][3])/max(1,abs(b['v'][3])),
      'coarseBeta':a['q'][1]-a['q'][3],'fineBeta':b['q'][1]-b['q'][3],
      'coarseEnergy':a['kinetic']+a['springEnergy'],'fineEnergy':b['kinetic']+b['springEnergy']})
report={'comparedRates':[4000,8000],'failure':[r['failure'] for r in runs],
 'maxStepEnergyGainJ':[r['maxStepEnergyGainJ'] for r in runs],'samples':samples,
 'limits':'Both runs stop at the unexamined angular-domain boundary. Agreement before failure is not full trajectory or original-vehicle acceptance.'}
(ROOT/'outputs/converter-strip-dynamics-step-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))

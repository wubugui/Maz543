"""Replay one rejected continuous step at decreasing sizes, preserving its seed."""
from pathlib import Path
import json, time, sys
import numpy as np
from converter_strip_spring import rest_curve
from converter_strip_surface_contact import SurfaceContactStrip
from converter_strip_dynamics import StripFreewheel
from converter_strip_cartesian_dynamics import CartesianStripFreewheel

ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'outputs/converter-strip-surface-resumed-dynamics.json').read_text())
seed=source['rows'][-1]
props=json.loads((ROOT/'outputs/converter-strip-inertia.json').read_text())
rows=[]
for divisor in [1,2,4,8,16,32]:
    beam=SurfaceContactStrip(rest_curve(64,24))
    cls=CartesianStripFreewheel if '--cartesian' in sys.argv else StripFreewheel
    system=cls(beam,props['roller']['massKg'],props['roller']['axialInertiaKgM2'],props['outerInertiaKgM2'],minimum_beta=-.115)
    system.spring_state=seed['strip'];q=np.asarray(seed['q']);force,strip=system.spring(q)
    old={**seed,'q':q,'v':np.asarray(seed['v']),'strip':strip,'springGeneralized':force}
    h=.00025/divisor;start=time.perf_counter()
    try:
        s=system.step(old,10.,h)
        row={'h':h,'success':True,'q':s['q'].tolist(),'v':s['v'].tolist(),
             'energyExcessJ':s['kinetic']+s['springEnergy']-old['kinetic']-old['springEnergy']-(s['inputWork']-old['inputWork']),
             'strip':s['strip']}
    except Exception as e:row={'h':h,'success':False,'error':str(e)}
    row['elapsedSeconds']=time.perf_counter()-start;rows.append(row)
    print(json.dumps({k:v for k,v in row.items() if k!='strip'}),flush=True)
report={'coordinates':'Cartesian' if '--cartesian' in sys.argv else 'polar','seedTime':seed['time'],'seed':seed,'rows':rows,'limits':'One-step sensitivity only; does not validate prior trajectory or repair a failed run.'}
suffix='-cartesian' if '--cartesian' in sys.argv else ''
(ROOT/f'outputs/converter-strip-surface-step-sensitivity{suffix}.json').write_text(json.dumps(report,indent=2),encoding='utf8')

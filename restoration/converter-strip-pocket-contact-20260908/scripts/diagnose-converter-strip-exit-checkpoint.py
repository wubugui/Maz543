"""Resume the saved pre-exit sample; do not rerun the complete failure history."""
from pathlib import Path
import math,json,numpy as np
from converter_strip_pocket import PocketStripSpring
from converter_strip_spring import rest_curve
from converter_strip_dynamics import StripFreewheel,PocketDomainExit
ROOT=Path(__file__).resolve().parents[1];source=json.loads((ROOT/'outputs/converter-strip-dynamics-4000hz-88segments-drive10.json').read_text())
props=source['inertia'];sample=source['rows'][-1];beam=PocketStripSpring(rest_curve(64,24))
system=StripFreewheel(beam,props['roller']['massKg'],props['roller']['axialInertiaKgM2'],props['outerInertiaKgM2']);system.initial_angles=sample['strip']['angles']
q=np.array(sample['q']);generalized,strip=system.spring(q)
state={**sample,'q':q,'v':np.array(sample['v']),'strip':strip,'springGeneralized':generalized};exit_event=None;records=[]
def snapshot(s):return {'time':s['time'],'q':s['q'].tolist(),'v':s['v'].tolist(),'inputWork':s['inputWork'],'kinetic':s['kinetic'],'springEnergy':s['springEnergy'],
 'gaps':s['gaps'],'normalForce':s['normalForce'],'frictionForce':s['frictionForce'],'strip':s['strip']}
records.append(snapshot(state))
for i in range(30):
    try:state=system.step(state,10.,1/source['hz']);records.append(snapshot(state))
    except PocketDomainExit as error:
        R,phi,spin,angle=error.candidate_q;local=R*np.array([math.cos(phi-angle),math.sin(phi-angle)])
        exit_event={'acceptedTime':state['time'],'candidateTime':state['time']+1/source['hz'],'beta':error.beta,
          'candidatePolarQ':error.candidate_q.tolist(),'localCentreM':local.tolist()};break
assert exit_event is not None
assert abs(exit_event['acceptedTime']-source['failure']['time'])<1e-10
report={'resumeTime':sample['time'],'states':records,'exit':exit_event,
 'limits':'Unmodified accepted-state replay from the saved 100 Hz sample. Candidate lies outside the audited region; no boundary expansion or completion claim.'}
(ROOT/'work/freewheel-contact/strip-domain-exit-checkpoint.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'resumeTime':sample['time'],'savedStates':len(records),'exit':exit_event},indent=2),flush=True)

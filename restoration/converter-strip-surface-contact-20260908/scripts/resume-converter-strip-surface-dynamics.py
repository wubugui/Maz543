"""Resume the rejected-domain event with newly verified body-contact mechanics.
This diagnostic does not publish or claim a complete vehicle animation.
"""
from pathlib import Path
import json,math,time,numpy as np
from converter_strip_spring import rest_curve
from converter_strip_surface_contact import SurfaceContactStrip
from converter_strip_dynamics import StripFreewheel
ROOT=Path(__file__).resolve().parents[1];checkpoint=json.loads((ROOT/'work/freewheel-contact/strip-domain-exit-checkpoint.json').read_text());seed=checkpoint['states'][-1]
props=json.loads((ROOT/'outputs/converter-strip-inertia.json').read_text());beam=SurfaceContactStrip(rest_curve(64,24))
system=StripFreewheel(beam,props['roller']['massKg'],props['roller']['axialInertiaKgM2'],props['outerInertiaKgM2'],minimum_beta=-.115)
system.spring_state=seed['strip'];system.initial_angles=seed['strip']['angles'];q=np.array(seed['q']);generalized,strip=system.spring(q)
assert abs(system.N*strip['energyJ']-seed['springEnergy'])<1e-8,'The checkpoint must agree before adding new motion'
state={**seed,'q':q,'v':np.array(seed['v']),'springGeneralized':generalized,'strip':strip};rows=[];failure=None;steps=0;start=time.perf_counter();max_step_energy=0.
def save(s,torque):return {'time':s['time'],'q':s['q'].tolist(),'v':s['v'].tolist(),'torque':torque,'inputWork':s['inputWork'],
 'kinetic':s['kinetic'],'springEnergy':s['springEnergy'],'gaps':s['gaps'],'normalForce':s['normalForce'],'frictionForce':s['frictionForce'],'strip':s['strip']}
rows.append(save(state,10.));h=.00025
while state['time']<2.-h/2:
    torque=10. if state['time']<1.2-1e-10 else -2.;old=state
    try:state=system.step(old,torque,h)
    except Exception as error:failure={'time':old['time'],'error':str(error)};break
    steps+=1
    excess=state['kinetic']+state['springEnergy']-old['kinetic']-old['springEnergy']-(state['inputWork']-old['inputWork']);max_step_energy=max(max_step_energy,excess)
    if steps%20==0:rows.append(save(state,torque))
    if steps%1000==0:print(json.dumps({'time':state['time'],'omega':state['v'][3],'beta':state['q'][1]-state['q'][3],'elapsed':time.perf_counter()-start}),flush=True)
if rows[-1]['time']!=state['time']:rows.append(save(state,torque))
report={'complete':failure is None,'failure':failure,'resumeTime':seed['time'],'hz':4000,'steps':steps,'model':'full ribbon surface contact; explicit spring force in contact dynamics',
 'diagnosticMinimumBeta':system.minimum_beta,'maximumSingleStepEnergyExcessJ':max_step_energy,'elapsedSeconds':time.perf_counter()-start,'rows':rows,
 'limits':'New deeper-contact model under fitted clamped/material/density/friction assumptions. Discrete native geometry and load checks precede this test; actual resumed trajectory still requires native and energy validation. Failed runs are incomplete.'}
(ROOT/'outputs/converter-strip-surface-resumed-dynamics.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)
if failure:raise SystemExit(1)

"""Continuous fitted contact run; partial failure traces are explicitly incomplete."""
from pathlib import Path
import argparse,json,time,math,hashlib
import numpy as np
from converter_strip_pocket import PocketStripSpring
from converter_strip_spring import rest_curve
from converter_strip_dynamics import StripFreewheel
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--hz',type=int,default=4000);parser.add_argument('--duration',type=float,default=2.);parser.add_argument('--scale',type=int,default=2);parser.add_argument('--drive-torque',type=float,default=2.);args=parser.parse_args()
props=json.loads((ROOT/'outputs/converter-strip-inertia.json').read_text());beam=PocketStripSpring(rest_curve(32*args.scale,12*args.scale))
system=StripFreewheel(beam,props['roller']['massKg'],props['roller']['axialInertiaKgM2'],props['outerInertiaKgM2'])
state=system.initial();initial_energy=state['springEnergy'];rows=[];failure=None;max_residual=0.;min_gap=1.;max_energy_surplus=0.;max_step_energy_gain=0.;min_beta=0.;max_beta=0.;start=time.perf_counter()
def compact(s,torque):
    r=s['strip'];R,phi,spin,outer=s['q']
    return {'time':s['time'],'q':s['q'].tolist(),'v':s['v'].tolist(),'torque':torque,'inputWork':s['inputWork'],
      'kinetic':s['kinetic'],'springEnergy':s['springEnergy'],'gaps':s['gaps'],'normalForce':s['normalForce'],'frictionForce':s['frictionForce'],
      'strip':{k:r[k] for k in ['points','angles','forceN','energyJ','maximumIncrementalBendingStressPa','minimumWedgePlaneGapM','wedgeContacts']}}
rows.append(compact(state,-2.))
for step in range(round(args.duration*args.hz)):
    t=step/args.hz;torque=-2. if t<.4 or t>=1.2 else args.drive_torque;old=state
    try:state=system.step(old,torque,1/args.hz)
    except Exception as error:failure={'step':step,'time':old['time'],'error':str(error)};break
    max_residual=max(max_residual,state['residual']);min_gap=min(min_gap,*state['gaps'])
    beta=math.atan2(math.sin(state['q'][1]-state['q'][3]),math.cos(state['q'][1]-state['q'][3]));min_beta=min(min_beta,beta);max_beta=max(max_beta,beta)
    max_energy_surplus=max(max_energy_surplus,state['kinetic']+state['springEnergy']-initial_energy-state['inputWork'])
    max_step_energy_gain=max(max_step_energy_gain,state['kinetic']+state['springEnergy']-old['kinetic']-old['springEnergy']-(state['inputWork']-old['inputWork']))
    if (step+1)%max(1,args.hz//100)==0:rows.append(compact(state,torque))
    if (step+1)%args.hz==0:print(json.dumps({'time':state['time'],'outerOmega':state['v'][3],'elapsed':time.perf_counter()-start}),flush=True)
report={'complete':failure is None,'failure':failure,'hz':args.hz,'segments':beam.n,'requestedDuration':args.duration,'driveTorqueNm':args.drive_torque,
 'inertia':props,'frictionFit':system.mu,'fit':{'widthM':beam.width,'thicknessM':beam.thickness,'youngPa':beam.young},'rows':rows,
 'maxContactResidual':max_residual,'minimumRollerGapM':min_gap,'maxEnergySurplusJ':max_energy_surplus,'maxStepEnergyGainJ':max_step_energy_gain,
 'betaRangeRad':[min_beta,max_beta],'elapsedSeconds':time.perf_counter()-start,
 'limits':'External torque drives one fitted twelve-cell row; massless quasi-static strip, unknown material and clamped seat, fitted density/friction. No reactor fluid or vehicle coupling. Incomplete traces never constitute successful dynamics.'}
tag='' if args.drive_torque==2 else f'-drive{args.drive_torque:g}'
target=ROOT/f'outputs/converter-strip-dynamics-{args.hz}hz-{beam.n}segments{tag}.json';target.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['rows','inertia']},indent=2),flush=True)
if failure:raise SystemExit(1)

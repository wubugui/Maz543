"""Independent small-deflection beam reference and curved-contact mesh refinement."""
from pathlib import Path
import json,numpy as np
from converter_strip_spring import StripSpring,rest_curve
ROOT=Path(__file__).resolve().parents[1];cantilever=[]
for n in [16,32,64]:
    L=.02;beam=StripSpring(np.stack([np.linspace(0,L,n+1),np.zeros(n+1)],axis=1));F=.001
    # Infinitesimal transverse endpoint load. No contact-solver reuse.
    torque=F*beam.lengths;delta=np.linalg.solve(beam.K,torque)
    deflection=float(np.dot(beam.lengths,delta));reference=F*L**3/(3*beam.EI)
    cantilever.append({'segments':n,'deflectionM':deflection,'EulerBernoulliDeflectionM':reference,'relativeError':abs(deflection-reference)/reference})
assert cantilever[-1]['relativeError']<.001 and cantilever[-1]['relativeError']<cantilever[0]['relativeError']/10
refinement=[]
for scale in [1,2,4]:
    beam=StripSpring(rest_curve(32*scale,12*scale));s=beam.solve([.06225,0]);refinement.append({'segments':beam.n,'forceN':s['forceN'],'energyJ':s['energyJ'],'stressPa':s['maximumIncrementalBendingStressPa']})
for row in refinement:row['relativeForceDifferenceToFine']=abs(row['forceN']-refinement[-1]['forceN'])/refinement[-1]['forceN']
assert refinement[1]['relativeForceDifferenceToFine']<.002
report={'straightCantilever':cantilever,'curvedStripRefinement':refinement,'limits':'Checks the discretized inextensible bending formulation. Does not validate original MAZ spring shape, seating, constitutive material, preload or strength.'}
(ROOT/'outputs/converter-strip-formulation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2),flush=True)

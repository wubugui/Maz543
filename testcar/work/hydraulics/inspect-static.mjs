import {initialTransmissionDynamics,stepTransmission,CLUTCH_SLIP} from './transmissionDynamics.mjs';
for(const [name,gear] of [['first',1],['second',2],['direct',3],['reverse',-1]]){
 let s=initialTransmissionDynamics();for(let j=0;j<1440;j++)s=stepTransmission(s,83.1,gear,'high',100,20550,.75,1/240);
 const b=CLUTCH_SLIP[name],l=s.clutchTorque[name];console.log(name,{a:s.inputOmega,c:s.outputOmega,slip:s.clutchSlip[name],p:s.hydraulics.boosters[name].pressure,cap:s.hydraulics.boosters[name].capacity,l,inputResidual:s.converterTorque+b[0]*l,outputResidual:s.roadTorque+b[1]*l});
}

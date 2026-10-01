// Map a verified installation datum into the existing FITTED linkage only.
// Does not change geometry, stop limits, preload, masses or application state.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
const {SUSPENSION:P,wheelGeometry,suspensionPose}=await import('../lib/suspension.ts');
const root=new URL('../',import.meta.url);
const read=async p=>JSON.parse(await fs.readFile(new URL(p,root),'utf8'));
const reference=await read('reference/suspension-installation-1977.json');
assert.equal(reference.variant,'MAZ-543A');
const drop=q=>P.lower[0]-wheelGeometry(q).lower[0];
let previous=Infinity;
for(let i=0;i<=100;i++){
 const value=drop(P.minGeometryTravel*(1-i/100));
 assert.ok(value<=previous+1e-9,'Installation mapping requires monotone current linkage');previous=value;
}
function solve(target){
 let lo=P.minGeometryTravel,hi=0;
 assert.ok(drop(lo)>target && drop(hi)<target,'Reference outside fitted linkage domain');
 for(let i=0;i<64;i++){const mid=(lo+hi)/2;if(drop(mid)>target)lo=mid;else hi=mid;}
 const q=(lo+hi)/2,g=wheelGeometry(q);
 assert.ok(Math.abs(drop(q)-target)<1e-7,'Current inverse-linkage residual');
 return {requestedVerticalDropM:target,achievedVerticalDropM:drop(q),fittedWheelTravelParameterM:q,
  fittedLowerAngleDegrees:g.lowerAngle*180/Math.PI,
  fittedUpperAngleFromHorizontalDegrees:Math.atan2(g.upper[0]-P.upper[0],g.upper[1]-P.upper[1])*180/Math.PI,
  pose:suspensionPose(Array(8).fill(q))};
}
const measurements=[reference.lowerArmHeadCentersVerticalSeparationM.minimum,.1385,reference.lowerArmHeadCentersVerticalSeparationM.maximum].map(solve);
const zero=wheelGeometry(0);
const report={status:'SOURCE_DATUM_RESOLVED; FITTED_LINKAGE_MAPPING_ONLY',reference,
 currentModel:{sourceSHA256:crypto.createHash('sha256').update(await fs.readFile(new URL('lib/suspension.ts',root))).digest('hex'),
  lowerInner:P.lower,lowerOuterAtDeclaredZero:zero.lower,declaredZeroVerticalDropM:drop(0),
  declaredZeroUpperAngleFromHorizontalDegrees:Math.atan2(zero.upper[0]-P.upper[0],zero.upper[1]-P.upper[1])*180/Math.PI,
  configuredDroopStopParameterM:P.droopStop,verticalDropAtConfiguredDroopStopM:drop(P.droopStop),
  configuredCompressionStopParameterM:P.compressionStop,geometryDomain:[P.minGeometryTravel,P.maxGeometryTravel]},
 measurements,interpretation:'The solved q/angles are consequences of reconstructed hardpoints, not factory measurements. The installation datum is not an unloaded equilibrium or wheel-travel specification. Stop contact, preload and full-load/empty/installation pose correspondence remain uncalibrated.',
 changedProductionOrPhysics:false,wholeVehicleAcceptance:'16 OPEN'};
const output=new URL('outputs/cloud-suspension-installation-20261001/',root);await fs.mkdir(output,{recursive:true});
await fs.writeFile(new URL('reference-mapping.json',output),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,zeroDropM:report.currentModel.declaredZeroVerticalDropM,atConfiguredDroopStopM:report.currentModel.verticalDropAtConfiguredDroopStopM,measurements:measurements.map(({pose,...r})=>r),output:fileURLToPath(output)},null,2));

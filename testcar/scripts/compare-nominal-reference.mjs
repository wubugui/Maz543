// Record reference/model differences; never alter model, mass or test thresholds to force agreement.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import crypto from 'node:crypto';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
const {SPECS}=await import('../lib/mechanics.ts');
const {SUSPENSION,initialSuspension}=await import('../lib/suspension.ts');
const reference=JSON.parse(await fs.readFile('reference/maz543a-nominal-1977.json','utf8'));
const native=JSON.parse(await fs.readFile('outputs/cloud-nominal-envelope-20260930/native-envelopes.json','utf8'));
assert.equal(reference.variant,'MAZ-543A');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
for(const f of native.files)assert.equal(hash(await fs.readFile('outputs/'+f.file)),f.sha256,'Measured native source changed; rerun actual geometry audit');
const baseline=native.files[0].allActive;assert.deepEqual(native.files[1].allActive.extentXYZ,baseline.extentXYZ,'Native whole-envelope parity');
const bodyLength=baseline.extentXYZ[0],d=reference.dimensions;
const normal=initialSuspension().normal,frontNormalN=normal.slice(0,4).reduce((a,b)=>a+b,0),rearNormalN=normal.slice(4).reduce((a,b)=>a+b,0);
const wheelChecks=native.files.map(f=>{const c=f.wheelSpinCenters;return {file:f.file,extremeSpanM:c[6].spinWorldXYZ[0]-c[0].spinWorldXYZ[0],tracksM:[0,2,4,6].map(i=>Math.abs(c[i].spinWorldXYZ[1]-c[i+1].spinWorldXYZ[1]))};});
for(const r of wheelChecks){assert.ok(Math.abs(r.extremeSpanM-d.extremeAxleSpanM)<1e-5);assert.ok(r.tracksM.every(v=>Math.abs(v-d.trackM)<1e-5));}
const report={status:'BASELINE_MEASURED_REFERENCE_CALIBRATION_REMAINS_OPEN',factoryReference:reference,
 actualNative:{lengthM:bodyLength,allActive:baseline,excludingNamedMirrors:native.files[0].excludingNamedMirrors,unladenHeightConventionNotEstablished:true,wheelChecks},
 differences:{lengthToNominalM:bodyLength-d.lengthM.nominal,lengthToLowerNominalBoundM:bodyLength-(d.lengthM.nominal-d.lengthM.plusMinus),searchlightTopZToNominalM:baseline.maxXYZ[2]-d.unladenSearchlightHeightM.nominal,warning:'Differences identify calibration work. They do not establish which overhang/component must move; width/height measurement conventions and posture remain unresolved.'},
 currentNumericalParameters:{specLengthM:SPECS.length,vehicleMassKg:SPECS.mass,sprungMassKg:SUSPENSION.sprungMass,unsprungMassEachKg:SUSPENSION.unsprungMass,totalSuspensionMassKg:SUSPENSION.sprungMass+8*SUSPENSION.unsprungMass,initialFrontGroupNormalN:frontNormalN,initialRearGroupNormalN:rearNormalN,initialFrontFraction:frontNormalN/(frontNormalN+rearNormalN)},
 massInterpretation:'20550 kg matches the base-543 table entry but is below the 543A upper-limit entry; this alone is not an upper-limit failure. Equal model static axle-group loads do not reproduce the handbook nominal 15200/5800 kg split. Neither individual wheel masses nor chassis inertia may be inferred from that group split alone.',
 changesAppliedToGeometryOrDynamics:false,wholeVehicleAcceptance:'16 OPEN'};
await fs.writeFile('outputs/cloud-nominal-envelope-20260930/reference-comparison.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,lengthM:bodyLength,lengthToNominalM:report.differences.lengthToNominalM,modelFrontFraction:report.currentNumericalParameters.initialFrontFraction,referenceFrontFraction:15200/21000,geometryOrDynamicsChanged:false},null,2));

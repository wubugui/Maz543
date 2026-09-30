// Compare the fitted force solver with dimensions measured from saved coils.
// Run the native hardware reader and hydraulic regression before this script.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const temporary=process.argv.includes('--geometry-only');
const native=JSON.parse(await fs.readFile(`${temporary?'work/transmission':'outputs'}/transmission-spring-hardware-checks.json`,'utf8'));
const {initialHydraulics,stepHydraulics,HYDRAULIC_FIT,BOOSTER_MECHANICAL_FIT,pistonArea,springRate}=await import('../work/hydraulics/transmissionHydraulics.mjs');
const {CLUTCH_PACKS,clutchContactTravel}=await import('../work/hydraulics/transmission.mjs');
const rows=[];
for(const row of native.packs){
  const name=row.pack,pack=CLUTCH_PACKS[name],d=row.wireDiameterM,D=row.meanCoilDiameterM,n=row.effectiveTurnsMeasured;
  const single=HYDRAULIC_FIT.steelShear*d**4/(8*D**3*n),total=single*row.springs;
  assert.ok(Math.abs(total-springRate(name))/total<1e-6);
  let state=initialHydraulics();
  for(let i=0;i<1680;i++)state=stepHydraulics(state,pack.gear,600*Math.PI/30/.831,0,1/240);
  const b=state.boosters[name],preload=BOOSTER_MECHANICAL_FIT[name].preload,L=clutchContactTravel(name);
  assert.equal(b.travel,L);assert.equal(b.velocity,0);
  const force=preload+total*L,expectedNormal=pistonArea(name)*b.pressure-force;
  assert.ok(Math.abs(expectedNormal-b.normalForce)<.02);
  const index=D/d,wahl=(4*index-1)/(4*index-4)+.615/index;
  rows.push({pack:name,count:row.springs,measuredSingleCoilRateNPerM:single,totalRateNPerM:total,
    fittedAssemblyPreloadN:preload,impliedUnloadedLengthM:row.installedLengthM+preload/total,
    fullTravelSpringForceN:force,normalForceErrorN:Math.abs(expectedNormal-b.normalForce),
    fittedMaximumWireShearPa:wahl*8*(force/row.springs)*D/(Math.PI*d**3)});
}
const report={packs:rows,limits:'Measured native coil dimensions with linear helical-spring formula and fitted steel shear modulus. Assembly preload is not independently sourced; implied free length and Wahl stress are diagnostic values, not factory dimensions or fatigue acceptance.'};
await fs.writeFile(`${temporary?'work/transmission':'outputs'}/transmission-spring-force-checks.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));

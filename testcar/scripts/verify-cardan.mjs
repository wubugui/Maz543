import fs from 'node:fs/promises';import assert from 'node:assert/strict';
import {validateBytes} from 'gltf-validator';
import {CARDAN,cardanPose,cardanMechanism} from '../work/compiled/cardan.mjs';
let worstOrthogonal=0,worstPhase=0,worstRolling=0;const samples=[];
for(const bend of [0,10,20,30])for(const extension of [0,40])for(let j=0;j<=96;j++){
  const angle=j*Math.PI*2/96,m=cardanMechanism(angle,bend,extension),p=cardanPose(angle,bend,extension);
  const d=(a,b)=>a.reduce((n,x,i)=>n+x*b[i],0);
  worstOrthogonal=Math.max(worstOrthogonal,Math.abs(d(m.a,m.b)),Math.abs(d(m.a,m.u)),Math.abs(d(m.b,m.v)),Math.abs(d(m.a2,m.b)));
  worstPhase=Math.max(worstPhase,Math.abs(Math.atan2(Math.sin(m.outputAngle-angle),Math.cos(m.outputAngle-angle))));
  assert.ok(m.splineOverlap>=.024999&&m.splineEndGap>=.015999);
  for(const pose of Object.values(p))assert.ok(Math.abs(Math.hypot(...pose.q)-1)<1e-12);
  const h=1e-6,m1=cardanMechanism(angle+h,bend,extension),p1=cardanPose(angle+h,bend,extension);
  const yAngle=q=>2*Math.atan2(q[1],q[3]);
  for(const kind of ['flange','shaft']){
    const key=kind==='flange'?'inputTwist':'middleTwist',wi=(m1[key]-m[key])/h;
    const c=`CJ_needles_0_${kind}_1`,r=`CJ_roller_0_${kind}_1_0`;
    const wc=(yAngle(p1[c].q)-yAngle(p[c].q))/h;
    const wr=wc+(yAngle(p1[r].q)-yAngle(p[r].q))/h;
    const R=CARDAN.rollerPitch,radius=CARDAN.rollerRadius;
    worstRolling=Math.max(worstRolling,Math.abs(R*wc+radius*wr),Math.abs(R*wc-radius*wr-(R-radius)*wi));
  }
  if(j%4===0)samples.push({angle,bend,extension,pose:Object.fromEntries(Object.entries(p).filter(([n])=>/^CJ_(flange|shaft|cross)_\d$/.test(n)))});
}
assert.ok(worstOrthogonal<1e-12&&worstPhase<1e-12&&worstRolling<1e-9);
const bytes=await fs.readFile('public/models/maz543a-cardan.glb');
const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
const nodes=new Set(gltf.nodes.map(n=>n.name));
for(const name of Object.keys(cardanPose(0)))assert.ok(nodes.has(name),`Missing native binding ${name}`);
const validation=await validateBytes(new Uint8Array(bytes));assert.equal(validation.issues.numErrors,0);assert.equal(validation.issues.numWarnings,0);
await fs.writeFile('work/cardan-clearance-samples.json',JSON.stringify(samples));
const report={samples:776,joints:190,worstOrthogonal,worstPhase,worstRolling,minimumSplineOverlapMM:25,minimumSplineEndGapMM:16,
  middleSpeedRatioAt30Degrees:[Math.cos(Math.PI/6),1/Math.cos(Math.PI/6)],bytes:bytes.length,errors:validation.issues.numErrors,warnings:validation.issues.numWarnings,
  limits:'Independent fitted equal-angle Cardan rig; no vehicle installation, bearing load capacity, measured spline fits or exact 543 suffix interchangeability acceptance.'};
await fs.writeFile('outputs/cardan-kinematic-verification.json',JSON.stringify(report,null,2));console.log(report);

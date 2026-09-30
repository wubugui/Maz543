import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {validateBytes} from 'gltf-validator';
import {D12,rodPair,d12Pose,bankPoint,valveLift,valveWindow,firingPhase} from '../work/compiled/d12.mjs';
const near=(a,b,e=1e-8)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
const dist=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
let mainMin=Infinity,mainMax=-Infinity,slaveMin=Infinity,slaveMax=-Infinity;
for(let k=0;k<=2880;k++){
  const angle=k/2880*4*Math.PI;
  for(let i=0;i<6;i++){
    const p=rodPair(angle,i);near(dist(p.main,p.pin),D12.mainRod);near(dist(p.slave,p.ear),D12.slaveRod);
    const reconstructed=p.pin.map((v,j)=>j===0?v:j===1?v+D12.earAlong*Math.cos(p.mainAngle)-D12.earAcross*Math.sin(p.mainAngle):v+D12.earAlong*Math.sin(p.mainAngle)+D12.earAcross*Math.cos(p.mainAngle));
    near(dist(reconstructed,p.ear),0);
    mainMin=Math.min(mainMin,p.distance);mainMax=Math.max(mainMax,p.distance);slaveMin=Math.min(slaveMin,p.slaveDistance);slaveMax=Math.max(slaveMax,p.slaveDistance);
  }
  if(k%12===0)for(const p of Object.values(d12Pose(angle)))assert.ok([...p.p,p.rx,p.sy??1].every(Number.isFinite));
}
near(mainMax-mainMin,.18,1e-7);near(slaveMax-slaveMin,.1867,1e-6);near(slaveMax,mainMax,1e-6);
// Independent support-function check: the actual authored flat-follower profile
// must touch, not pass through, the flat tappet surface throughout a full cycle.
let contactError=0;
for(const bank of ['L','R'])for(const kind of ['intake','exhaust'])for(let i=0;i<6;i++){
  const beta=bank==='L'?-Math.PI/6:Math.PI/6,sign=kind==='intake'?1:-1;
  const window=valveWindow(kind),center=window.center+firingPhase(bank,i),half=window.half/2;
  const poly=Array.from({length:384},(_,j)=>{const a=j/384*2*Math.PI,delta=((sign*(beta+Math.PI-a)-center/2+Math.PI)%(2*Math.PI)+2*Math.PI)%(2*Math.PI)-Math.PI;
    const u=delta/half,h=Math.abs(u)<1?D12.valveLift*(1-u*u)**2:0;
    const dh=Math.abs(u)<1?sign*4*D12.valveLift*u*(1-u*u)/half:0,r=D12.camBaseRadius+h;
    return [r*Math.cos(a)-dh*Math.sin(a),r*Math.sin(a)+dh*Math.cos(a)];});
  for(let k=0;k<=240;k++){
    const a=k/240*4*Math.PI,normal=beta+Math.PI-sign*a/2;
    const support=Math.max(...poly.map(([y,z])=>y*Math.cos(normal)+z*Math.sin(normal)));
    const expected=D12.camBaseRadius+valveLift(a,bank,i,kind);contactError=Math.max(contactError,Math.abs(support-expected));
    assert.ok(support<=expected+1e-8,'cam penetrates flat tappet');
    assert.ok(expected-support<.000025,'cam loses contact with follower');
    near(D12.camY-D12.camBaseRadius,.525+.119+.017/2);
  }
}
// Check documented event angles independently of the window implementation.
for(const bank of ['L','R'])for(let i=0;i<6;i++)for(const [kind,open,close] of [['intake',340,588],['exhaust',132,380]]){
  const phase=firingPhase(bank,i),at=d=>valveLift(phase+d*Math.PI/180,bank,i,kind);
  near(at(open),0);near(at(close),0);near(at(open-.01),0);near(at(close+.01),0);
  assert.ok(at(open+.1)>0&&at(close-.1)>0,`${bank}${i+1} ${kind} event`);
  const p=d12Pose(2);near(p[`D12_cam_${bank}_intake`].rx,1);near(p[`D12_cam_${bank}_exhaust`].rx,-1);
}
const bytes=await fs.readFile('public/models/d12a525a-engine.glb');
const json=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
const nodes=new Map(json.nodes.map(n=>[n.name,n]));
for(const name of Object.keys(d12Pose(0)))assert.ok(nodes.has(name),`unbound native joint ${name}`);
for(const [prefix,count] of [['D12_piston_L',6],['D12_piston_R',6],['D12_master_rod_',6],['D12_slave_rod_',6],['D12_valve_L',24],['D12_valve_R',24],['D12_spring_L',24],['D12_spring_R',24]]){
  assert.equal([...nodes.keys()].filter(n=>n.startsWith(prefix)&&!n.includes('_D12_')).length,count,prefix);
}
const result=await validateBytes(new Uint8Array(bytes),{uri:'d12a525a-engine.glb',maxIssues:100});
await fs.writeFile('outputs/d12-gltf-validation.json',JSON.stringify(result,null,2));assert.equal(result.issues.numErrors,0,JSON.stringify(result.issues.messages));
const report={mainStroke:mainMax-mainMin,articulatedStroke:slaveMax-slaveMin,topDeadCentreMismatch:Math.abs(mainMax-slaveMax),maximumCamContactError:contactError,kinematicSamples:2881,joints:Object.keys(d12Pose(0)).length,bytes:bytes.length,triangles:json.meshes.reduce((sum,m)=>sum+m.primitives.reduce((s,p)=>s+(p.indices===undefined?json.accessors[p.attributes.POSITION].count:json.accessors[p.indices].count)/3,0),0),errors:result.issues.numErrors,warnings:result.issues.numWarnings,scope:'Geometric linkage consistency; no factory dimensional or physical engine acceptance'};
await fs.writeFile('outputs/d12-verification.json',JSON.stringify(report,null,2));console.log(report);

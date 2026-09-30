import fs from 'node:fs/promises';import assert from 'node:assert/strict';import * as T from 'three';
import {d12Pose} from '../work/compiled/d12.mjs';
const bytes=await fs.readFile('public/models/d12a525a-engine.glb'),g=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
const objects=g.nodes.map(n=>{const o=new T.Object3D();o.name=n.name;if(n.matrix){o.matrix.fromArray(n.matrix);o.matrix.decompose(o.position,o.quaternion,o.scale);}else{if(n.translation)o.position.fromArray(n.translation);if(n.rotation)o.quaternion.fromArray(n.rotation);if(n.scale)o.scale.fromArray(n.scale);}return o;});
g.nodes.forEach((n,i)=>(n.children??[]).forEach(j=>objects[i].add(objects[j])));
const nodes=new Map(objects.map(o=>[o.name,o])),root=nodes.get('D12A_525A');
assert(root);assert(nodes.get('D12_water_rotor'));assert.equal(g.nodes.filter(n=>n.extras?.waterPump&&n.name.startsWith('D12_water_ball_')).length,18);
const labels=new Set(g.nodes.filter(n=>n.extras?.waterPump).map(n=>n.extras.figureItem));for(let j=1;j<=17;j++)assert(labels.has(String(j)),`fig28 item ${j}`);
assert(g.nodes.some(n=>n.extras?.waterHalf===1)&&g.nodes.some(n=>n.extras?.waterHalf===-1));
let axisError=0,centerError=0,rollingError=0;
for(const angle of [0,.173,3.47,4*Math.PI-.0001,4*Math.PI+.0001,80*Math.PI+.3]){
 const p=d12Pose(angle);for(const [name,q] of Object.entries(p)){const o=nodes.get(name);assert(o,name);o.position.fromArray(q.p);o.rotation.set(q.rx,0,0);o.scale.set(1,q.sy??1,1);}root.updateWorldMatrix(true,true);
 const rotor=nodes.get('D12_water_rotor'),axis=new T.Vector3(1,0,0).transformDirection(rotor.matrixWorld);axisError=Math.max(axisError,axis.distanceTo(new T.Vector3(0,-1,0)));
 assert(Math.abs(p.D12_water_rotor.rx-p.D12_timing_lower.rx)<1e-12);
 centerError=Math.max(centerError,rotor.getWorldPosition(new T.Vector3()).distanceTo(new T.Vector3(-.665,-.221,0)));
 // Contact velocity independently derived in the local bearing frame. The outer
 // race must be stationary; the inner contact must match the rotating journal.
 const h=1e-5,p2=d12Pose(angle+h),wi=-1.5;
 for(let b=0;b<2;b++)for(let j=0;j<9;j++){
  const cage=`D12_water_cage_${b}`,ball=`D12_water_ball_${b}_${j}`;
  const wc=(p2[cage].rx-p[cage].rx)/h,wb=wc+(p2[ball].rx-p[ball].rx)/h;
  const outer=wc*.0175+wb*.004,inner=wc*.0175-wb*.004-wi*(.0175-.004);
  rollingError=Math.max(rollingError,Math.abs(outer),Math.abs(inner));
 }
}
assert(axisError<2e-6&&centerError<2e-6&&rollingError<1e-8,{axisError,centerError,rollingError});
const result={all17FigureItems:true,rollingBalls:18,engineBindings:Object.keys(d12Pose(0)).length,axisError,centerError,rollingContactVelocityErrorPerUnitCrankSpeed:rollingError,limits:'Exported transforms and ideal no-slip rolling only; native cavity checked separately; dimensions and load model not certified.'};
await fs.writeFile('outputs/water-web-verification.json',JSON.stringify(result,null,2));console.log(result);

import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import * as T from 'three';
import {d12Pose,D12_TIMING} from '../work/compiled/d12.mjs';
const bytes=await fs.readFile('public/models/d12a525a-engine.glb');
const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
const objects=gltf.nodes.map(n=>{const o=new T.Object3D();o.name=n.name;if(n.matrix){o.matrix.fromArray(n.matrix);o.matrix.decompose(o.position,o.quaternion,o.scale);}else{if(n.translation)o.position.fromArray(n.translation);if(n.rotation)o.quaternion.fromArray(n.rotation);if(n.scale)o.scale.fromArray(n.scale);}return o;});
gltf.nodes.forEach((n,i)=>(n.children??[]).forEach(j=>objects[i].add(objects[j])));
const nodes=new Map(objects.map(o=>[o.name,o]));
const gears=gltf.nodes.filter(n=>n.extras?.timingGearId);assert.equal(gears.length,25,'all original gear identities survive batching');
const expected={crank:1,upper:1.5,lower:1.5,generator_takeoff:1.5,generator:1.75,injection:.5,oil_idler:23/24,oil_pump:1.725,fuel_takeoff:1.5,fuel_feed:11/14,inclined_L:1,inclined_R:1,intake_L:.5,intake_R:.5,exhaust_L:.5,exhaust_R:.5};
let axisError=0,originError=0;
for(const angle of [0,4*Math.PI-.0001,4*Math.PI+.0001,80*Math.PI+.3]){
 const pose=d12Pose(angle);
 for(const [name,p] of Object.entries(pose)){const o=nodes.get(name);assert(o,name);o.position.fromArray(p.p);o.rotation.set(p.rx,0,0);o.scale.set(1,p.sy??1,1);}
 const root=nodes.get('D12A_525A');root.updateWorldMatrix(true,true);const inv=root.matrixWorld.clone().invert();
 for(const [id,sh] of Object.entries(D12_TIMING.shafts)){
  assert(Math.abs(Math.abs(sh.rate)-expected[id])<1e-12,id+' original ratio');
  const o=nodes.get(sh.node),m=new T.Matrix4().multiplyMatrices(inv,o.matrixWorld);
  axisError=Math.max(axisError,new T.Vector3(1,0,0).transformDirection(m).distanceTo(new T.Vector3(...sh.axis)));
  originError=Math.max(originError,new T.Vector3().setFromMatrixPosition(m).distanceTo(new T.Vector3(...sh.origin)));
 }
}
assert(axisError<2e-6&&originError<2e-6,{axisError,originError});
const before=d12Pose(4*Math.PI-1e-5),after=d12Pose(4*Math.PI+1e-5);
for(const sh of Object.values(D12_TIMING.shafts))assert(Math.abs(after[sh.node].rx-before[sh.node].rx)<.0001,'continuous shaft at 720 degrees');
const report={gearIdentities:gears.length,shaftAxes:16,enginePoseBindings:Object.keys(d12Pose(0)).length,axisError,originError,continuousAcross720:true,limits:'Exported transforms and identities; native gear surfaces verified separately. No physical or factory dimensional certification.'};
await fs.writeFile('outputs/timing-web-verification.json',JSON.stringify(report,null,2));console.log(report);

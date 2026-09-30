import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {Matrix4} from 'three';
const dir='outputs/front-assembly-20260930';
const browser=JSON.parse(await fs.readFile(dir+'/hinge-rubber-after/browser-evidence.json','utf8'));
const sweep=JSON.parse(await fs.readFile('work/front-door-sweep-rebased-20260930/front-door-sweep-verification.json','utf8'));
const convert=new Matrix4().set(1,0,0,0,0,0,1,0,0,-1,0,0,0,0,0,1),inverse=convert.clone().invert();
const poses=[];
for(const [key,degrees] of [['closed',0],['open',99]])for(const actual of browser[key].doors){
 const native=sweep.doors.find(d=>d.hinge===actual.name).states.find(s=>s.degrees===degrees);
 const expected=convert.clone().multiply(new Matrix4().set(...native.nativeMatrixWorld.flat())).multiply(inverse).elements;
 const error=Math.max(...actual.matrixWorld.map((v,i)=>Math.abs(v-expected[i])));
 assert.ok(error<2e-6,actual.name+' '+degrees+' native/runtime pose mismatch');
 poses.push({name:actual.name,degrees,maxMatrixDifference:error});
}
const parts=browser.closed.parts.map(before=>{const after=browser.open.parts.find(o=>o.name===before.name);assert.ok(after);const error=Math.max(...before.min.map((v,i)=>Math.abs(v-after.min[i])),...before.max.map((v,i)=>Math.abs(v-after.max[i])));assert.equal(error,0,before.name+' moved during actual door opening');return {name:before.name,maxBoundsDifference:error};});
assert.equal(sweep.failedPairs,0);assert.deepEqual(browser.errors,[]);assert.equal(browser.http,200);
const report={timeUTC:new Date().toISOString(),status:'PASS scoped native/runtime 0 and 99 degree pose registration and sampled front clearance',poses,stationaryFrontParts:parts,clearanceSampling:sweep.sampling,limits:'Only actual front components vs four doors, frame zero, 3 degree sampling. Continuous travel, original body/interior, suspension and full vehicle acceptance remain OPEN.'};
await fs.writeFile(dir+'/runtime-door-pose-after.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({status:report.status,parts:parts.length,maxMatrixDifference:Math.max(...poses.map(p=>p.maxMatrixDifference))}));

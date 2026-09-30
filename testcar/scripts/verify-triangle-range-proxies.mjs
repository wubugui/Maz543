import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {createTriangleRangeProxies,visibleTriangleRuns} from '../lib/triangleRangeProxies.ts';
import {ConservativeRasterBounds} from '../lib/conservativeRasterBounds.ts';
let seed=0x352181;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
const mul=(matrix,vector)=>[0,1,2,3].map(row=>{let sum=Math.fround(0);for(let i=0;i<4;i++)sum=Math.fround(sum+Math.fround(Math.fround(matrix.elements[i*4+row])*vector[i]));return sum;});
const camera=new T.PerspectiveCamera(45,1.5,.05,100),viewport=[0,0,900,600],bounds=new ConservativeRasterBounds();let checked=0,morphed=0;
for(let example=0;example<80;example++){
 const geometry=new T.BufferGeometry(),values=new Float32Array(900);for(let i=0;i<values.length;i++)values[i]=(random()-.5)*4;
 geometry.setAttribute('position',new T.BufferAttribute(values,3));geometry.setIndex(Array.from({length:900},()=>Math.floor(random()*300)));geometry.setDrawRange(3,891);
 const relative=example%2===0;geometry.morphTargetsRelative=relative;geometry.morphAttributes.position=[0,1].map(()=>new T.BufferAttribute(Float32Array.from(values,()=>random()-.5),3));
 const originalIndex=geometry.index.array.slice(),originalPositions=values.slice(),ranges=createTriangleRangeProxies(geometry,19);assert.ok(ranges);assert.equal(ranges.ranges[0].start,3);assert.equal(ranges.ranges.reduce((sum,r)=>sum+r.count,0),891);
 assert.equal(ranges.bytes,ranges.ranges.length*96*3);const weights=[random()*2-1,random()*2-1],baseWeight=Math.fround(relative?1:1-weights[0]-weights[1]);
 const mv=new T.Matrix4().compose(new T.Vector3(0,0,-15),new T.Quaternion().setFromEuler(new T.Euler(random()*4,random()*4,random()*4)),new T.Vector3(.5+random(),.5+random(),.5+random()));
 for(const range of ranges.ranges){
  const volume=bounds.volume(range.bounds,mv,camera.projectionMatrix,viewport,weights);assert.ok(volume);
  for(let element=range.start;element<range.start+range.count;element++){
   const vertex=originalIndex[element],p=[0,1,2].map(axis=>{let value=Math.fround(values[vertex*3+axis]*baseWeight);for(let m=0;m<2;m++)value=Math.fround(value+Math.fround(geometry.morphAttributes.position[m].array[vertex*3+axis]*Math.fround(weights[m])));return value;});
   const clip=mul(camera.projectionMatrix,mul(mv,[...p,1])),x=(clip[0]/clip[3]+1)*450,y=(clip[1]/clip[3]+1)*300,depth=(clip[2]/clip[3]+1)/2;
   assert.ok(x>=volume.left&&x<=volume.right&&y>=volume.bottom&&y<=volume.top&&depth>=volume.nearDepth);checked++;morphed++;
  }
 }
 let disposed=0,sourceDisposed=0;ranges.ranges.forEach(r=>r.bounds.addEventListener('dispose',()=>disposed++));geometry.addEventListener('dispose',()=>sourceDisposed++);const rangeCount=ranges.ranges.length;
 assert.deepEqual(geometry.index.array,originalIndex);assert.deepEqual(values,originalPositions);assert.ok(ranges.matches(geometry));geometry.index.needsUpdate=true;assert.equal(ranges.matches(geometry),false);
 ranges.dispose();ranges.dispose();assert.equal(disposed,rangeCount);assert.equal(sourceDisposed,0);geometry.dispose();
}
{
 const g=new T.BufferGeometry();const data=new Float32Array([99,0,0,0,99, 99,1,0,0,99, 99,0,1,0,99, 99,4,4,4,99, 99,5,4,4,99, 99,4,5,4,99]);g.setAttribute('position',new T.InterleavedBufferAttribute(new T.InterleavedBuffer(data,5),3,1));g.setDrawRange(0,6);
 const ranges=createTriangleRangeProxies(g,1);assert.ok(ranges);assert.equal(ranges.ranges.length,2);assert.equal(ranges.bytes,192);assert.equal(ranges.ranges[0].bounds.attributes.position.getX(7),1);assert.equal(ranges.ranges[1].bounds.attributes.position.getX(0),4);
 const old=ranges.matches(g);g.attributes.position.data.needsUpdate=true;assert.ok(old);assert.equal(ranges.matches(g),false);ranges.dispose();g.dispose();
}
{
 const g=new T.BoxGeometry();g.setDrawRange(0,36);assert.equal(createTriangleRangeProxies(g,1,2),null,'Budget overflow retains original geometry');g.clearGroups();g.addGroup(1,6,0);assert.equal(createTriangleRangeProxies(g),null,'Unaligned group preserves original primitive assembly');g.clearGroups();
 g.morphAttributes.position=[g.attributes.position.clone()];g.morphAttributes.position[0].needsUpdate=true;assert.equal(createTriangleRangeProxies(g),null);g.morphAttributes.position=[];
 g.index.setX(0,65535);assert.equal(createTriangleRangeProxies(g),null,'Out-of-range index rejects entire proxy set');g.index.setX(0,0);g.attributes.position.setX(0,NaN);assert.equal(createTriangleRangeProxies(g),null);g.dispose();
}
const ranges=[{start:0,count:6,zero:false},{start:6,count:6,zero:true},{start:12,count:6,zero:false},{start:18,count:6,zero:false}];
{
 const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(65536*3),3));g.setIndex(new T.BufferAttribute(new Uint16Array([0,1,65535]),1));assert.equal(createTriangleRangeProxies(g),null,'Fixed restart index changes assembly even when within attribute count');g.dispose();
}
assert.deepEqual(visibleTriangleRuns(0,24,ranges),[{start:0,count:6},{start:12,count:12}]);
assert.deepEqual(visibleTriangleRuns(3,18,ranges),[{start:3,count:3},{start:12,count:9}]);
assert.deepEqual(visibleTriangleRuns(6,6,ranges),[]);assert.equal(visibleTriangleRuns(1,6,ranges),null);assert.equal(visibleTriangleRuns(0,27,ranges),null);
assert.deepEqual(visibleTriangleRuns(0,24,ranges.map(r=>({...r,zero:false}))),[{start:0,count:24}]);
for(let sample=0;sample<100;sample++){
 const blocks=Array.from({length:20},(_,i)=>({start:i*15,count:15,zero:random()<.5}));const runs=visibleTriangleRuns(0,300,blocks);
 const expected=blocks.flatMap(r=>r.zero?[]:Array.from({length:r.count},(_,i)=>r.start+i));assert.deepEqual(runs.flatMap(r=>Array.from({length:r.count},(_,i)=>r.start+i)),expected,'Original surviving element order and triangle boundaries preserved');
}
const report={passed:true,checkedFloat32MorphVertexReferences:checked,morphed,sourceIndexAndPositionBytesUnchanged:true,nonIndexedInterleavedAndDrawRangesCovered:true,originalElementOrderPreserved:true,alignedGroupsRequired:true,budgetAndUnsupportedInputsFallBack:true,attributeVersionInvalidates:true,proxyResourcesDisposedExactlyOnce:true,sourceResourcesNeverDisposed:true,bytesPerUnmorphedRange:96,limits:'CPU extrema and highp-style transform coverage; not actual GPU occlusion, image equivalence or performance acceptance.'};
await fs.mkdir('outputs/triangle-range-occlusion',{recursive:true});await fs.writeFile('outputs/triangle-range-occlusion/range-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {ConservativeRasterBounds,rasterTiles} from '../lib/conservativeRasterBounds.ts';
const bounds=new ConservativeRasterBounds(),viewport=[7,11,1212,773];
let seed=0x12345678;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
const mul=(matrix,vector)=>[0,1,2,3].map(row=>{let sum=Math.fround(0);for(let i=0;i<4;i++)sum=Math.fround(sum+Math.fround(Math.fround(matrix.elements[i*4+row])*vector[i]));return sum;});
let covered=0,fallback=0;
for(let example=0;example<300;example++){
 const geometry=new T.BufferGeometry(),data=new Float32Array(900);for(let i=0;i<data.length;i++)data[i]=(random()-.5)*3;
 geometry.setAttribute('position',new T.BufferAttribute(data,3));
 const camera=new T.PerspectiveCamera(20+random()*80,viewport[2]/viewport[3],.05,1000);camera.position.z=10+random()*30;camera.updateMatrixWorld();
 const world=new T.Matrix4().compose(new T.Vector3((random()-.5)*8,(random()-.5)*8,(random()-.5)*5),new T.Quaternion().setFromEuler(new T.Euler(random()*6,random()*6,random()*6)),new T.Vector3(.01+random()*4,.01+random()*4,.01+random()*4));
 const mv=new T.Matrix4().multiplyMatrices(camera.matrixWorldInverse,world),rect=bounds.get(geometry,mv,camera.projectionMatrix,viewport),tight=bounds.volume(geometry,mv,camera.projectionMatrix,viewport);
 if(!rect){fallback++;geometry.dispose();continue;}
 for(let i=0;i<data.length;i+=3){
  const clip=mul(camera.projectionMatrix,mul(mv,[data[i],data[i+1],data[i+2],1]));
  assert.ok(clip[3]>0);const x=(clip[0]/clip[3]+1)*viewport[2]/2+viewport[0],y=(clip[1]/clip[3]+1)*viewport[3]/2+viewport[1];
  assert.ok(x>=rect.left&&x<=rect.right&&y>=rect.bottom&&y<=rect.top,'All float32 transformed vertices remain within outward rectangle');covered++;
  assert.ok((clip[2]/clip[3]+1)/2>=rect.nearDepth,'Query depth remains in front of every transformed vertex');
  assert.ok(tight);assert.ok(x>=tight.left&&x<=tight.right&&y>=tight.bottom&&y<=tight.top);assert.ok((clip[2]/clip[3]+1)/2>=tight.nearDepth,'Correlated bounds contain every float32 vertex');
 }
 geometry.dispose();
}
const geo=new T.BoxGeometry(),camera=new T.PerspectiveCamera(35,1,.05,100),mv=new T.Matrix4().makeTranslation(0,0,-10);
const first=bounds.get(geo,mv,camera.projectionMatrix,viewport);assert.ok(first);
geo.attributes.position.setX(0,100);geo.attributes.position.needsUpdate=true;const edited=bounds.get(geo,mv,camera.projectionMatrix,viewport);assert.ok(edited.right>first.right,'Actual attribute version refreshes bounds');
assert.equal(bounds.get(geo,new T.Matrix4(),camera.projectionMatrix,viewport),null,'Eye plane falls back');
geo.morphAttributes.position=[geo.attributes.position.clone()];assert.equal(bounds.get(geo,mv,camera.projectionMatrix,viewport),null,'Morph geometry falls back');delete geo.morphAttributes.position;
geo.attributes.position.setY(0,NaN);geo.attributes.position.needsUpdate=true;assert.equal(bounds.get(geo,mv,camera.projectionMatrix,viewport),null);
const full=rasterTiles(null,viewport);assert.equal(full.length,38*25);assert.ok(rasterTiles({left:70,right:71,bottom:80,top:81},viewport).length<full.length);assert.equal(rasterTiles(null,[0,0,100000,100000]).length,1,'Oversized target becomes one whole-screen dependency');
geo.dispose();bounds.clear();
let morphVertices=0;
for(const relative of [false,true])for(let sample=0;sample<100;sample++){
 const geometry=new T.BoxGeometry();geometry.morphTargetsRelative=relative;
 geometry.morphAttributes.position=[0,1].map(()=>{const attribute=geometry.attributes.position.clone();for(let i=0;i<attribute.array.length;i++)attribute.array[i]=(random()-.5)*2;return attribute;});
 const weights=[random()*3-1,random()*3-1],baseWeight=Math.fround(relative?1:1-weights.reduce((a,b)=>a+b,0));
 const rect=bounds.get(geometry,mv,camera.projectionMatrix,viewport,weights),tight=bounds.volume(geometry,mv,camera.projectionMatrix,viewport,weights);assert.ok(rect);assert.ok(tight);
 for(let vertex=0;vertex<geometry.attributes.position.count;vertex++){
  const transformed=[0,1,2].map(axis=>{let v=Math.fround(geometry.attributes.position.array[vertex*3+axis]*baseWeight);for(let target=0;target<2;target++)v=Math.fround(v+Math.fround(geometry.morphAttributes.position[target].array[vertex*3+axis]*Math.fround(weights[target])));return v;});
  const clip=mul(camera.projectionMatrix,mul(mv,[...transformed,1])),x=(clip[0]/clip[3]+1)*viewport[2]/2+viewport[0],y=(clip[1]/clip[3]+1)*viewport[3]/2+viewport[1];
  assert.ok(x>=rect.left&&x<=rect.right&&y>=rect.bottom&&y<=rect.top);assert.ok((clip[2]/clip[3]+1)/2>=rect.nearDepth);morphVertices++;
  assert.ok(x>=tight.left&&x<=tight.right&&y>=tight.bottom&&y<=tight.top);assert.ok((clip[2]/clip[3]+1)/2>=tight.nearDepth);
 }
 geometry.morphAttributes.position[0].needsUpdate=true;assert.equal(bounds.get(geometry,mv,camera.projectionMatrix,viewport,weights),null,'Changed morph source falls back because r183 texture is not refreshed');geometry.dispose();
}
const extended=new T.BoxGeometry(1,1,2),loose=bounds.get(extended,mv,camera.projectionMatrix,viewport),tight=bounds.volume(extended,mv,camera.projectionMatrix,viewport);assert.ok(tight.nearDepth>loose.nearDepth+.05,'Correlated z/w avoids placing the proxy far in front of the component');extended.dispose();
const result={passed:true,coveredFloat32Vertices:covered,coveredMorphVertices:morphVertices,frontDepthBoundVerified:true,correlatedBoundsVerified:true,conservativeFallbackCases:fallback,attributeChangesRefresh:true,unknownAndNearPlaneFallBack:true,modifiedMorphSourceFallsBack:true,limits:'CPU highp-style sequential float32 transform coverage. Not GPU compiler or raster coverage proof; actual full-frame pairs required.'};
await fs.writeFile((process.argv[2]??'outputs/occlusion-tile-reuse')+'/bounds-tests.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));

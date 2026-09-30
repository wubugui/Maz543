import assert from 'node:assert/strict';
import {Matrix4,Vector3,Quaternion} from 'three';
export function verifyLocalTransform(before,after,declaredDeltaX){
 for(const k of ['rotation','scale','matrix'])assert.deepEqual(after[k],before[k],after.name+' transform '+k);
 if(declaredDeltaX===undefined){assert.deepEqual(after.translation,before.translation,after.name+' transform translation');return;}
 assert.ok(Number.isFinite(declaredDeltaX)&&Math.abs(declaredDeltaX)<=.281,'Unexpected declared hinge delta');
 const a=before.translation??[0,0,0],b=after.translation??[0,0,0];
 for(let i=0;i<3;i++)assert.ok(Math.abs((b[i]-a[i])-(i===0?declaredDeltaX:0))<2e-6,after.name+' incorrect declared hinge rebase');
}
export function worldMatrices(j){
 const parents=new Map(),cache=new Map();for(let i=0;i<j.nodes.length;i++)for(const child of j.nodes[i].children??[])parents.set(child,i);
 function world(i){if(cache.has(i))return cache.get(i);const n=j.nodes[i],m=n.matrix?new Matrix4().fromArray(n.matrix):new Matrix4().compose(new Vector3().fromArray(n.translation??[0,0,0]),new Quaternion().fromArray(n.rotation??[0,0,0,1]),new Vector3().fromArray(n.scale??[1,1,1]));if(parents.has(i))m.premultiply(world(parents.get(i)));cache.set(i,m);return m;}
 return new Map(j.nodes.map((n,i)=>[n.name,world(i).elements.slice()]));
}
export function verifyClosedWorldGeometry(before,after){assert.ok(before&&after);assert.ok(Math.max(...before.map((x,i)=>Math.abs(x-after[i])))<2e-6,'Unapproved movement of closed world geometry');}

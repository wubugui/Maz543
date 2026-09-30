import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {WebGLRenderList} from 'three/src/renderers/webgl/WebGLRenderLists.js';
import {createContextSourceOrder} from '../lib/contextSourceOrder.ts';

function sample(reverse,mode){
 const scene=new T.Scene(),materials={},objects={};
 for(const name of reverse?['b','a']:['a','b'])materials[name]=new T.MeshPhysicalMaterial({transparent:mode==='transparent',transmission:mode==='transmissive'?1:0});
 for(const name of reverse?['b2','b1','a2','a1']:['a1','a2','b1','b2']){const object=new T.Mesh(new T.BufferGeometry(),materials[name[0]]);object.name=name;objects[name]=object;}
 for(const name of ['a1','a2','b1','b2'])scene.add(objects[name]);
 const sorter=createContextSourceOrder(scene),list=new WebGLRenderList();
 for(const object of [...scene.children].reverse())list.push(object,object.geometry,object.material,0,1,null);
 list.sort();const stock=list[mode].map(item=>item.object.name);
 list.sort(sorter.opaque,sorter.transparent);const canonical=list[mode].map(item=>item.object.name);
 const a=list[mode][0],b=list[mode][1];
 assert.ok(sorter.opaque({...a,groupOrder:0},{...b,groupOrder:1})<0);
 assert.ok(sorter.opaque({...a,renderOrder:0},{...b,renderOrder:1})<0);
 assert.ok(sorter.opaque({...a,z:1+Number.EPSILON},{...a,z:1})>0,'No depth epsilon');
 assert.ok(sorter.transparent({...a,z:1+Number.EPSILON},{...a,z:1})<0,'Transparent depth remains back-to-front');
 assert.ok(sorter.opaque({...a,materialVariant:0},{...a,materialVariant:1})<0);
 for(const object of scene.children)object.geometry.dispose();Object.values(materials).forEach(material=>material.dispose());
 return {stock,canonical};
}
const modes={};
for(const mode of ['opaque','transparent','transmissive']){
 const forward=sample(false,mode),reverse=sample(true,mode);
 assert.notDeepEqual(forward.stock,reverse.stock,`Actual r183 ${mode} stock allocation order differs`);
 assert.deepEqual(forward.canonical,reverse.canonical);assert.deepEqual(forward.canonical,['a1','a2','b1','b2']);
 modes[mode]={forward,reverse};
}
const report={passed:true,modes,exactDepthPreserved:true,groupRenderVariantPrecedencePreserved:true,
 limits:'Actual installed r183 render-list sorting under controlled allocation permutations. Audit-only comparator; does not establish identical pixels, calibrated geometry, physical behavior or performance.'};
await fs.writeFile('outputs/context-draw-order/sort-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));

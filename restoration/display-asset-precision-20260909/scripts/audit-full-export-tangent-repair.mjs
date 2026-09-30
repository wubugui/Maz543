import fs from 'node:fs/promises';
import * as T from 'three';
import {prepareExportTangents} from '../lib/exportTangents.ts';
const bytes=await fs.readFile('outputs/render-worker-evidence/whole-current-pose.glb'),jsonLength=bytes.readUInt32LE(12),json=JSON.parse(bytes.subarray(20,20+jsonLength).toString()),binaryOffset=28+jsonLength;
const cache=new Map(),sizes={SCALAR:1,VEC2:2,VEC3:3,VEC4:4},arrays={5121:Uint8Array,5123:Uint16Array,5125:Uint32Array,5126:Float32Array};
function attribute(id){if(cache.has(id))return cache.get(id);const a=json.accessors[id],view=json.bufferViews[a.bufferView],Ctor=arrays[a.componentType],size=sizes[a.type],offset=bytes.byteOffset+binaryOffset+(view.byteOffset??0)+(a.byteOffset??0);if(view.byteStride&&view.byteStride!==size*Ctor.BYTES_PER_ELEMENT)throw new Error('Unexpected interleaved export');const attr=new T.BufferAttribute(new Ctor(bytes.buffer,offset,a.count*size),size,a.normalized??false);cache.set(id,attr);return attr;}
const rows=[];let candidates=0,repaired=0,unresolved=0;
for(let i=0;i<json.meshes.length;i++)for(const primitive of json.meshes[i].primitives){
 if(primitive.attributes.TANGENT===undefined)continue;const geometry=new T.BufferGeometry();
 for(const [name,semantic] of [['position','POSITION'],['normal','NORMAL'],['tangent','TANGENT'],['skinIndex','JOINTS_0'],['skinWeight','WEIGHTS_0']])if(primitive.attributes[semantic]!==undefined)geometry.setAttribute(name,attribute(primitive.attributes[semantic]));
 if(primitive.indices!==undefined)geometry.setIndex(attribute(primitive.indices));geometry.morphTargetsRelative=true;
 if(primitive.targets?.some(target=>target.POSITION!==undefined))geometry.morphAttributes.position=primitive.targets.map(target=>attribute(target.POSITION));
 const result=prepareExportTangents(geometry);if(result.audit.candidates){const samples=[];
  if(result.audit.unresolved){const t=result.geometry.attributes.tangent,p=geometry.attributes.position,ix=geometry.index;for(let v=0;v<t.count&&samples.length<4;v++)if(Math.hypot(t.getX(v),t.getY(v),t.getZ(v))<.01){const triangles=[];for(let k=0;k<(ix?.count??p.count);k+=3){const ids=[ix?ix.getX(k):k,ix?ix.getX(k+1):k+1,ix?ix.getX(k+2):k+2];if(!ids.includes(v))continue;const a=new T.Vector3().fromBufferAttribute(p,ids[0]),b=new T.Vector3().fromBufferAttribute(p,ids[1]),c=new T.Vector3().fromBufferAttribute(p,ids[2]);triangles.push({ids,points:[a.toArray(),b.toArray(),c.toArray()],cross:b.sub(a).cross(c.sub(a)).toArray()});}samples.push({vertex:v,triangles});}}
  rows.push({mesh:i,names:json.nodes.filter(node=>node.mesh===i).map(node=>node.name),...result.audit,morphTargets:geometry.morphAttributes.position?.length??0,samples});candidates+=result.audit.candidates;repaired+=result.audit.repaired;unresolved+=result.audit.unresolved;}
 result.geometry.dispose();geometry.dispose();
}
const report={candidates,repaired,unresolved,rows,sourceFileChanged:false,limits:'Evaluates the guarded export repair against the actual previous browser export. Separate browser export verifies integration.'};await fs.writeFile('outputs/tangent-audit/full-repair-audit.json',JSON.stringify(report,null,2));console.log(JSON.stringify({candidates,repaired,unresolved,affectedMeshes:rows.length,unresolvedMeshes:rows.filter(row=>row.unresolved).map(({samples,...row})=>row)},null,2));

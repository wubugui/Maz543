import * as T from 'three';

type Attribute=T.BufferAttribute|T.InterleavedBufferAttribute;
export type TriangleRangeProxy={start:number;count:number;bounds:T.BufferGeometry};
const equal=(a:unknown[],b:unknown[])=>a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));
const attributeKey=(a:Attribute)=>[a,a.array,a.array.buffer,a.count,a.itemSize,a.normalized,...(a instanceof T.InterleavedBufferAttribute?[a.data,a.data.version,a.data.stride,a.offset]:[a.version,a.gpuType])];
function signature(g:T.BufferGeometry){
 const position=g.attributes.position;if(!position)return null;
 const out:unknown[]=[g,g.drawRange.start,g.drawRange.count,g.morphTargetsRelative,...attributeKey(position),g.index,...(g.index?attributeKey(g.index):[])];
 out.push(g.groups.length);for(const group of g.groups)out.push(group.start,group.count,group.materialIndex);
 const morphs=g.morphAttributes.position??[];out.push(morphs.length);for(const a of morphs)out.push(...attributeKey(a));return out;
}
const supported=(a:Attribute)=>a.array instanceof Float32Array&&!a.normalized&&a.itemSize===3&&Number.isInteger(a.count)&&a.count>0&&(a instanceof T.InterleavedBufferAttribute||a.gpuType===T.FloatType);

/** CPU-only extrema for contiguous original triangle ranges. The eight corners
 * encode exact Float32 minima/maxima of the original referenced attributes.
 * They are never drawn, exported, attached to the scene, or uploaded to WebGL.
 * ConservativeRasterBounds applies the existing morph/transform error bound.
 * No source vertex/index/material/triangle ordering is changed. */
export function createTriangleRangeProxies(geometry:T.BufferGeometry,trianglesPerRange=2048,maxRanges=4096){
 if(!Number.isInteger(trianglesPerRange)||trianglesPerRange<1||!Number.isInteger(maxRanges)||maxRanges<1)return null;
 const position=geometry.attributes.position,index=geometry.index,morphs=geometry.morphAttributes.position??[],attributes=[position,...morphs];
 if(!position||!attributes.every(supported)||morphs.some(a=>a.count!==position.count||(a instanceof T.InterleavedBufferAttribute?a.data.version:a.version)!==0)||morphs.length>64)return null;
 if(index&&(!(index.array instanceof Uint16Array||index.array instanceof Uint32Array)||index.itemSize!==1||index.normalized))return null;
 const length=index?.count??position.count,start=Math.max(0,geometry.drawRange.start),end=Math.min(length,geometry.drawRange.start+geometry.drawRange.count),count=end-start;
 if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||count<=0||count%3!==0||Math.ceil(count/(trianglesPerRange*3))>maxRanges)return null;
 // A group can start a new TRIANGLES assembly at its own first element. Only
 // common triangle alignment permits clipping an existing range at its ends.
 for(const group of geometry.groups){const first=Math.max(start,group.start),last=Math.min(end,group.start+group.count);if(last>first&&(!Number.isSafeInteger(first)||!Number.isSafeInteger(last)||(first-start)%3!==0||(last-first)%3!==0))return null;}
 const key=signature(geometry);if(!key)return null;
 const ranges:TriangleRangeProxy[]=[];let bytes=0,disposed=false;
 const dispose=()=>{if(disposed)return;disposed=true;for(const range of ranges)range.bounds.dispose();ranges.length=0;};
 const corners=(attribute:Attribute,first:number,last:number)=>{
  const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity],stride=attribute instanceof T.InterleavedBufferAttribute?attribute.data.stride:3,offset=attribute instanceof T.InterleavedBufferAttribute?attribute.offset:0;
  for(let element=first;element<last;element++){
   const vertex=index?index.array[element]:element;
   // r183 utils.arrayNeedsUint32 also reserves the fixed restart index. A
   // restart changes TRIANGLES assembly, so raw modulo-three splits are unsafe.
   const restart=index?(index.array instanceof Uint16Array?65535:4294967295):-1;
   if(!Number.isInteger(vertex)||vertex<0||vertex>=position.count||vertex===restart)return null;
   for(let axis=0;axis<3;axis++){const value=attribute.array[vertex*stride+offset+axis];if(!Number.isFinite(value))return null;lo[axis]=Math.min(lo[axis],value);hi[axis]=Math.max(hi[axis],value);}
  }
  const result=new Float32Array(24);for(let corner=0;corner<8;corner++)for(let axis=0;axis<3;axis++)result[corner*3+axis]=(corner&(1<<axis))?hi[axis]:lo[axis];return result;
 };
 for(let first=start;first<end;first+=trianglesPerRange*3){
  const last=Math.min(end,first+trianglesPerRange*3),values=attributes.map(a=>corners(a,first,last));
  if(values.some(v=>v===null)){dispose();return null;}
  const bounds=new T.BufferGeometry();bounds.setAttribute('position',new T.BufferAttribute(values[0]!,3));bounds.morphTargetsRelative=geometry.morphTargetsRelative;
  if(morphs.length)bounds.morphAttributes.position=values.slice(1).map(v=>new T.BufferAttribute(v!,3));
  ranges.push({start:first,count:last-first,bounds});bytes+=values.reduce((sum,v)=>sum+v!.byteLength,0);
 }
 return {ranges,bytes,start,count,matches:(current:T.BufferGeometry)=>!disposed&&current===geometry&&equal(key,signature(current)??[]),dispose};
}

/** Retain original triangle order and coalesce adjacent visible ranges. Null
 * rejects an unaligned/uncovered call instead of guessing its geometry span. */
export function visibleTriangleRuns(start:number,count:number,ranges:readonly {start:number;count:number;zero:boolean}[]){
 if(!Number.isSafeInteger(start)||!Number.isSafeInteger(count)||start<0||count<=0||count%3!==0)return null;
 const end=start+count;if(!Number.isSafeInteger(end))return null;
 const runs:{start:number;count:number}[]=[];let cursor=start;
 for(const range of ranges){
  const first=Math.max(start,range.start),last=Math.min(end,range.start+range.count);if(last<=first)continue;
  if(first!==cursor||(first-start)%3!==0||(last-first)%3!==0)return null;
  if(!range.zero){const previous=runs.at(-1);if(previous&&previous.start+previous.count===first)previous.count+=last-first;else runs.push({start:first,count:last-first});}
  cursor=last;
 }
 return cursor===end?runs:null;
}

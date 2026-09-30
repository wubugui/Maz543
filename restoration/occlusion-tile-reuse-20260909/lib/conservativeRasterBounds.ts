import * as T from 'three';

type Range=readonly [number,number];
type Bounds=readonly [Range,Range,Range,Range];
export type RasterRect={left:number;bottom:number;right:number;top:number};
const MIN_NORMAL=2**-126,MAX_FLOAT=3.4028234663852886e38,U=2**-23;
const same=(a:unknown[],b:unknown[])=>a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));

// GLSL ES 3.00 section 4.5.1: highp +/-/* correctly rounded; FMA may be
// fused; subnormal inputs/results may flush to zero. A 4-term dot has at
// most 7 rounded operations. 16 U * sum(abs terms) also covers reassociation
// and JS accumulation error. Overflow/unknown input returns full viewport.
function dot(matrix:readonly number[],row:number,box:Bounds):Range|null{
 let lo=0,hi=0,magnitude=0;
 for(let i=0;i<4;i++){
  const v=Math.fround(matrix[i*4+row]);if(!Number.isFinite(v))return null;
  const a=Math.min(v,Math.abs(v)<MIN_NORMAL?0:v),b=Math.max(v,Math.abs(v)<MIN_NORMAL?0:v);
  const products=[a*box[i][0],a*box[i][1],b*box[i][0],b*box[i][1]];
  const low=Math.min(...products),high=Math.max(...products);lo+=low;hi+=high;magnitude+=Math.max(Math.abs(low),Math.abs(high));
 }
 if(!Number.isFinite(magnitude)||magnitude>MAX_FLOAT/64)return null;
 const error=16*U*magnitude+16*MIN_NORMAL;return [lo-error,hi+error];
}
function transform(matrix:readonly number[],box:Bounds):Bounds|null{
 const result=[0,1,2,3].map(row=>dot(matrix,row,box));return result.every(v=>v!==null)?result as unknown as Bounds:null;
}

/** Conservative influence bounds only; never frustum-culls a mesh. Bounds
 * include every position, not just current drawRange/index, and don't trust
 * authored boundingBox. Only plain Float32 positions and stock highp transforms
 * are supported. null means every screen tile is a dependency. */
export class ConservativeRasterBounds{
 private local=new WeakMap<T.BufferAttribute|T.InterleavedBufferAttribute,{key:unknown[];box:Bounds|null}>();
 clear(){this.local=new WeakMap();}
 private attributeBounds(position:T.BufferAttribute|T.InterleavedBufferAttribute):Bounds|null{
  if(!position||!(position.array instanceof Float32Array)||position.normalized||position.itemSize!==3)return null;
  const interleaved=position instanceof T.InterleavedBufferAttribute;
  if(!interleaved&&position.gpuType!==T.FloatType)return null;
  const key=[position,position.array,position.array.buffer,position.count,position.itemSize,interleaved?position.data.version:position.version,interleaved?position.data.stride:3,interleaved?position.offset:0];
  const saved=this.local.get(position);if(saved&&same(key,saved.key))return saved.box;
  const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];let valid=Number.isInteger(position.count)&&position.count>0;
  for(let i=0;i<position.count&&valid;i++)for(let axis=0;axis<3;axis++){
   const value=position.array[i*(interleaved?position.data.stride:3)+(interleaved?position.offset:0)+axis];
   if(!Number.isFinite(value)){valid=false;break;}
   low[axis]=Math.min(low[axis],value,Math.abs(value)<MIN_NORMAL?0:value);high[axis]=Math.max(high[axis],value,Math.abs(value)<MIN_NORMAL?0:value);
  }
  const box:Bounds|null=valid?[[low[0],high[0]],[low[1],high[1]],[low[2],high[2]],[1,1]]:null;
  this.local.set(position,{key,box});return box;
 }
 private positions(geometry:T.BufferGeometry,influences:readonly number[]|undefined):Bounds|null{
  const base=this.attributeBounds(geometry.attributes.position);if(!base)return null;
  const morphs=geometry.morphAttributes.position;if(!morphs?.length)return base;
  if(!influences||influences.length!==morphs.length||morphs.length>64||!influences.every(Number.isFinite))return null;
  // r183 uploads morphs once to a Float32 texture and does not refresh it for
  // attribute.version changes. Only immutable original morph attributes are
  // supported; modified sources get whole-viewport dependencies instead.
  const ranges:Bounds[]=[base];
  for(const attribute of morphs){
   const version=attribute instanceof T.InterleavedBufferAttribute?attribute.data.version:attribute.version;
   if(version!==0||attribute.count!==geometry.attributes.position.count)return null;
   const range=this.attributeBounds(attribute);if(!range)return null;ranges.push(range);
  }
  let sum=0;for(const influence of influences)sum+=influence;
  const weights=[geometry.morphTargetsRelative?1:1-sum,...influences].map(Math.fround);
  if(!weights.every(Number.isFinite))return null;
  const result:Range[]=[];
  for(let axis=0;axis<3;axis++){
   let lo=0,hi=0,magnitude=0;
   for(let i=0;i<weights.length;i++){
    const weight=weights[i],a=Math.min(weight,Math.abs(weight)<MIN_NORMAL?0:weight),b=Math.max(weight,Math.abs(weight)<MIN_NORMAL?0:weight);
    const values=[a*ranges[i][axis][0],a*ranges[i][axis][1],b*ranges[i][axis][0],b*ranges[i][axis][1]];
    const low=Math.min(...values),high=Math.max(...values);lo+=low;hi+=high;magnitude+=Math.max(Math.abs(low),Math.abs(high));
   }
   if(!Number.isFinite(magnitude)||magnitude>MAX_FLOAT/1024)return null;
   const error=(4*weights.length+16)*(U*magnitude+MIN_NORMAL);result.push([lo-error,hi+error]);
  }
  return [result[0],result[1],result[2],[1,1]];
 }
 get(geometry:T.BufferGeometry,modelView:T.Matrix4,projection:T.Matrix4,viewport:readonly number[],influences?:readonly number[]):RasterRect|null{
  if(viewport.length!==4||!viewport.every(Number.isFinite)||viewport[2]<=0||viewport[3]<=0||viewport.some(v=>Math.abs(v)>65536))return null;
  const box=this.positions(geometry,influences);if(!box)return null;
  const view=transform(modelView.elements,box);if(!view)return null;
  const clip=transform(projection.elements,view);if(!clip)return null;
  // Near/eye-plane uncertainty deliberately gets the full viewport. No
  // projective division across a possibly zero/negative homogeneous w.
  if(clip[3][0]<=1e-3||clip[2][0]<-clip[3][0])return null;
  const screen=(range:Range,axis:0|1):Range|null=>{
   const ratios=[range[0]/clip[3][0],range[0]/clip[3][1],range[1]/clip[3][0],range[1]/clip[3][1]];
   const low=Math.min(...ratios),high=Math.max(...ratios),magnitude=Math.max(Math.abs(low),Math.abs(high));
   if(!Number.isFinite(magnitude)||magnitude>1e6)return null;
   // Outward interval for division + viewport arithmetic, then two whole
   // pixels for fixed-point snapping and coverage samples (all MSAA modes).
   const error=16*U*Math.max(1,magnitude),extent=viewport[axis+2],origin=viewport[axis];
   return [(low-error+1)*extent/2+origin-2,(high+error+1)*extent/2+origin+2];
  };
  const x=screen(clip[0],0),y=screen(clip[1],1);if(!x||!y)return null;
  return {left:x[0],bottom:y[0],right:x[1],top:y[1]};
 }
}

/** Tile rectangles are only influence sets, not draw scissor rectangles. */
export function rasterTiles(rect:RasterRect|null,viewport:readonly number[],size=32):number[]{
 const cols=Math.ceil(viewport[2]/size),rows=Math.ceil(viewport[3]/size);
 if(cols<=0||rows<=0||cols*rows>8192)return [0];
 if(!rect)return Array.from({length:cols*rows},(_,i)=>i);
 const x0=Math.max(0,Math.min(cols-1,Math.floor((rect.left-viewport[0])/size))),x1=Math.max(0,Math.min(cols-1,Math.floor((rect.right-viewport[0])/size)));
 const y0=Math.max(0,Math.min(rows-1,Math.floor((rect.bottom-viewport[1])/size))),y1=Math.max(0,Math.min(rows-1,Math.floor((rect.top-viewport[1])/size)));
 // Clamp offscreen objects to a border tile instead of inferring zero coverage.
 const tiles:number[]=[];for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++)tiles.push(y*cols+x);return tiles;
}

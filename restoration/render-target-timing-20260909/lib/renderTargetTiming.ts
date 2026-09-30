import * as T from 'three';

/** One deliberately intrusive command/state round-trip diagnostic frame.
 * Chromium implements WebGL finish() as Flush(), so it alone is NOT a GPU
 * completion barrier. Include state-read stalls and retain every original
 * draw/order; these intervals are wall time, not proven GPU durations. */
export function measureRenderTargets(renderer:T.WebGLRenderer,scene:T.Scene,camera:T.Camera,draw:()=>void,labels:ReadonlyMap<T.Material,string>=new Map()){
 const gl=renderer.getContext(),originalTarget=renderer.setRenderTarget,originalDraw=renderer.renderBufferDirect;
 type Target=Parameters<T.WebGLRenderer['setRenderTarget']>[0];
 const ids=new Map<NonNullable<Target>,number>(),segments:Record<string,unknown>[]=[];
 let target:Target=renderer.getRenderTarget(),cube=renderer.getActiveCubeFace(),mip=renderer.getActiveMipmapLevel(),draws=0,triangles=0;
 let kinds=new Map<string,number>(),materials=new Map<string,number>(),start=0;
 const targetId=(value:Target)=>{if(!value)return 'screen';if(!ids.has(value))ids.set(value,ids.size+1);return `target-${ids.get(value)}`;};
 const drainStart=performance.now();gl.finish();gl.getParameter(gl.SAMPLES);gl.getParameter(gl.DEPTH_BITS);const captureStart=performance.now(),initialDrainMs=captureStart-drainStart;start=captureStart;
 const close=(reason:string)=>{
  gl.finish();const finishReturned=performance.now();
  const endFramebufferSamples=gl.getParameter(gl.SAMPLES),endFramebufferDepthBits=gl.getParameter(gl.DEPTH_BITS),end=performance.now();
  const texture=Array.isArray(target?.texture)?target.texture[0]:target?.texture;
  segments.push({target:targetId(target),width:target?.width??gl.drawingBufferWidth,height:target?.height??gl.drawingBufferHeight,cube,mip,requestedSamples:target?.samples??null,endFramebufferSamples,endFramebufferDepthBits,textureType:texture?.type??null,textureFormat:texture?.format??null,generateMipmaps:texture?.generateMipmaps??false,draws,triangles,kinds:Object.fromEntries(kinds),materials:Object.fromEntries(materials),submitAndFinishReturnMs:finishReturned-start,stateReadWaitMs:end-finishReturned,synchronizedMs:end-start,reason});
 };
 renderer.setRenderTarget=(...args)=>{
  const [next,nextCube=0,nextMip=0]=args;
  if(next===target&&nextCube===cube&&nextMip===mip)return originalTarget.apply(renderer,args);
  close('target-change');target=next;cube=nextCube;mip=nextMip;draws=0;triangles=0;kinds=new Map();materials=new Map();start=performance.now();
  return originalTarget.apply(renderer,args);
 };
 renderer.renderBufferDirect=(...args)=>{
  const [passCamera,passScene,geometry,material,object,group]=args;
  const kind=passCamera!==camera?(material instanceof T.MeshDepthMaterial||material instanceof T.MeshDistanceMaterial?'shadow-depth-camera':'other-camera'):passScene!==scene?'other-scene':scene.overrideMaterial?'vehicle-override':'vehicle-color';
  const label=labels.get(material)||material.name||material.type;
  kinds.set(kind,(kinds.get(kind)??0)+1);materials.set(label,(materials.get(label)??0)+1);draws++;
  if((object as T.Mesh).isMesh){const count=geometry.index?.count??geometry.attributes.position?.count??0,first=Math.max(geometry.drawRange.start,group?.start??0),last=Math.min(count,geometry.drawRange.start+geometry.drawRange.count,group?group.start+group.count:Infinity);triangles+=Math.max(0,Math.floor((last-first)/3));}
  return originalDraw.apply(renderer,args);
 };
 try{draw();close('frame-end');}
 finally{renderer.setRenderTarget=originalTarget;renderer.renderBufferDirect=originalDraw;}
 const captureMs=performance.now()-captureStart,attributedMs=segments.reduce((sum,row)=>sum+Number(row.synchronizedMs),0);
 return {kind:'synchronized-render-target-wall-time',initialStateRoundTripMs:initialDrainMs,captureMs,attributedMs,unattributedMs:captureMs-attributedMs,gpuCompletionProven:false,segments,glError:gl.getError(),limits:'Finite intrusive diagnostic only. Chromium WebGL finish() is a flush; synchronous state reads measure command/driver round trips but do not prove GPU completion. Initial state round trip precedes capture. Intervals include submission, state-read waits and target resolve/mipmap command work. All original draws/quality/mechanics retained; not hardware GPU durations or sustained FPS.'};
}

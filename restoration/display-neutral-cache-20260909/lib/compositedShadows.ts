import type {WebGLRenderer} from 'three';

/** The first scene pass refreshes shadows for the current mechanical pose.
 * Later normal/depth passes share that exact pose and must reuse those maps.
 * Request a fresh map on EVERY frame, so moving doors/gears keep live shadows.
 */
export function renderWithOneShadowUpdate(renderer:WebGLRenderer,render:()=>void){
  const previous=renderer.shadowMap.autoUpdate;
  renderer.shadowMap.autoUpdate=false;
  renderer.shadowMap.needsUpdate=true;
  try{render();}finally{renderer.shadowMap.autoUpdate=previous;}
}

/** Development-only paired actual-frame audit. Both draws use identical scene
 * transforms, materials, camera and post-processing. Pixel reads are immediate
 * in the same animation callback; no preserved drawing buffer is required.
 */
export function auditCompositedShadows(renderer:WebGLRenderer,render:()=>void){
  const previous=renderer.shadowMap.autoUpdate;
  try{return auditRenderPair(renderer,()=>renderWithOneShadowUpdate(renderer,render),()=>{renderer.shadowMap.autoUpdate=true;render();});}
  finally{renderer.shadowMap.autoUpdate=previous;}
}

export function auditRenderPair(renderer:WebGLRenderer,candidate:()=>void,baselineRender:()=>void){
  const gl=renderer.getContext(),width=gl.drawingBufferWidth,height=gl.drawingBufferHeight;
  const before=new Uint8Array(width*height*4),after=new Uint8Array(before.length);
  // Candidate goes first, so a freshly generated baseline map cannot conceal
  // a missing per-frame update in the candidate when a mechanism has moved.
  renderer.info.reset();
  const optimizedStart=performance.now();candidate();
  gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,after);
  const optimized={calls:renderer.info.render.calls,triangles:renderer.info.render.triangles,synchronizedMs:performance.now()-optimizedStart};
  const optimizedReadbackError=gl.getError();
  renderer.info.reset();
  const baselineStart=performance.now();
  baselineRender();
  gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,before);
  const baseline={calls:renderer.info.render.calls,triangles:renderer.info.render.triangles,synchronizedMs:performance.now()-baselineStart};
  const baselineReadbackError=gl.getError();
  let differentPixels=0,maxChannelDifference=0,squaredDifference=0;
  for(let i=0;i<before.length;i+=4){let changed=false;for(let c=0;c<4;c++){const d=Math.abs(before[i+c]-after[i+c]);changed ||= d!==0;maxChannelDifference=Math.max(maxChannelDifference,d);squaredDifference+=d*d;}if(changed)differentPixels++;}
  return {width,height,order:'optimized-then-baseline',baseline,optimized,optimizedReadbackError,baselineReadbackError,differentPixels,maxChannelDifference,rmsChannelDifference:Math.sqrt(squaredDifference/before.length),
    identicalPixels:differentPixels===0,limits:'Paired frame, not steady-state FPS. Synchronized times include readback and compilation/cache effects. Same complete scene and current mechanical pose.'};
}

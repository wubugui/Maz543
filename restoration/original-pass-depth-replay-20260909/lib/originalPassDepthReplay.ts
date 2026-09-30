import * as T from 'three';
import {opaqueDepthMaterial} from './staticOccluderScene';

type DrawArgs=Parameters<T.WebGLRenderer['renderBufferDirect']>;
type Program={program:WebGLProgram;id:number};
type Row={args:DrawArgs;program:Program;linked:WebGLProgram;world:number[];modelView:number[];normal:number[];morph:number[];side:T.Side;version:number;triangles:number};
type Pass={source:T.WebGLRenderTarget;rows:Row[];samples:number;depthBits:number;viewport:number[];override:boolean;done:boolean};
const same=(a:readonly unknown[],b:readonly unknown[])=>a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));

/** Finite DEV proof only. Duplicate original eligible draws while the original
 * scene's render state is still active. No product draw is skipped. */
export function replayOriginalPassDepth(renderer:T.WebGLRenderer,scene:T.Scene,camera:T.Camera,eligible:ReadonlySet<T.Mesh>,draw:()=>void,consume?:(target:T.WebGLRenderTarget,info:{samples:number;depthBits:number;viewport:number[];normalOverride:boolean},direct:(...args:DrawArgs)=>void)=>void){
 const gl=renderer.getContext(),originalDraw=renderer.renderBufferDirect,originalAfter=scene.onAfterRender;
 const passes=new Map<T.WebGLRenderTarget,Pass>(),owned:T.WebGLRenderTarget[]=[];
 const disposedDepth=new Set<T.DepthTexture>();
 const report={kind:'original-linked-program-depth-replay',threeRevision:T.REVISION,eligibleMeshes:eligible.size,recordedDraws:0,replayedDraws:0,replayedTriangles:0,programMatches:0,programMismatches:0,matrixMismatches:0,errors:[] as string[],passes:[] as Record<string,unknown>[],sourceCallsUnchanged:true,limits:'Finite depth-snapshot proof only; original product draws retained. Captured linked handle, source geometry/material, world/model-view/normal matrices and morph weights checked per replay. Not cross-frame validity, actual culling or performance acceptance.'};
 let custom=false;scene.traverseVisible(object=>{if(object.onBeforeRender!==T.Object3D.prototype.onBeforeRender||object.onAfterRender!==T.Object3D.prototype.onAfterRender)custom=true;if(object instanceof T.Mesh){if(object.onBeforeShadow!==T.Object3D.prototype.onBeforeShadow||object.onAfterShadow!==T.Object3D.prototype.onAfterShadow)custom=true;for(const m of Array.isArray(object.material)?object.material:[object.material])if(m.onBeforeRender!==T.Material.prototype.onBeforeRender||m.onBeforeCompile!==T.Material.prototype.onBeforeCompile||m.customProgramCacheKey!==T.Material.prototype.customProgramCacheKey)custom=true;}});
 if(T.REVISION!=='183'||custom||originalAfter!==T.Object3D.prototype.onAfterRender||renderer.xr.enabled||renderer.capabilities.logarithmicDepthBuffer||renderer.capabilities.reversedDepthBuffer||renderer.clippingPlanes.length||gl.isContextLost()){report.errors.push('Unsupported Three revision, callbacks, renderer or context');draw();return report;}
 const program=(material:T.Material)=>(renderer.properties.get(material) as {currentProgram?:Program}).currentProgram;
 const replay=(pass:Pass)=>{
  pass.done=true;if(!pass.rows.length)return;
  const source=pass.source,texture=source.texture;
  const result={requestedSamples:source.samples,originalSamples:pass.samples,originalDepthBits:pass.depthBits,viewport:pass.viewport,normalOverride:pass.override,draws:pass.rows.length,programMatches:0,programMismatches:0,matrixMismatches:0,triangles:0,actualSamples:0,actualDepthBits:0,error:''};report.passes.push(result);
  const colorSpace=texture.colorSpace;
  if(texture.format!==T.RGBAFormat||(colorSpace!==T.NoColorSpace&&colorSpace!==T.LinearSRGBColorSpace&&colorSpace!==T.SRGBColorSpace)){result.error='Unsupported source color attachment';report.errors.push(result.error);return;}
  const target=new T.WebGLRenderTarget(source.width,source.height,{samples:source.samples,depthBuffer:true,stencilBuffer:source.stencilBuffer,type:texture.type,format:T.RGBAFormat,internalFormat:texture.internalFormat,colorSpace,generateMipmaps:false});owned.push(target);
  if(source.depthTexture){const depth=new T.DepthTexture(source.width,source.height,source.depthTexture.type);target.depthTexture=depth;depth.format=source.depthTexture.format;depth.addEventListener('dispose',()=>disposedDepth.add(depth));}
  target.viewport.fromArray(pass.viewport);target.scissor.copy(source.scissor);target.scissorTest=source.scissorTest;
  const previousTarget=renderer.getRenderTarget(),previousCube=renderer.getActiveCubeFace(),previousMip=renderer.getActiveMipmapLevel();
  const depthMask=!!gl.getParameter(gl.DEPTH_WRITEMASK),colorMask=Array.from(gl.getParameter(gl.COLOR_WRITEMASK) as boolean[]),depthClear=Number(gl.getParameter(gl.DEPTH_CLEAR_VALUE));
  const viewport=new T.Vector4().fromArray(gl.getParameter(gl.VIEWPORT)),scissor=new T.Vector4().fromArray(gl.getParameter(gl.SCISSOR_BOX)),scissorTest=!!gl.getParameter(gl.SCISSOR_TEST);
  try{
   if(colorMask.some(v=>v!==colorMask[0]))throw new Error('Nonuniform color mask unsupported');
   renderer.setRenderTarget(target);result.actualSamples=gl.getParameter(gl.SAMPLES);result.actualDepthBits=gl.getParameter(gl.DEPTH_BITS);
   if(result.actualSamples!==pass.samples||result.actualDepthBits!==pass.depthBits||!same(Array.from(gl.getParameter(gl.VIEWPORT)),pass.viewport))throw new Error('Replay raster target mismatch');
   renderer.state.buffers.depth.setMask(true);renderer.state.buffers.depth.setClear(1);renderer.clear(false,true,true);
   for(const row of pass.rows){
    const material=row.args[3],object=row.args[4];
    if(material.side!==row.side||material.version!==row.version||!same(object.matrixWorld.elements,row.world)||!same(object.modelViewMatrix.elements,row.modelView)||!same(object.normalMatrix.elements,row.normal)||!same((object as T.Mesh).morphTargetInfluences??[],row.morph)){result.matrixMismatches++;report.matrixMismatches++;continue;}
    const write=material.colorWrite;
    try{material.colorWrite=false;originalDraw.apply(renderer,row.args);}
    finally{material.colorWrite=write;}
    const actual=program(material),matches=actual===row.program&&actual?.program===row.linked;
    if(matches){result.programMatches++;report.programMatches++;}else{result.programMismatches++;report.programMismatches++;}
    result.triangles+=row.triangles;report.replayedTriangles+=row.triangles;report.replayedDraws++;
   }
   if(!result.programMismatches&&!result.matrixMismatches)consume?.(target,{samples:pass.samples,depthBits:pass.depthBits,viewport:pass.viewport,normalOverride:pass.override},(...args)=>originalDraw.apply(renderer,args));
   const error=gl.getError();if(error)throw new Error(`Replay WebGL ${error}`);
  }catch(error){result.error=String(error);report.errors.push(result.error);}
  finally{renderer.state.buffers.depth.setMask(depthMask);renderer.state.buffers.depth.setClear(depthClear);renderer.state.buffers.color.setMask(colorMask[0]);renderer.setRenderTarget(previousTarget,previousCube,previousMip);renderer.state.viewport(viewport);renderer.state.scissor(scissor);renderer.state.setScissorTest(scissorTest);}
 };
 renderer.renderBufferDirect=(...args)=>{
  originalDraw.apply(renderer,args);
  const [passCamera,passScene,geometry,material,object,group]=args;
  if(passCamera!==camera||passScene!==scene||!eligible.has(object as T.Mesh)||!opaqueDepthMaterial(material))return;
  const source=renderer.getRenderTarget();if(!source||source.textures.length!==1)return;
  const linked=program(material);if(!linked?.program){report.errors.push('Original linked program unavailable');return;}
  let pass=passes.get(source);
  if(!pass){pass={source,rows:[],samples:gl.getParameter(gl.SAMPLES),depthBits:gl.getParameter(gl.DEPTH_BITS),viewport:Array.from(gl.getParameter(gl.VIEWPORT)),override:scene.overrideMaterial!==null,done:false};passes.set(source,pass);}
  if(pass.done){report.errors.push('Unexpected target reused after snapshot');return;}
  const count=geometry.index?.count??geometry.attributes.position?.count??0,first=Math.max(geometry.drawRange.start,group?.start??0),last=Math.min(count,geometry.drawRange.start+geometry.drawRange.count,group?group.start+group.count:Infinity);
  pass.rows.push({args,program:linked,linked:linked.program,world:object.matrixWorld.elements.slice(),modelView:object.modelViewMatrix.elements.slice(),normal:object.normalMatrix.elements.slice(),morph:[...((object as T.Mesh).morphTargetInfluences??[])],side:material.side,version:material.version,triangles:Math.max(0,Math.floor((last-first)/3))});report.recordedDraws++;
 };
 scene.onAfterRender=function(...args){
  if(args[0]===renderer&&args[2]===camera)for(const pass of passes.values())if(!pass.done)replay(pass);
  originalAfter.apply(this,args);
 };
 try{draw();}finally{renderer.renderBufferDirect=originalDraw;scene.onAfterRender=originalAfter;for(const target of owned){target.dispose();if(target.depthTexture&&!disposedDepth.has(target.depthTexture))target.depthTexture.dispose();}passes.clear();}
 return report;
}

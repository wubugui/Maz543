import * as T from 'three';
import {StaticOccluderObservations,opaqueDepthMaterial} from './staticOccluderScene';
import {ConservativeRasterBounds,type RasterVolume} from './conservativeRasterBounds';
import {containsVolume} from './normalOcclusionCache';
import {replayOriginalPassDepth,type OriginalProgramDraw} from './originalPassDepthReplay';
import {OriginalReplayDepthQueries} from './originalReplayDepthQueries';

const same=(a:unknown[],b:unknown[])=>a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));
type Proof={volume:RasterVolume;zero:boolean};
type Pass={target:T.WebGLRenderTarget;signature:unknown[];samples:number;depthBits:number;viewport:number[];normalOverride:boolean;programs:Map<T.Mesh,OriginalProgramDraw[]>;proofs:Map<T.Mesh,Proof>};

/** Exact stock-material configuration, including values which do not increment
 * Material.version. Unsupported property objects force original rendering. */
export function materialDepthSignature(material:T.Material):unknown[]|null{
 if(!opaqueDepthMaterial(material)||material.customProgramCacheKey!==T.Material.prototype.customProgramCacheKey)return null;
 const out:unknown[]=[material];
 for(const key of Object.keys(material).sort()){
  if(key==='userData'||key==='_listeners')continue;
  const value=(material as unknown as Record<string,unknown>)[key];out.push(key);
  if(value===null||value===undefined||['boolean','number','string'].includes(typeof value)){out.push(value);continue;}
  if(value instanceof T.Texture){out.push(value,value.version,value.source,value.source.version,value.mapping,value.channel,value.colorSpace,value.type,value.format,...value.matrix.elements);continue;}
  if(value instanceof T.Color||value instanceof T.Euler||value instanceof T.Vector2||value instanceof T.Vector3||value instanceof T.Vector4||value instanceof T.Matrix3||value instanceof T.Matrix4){out.push(...value.toArray());continue;}
  if(Array.isArray(value)&&value.every(v=>typeof v==='number')){out.push(value.length,...value);continue;}
  if(key==='defines'&&typeof value==='object'){for(const [k,v] of Object.entries(value as object).sort())out.push(k,v);continue;}
  return null;
 }
 return out;
}
const targetSignature=(target:T.WebGLRenderTarget)=>[target,target.width,target.height,target.depth,target.samples,target.depthBuffer,target.stencilBuffer,target.depthTexture,target.depthTexture?.type,target.depthTexture?.format,target.textures.length,...target.textures.flatMap(t=>[t,t.type,t.format,t.internalFormat,t.colorSpace]),...target.viewport.toArray(),...target.scissor.toArray(),target.scissorTest];

/** DEV-only exact-program camera-pass cache. Original renderBufferDirect still
 * selects the original program and uploads original matrices/uniforms. Only a
 * proven zero-sample TRIANGLES submission is omitted at the actual GL call.
 * Shadow, transparent, custom and unsupported draws remain original. */
export class OriginalProgramOcclusionCache{
 private renderer:T.WebGLRenderer;private normal:T.MeshNormalMaterial;private gl:WebGL2RenderingContext;
 private observations=new StaticOccluderObservations();private bounds=new ConservativeRasterBounds();private queries:OriginalReplayDepthQueries|null=null;
 private retained=new Map<T.Mesh,unknown[]>();private excluded=new WeakSet<T.Mesh>();private passes:Pass[]=[];private global:unknown[]=[];
 private ready=false;private pending=false;private disposed=false;private generation=0;
 private controlSummary:unknown=null;
 private watched=new Set<T.BufferGeometry|T.Material|T.WebGLRenderTarget>();private changed=()=>this.invalidate();
 lastReport:Record<string,unknown>|undefined;
 constructor(renderer:T.WebGLRenderer,normal:T.MeshNormalMaterial){this.renderer=renderer;this.normal=normal;this.gl=renderer.getContext() as WebGL2RenderingContext;}
 invalidate(){this.generation++;this.queries?.cancel();this.pending=false;this.ready=false;this.controlSummary=null;this.retained.clear();this.passes=[];this.bounds.clear();for(const asset of this.watched)asset.removeEventListener('dispose',this.changed);this.watched.clear();}
 private watch(asset:T.BufferGeometry|T.Material|T.WebGLRenderTarget){if(!this.watched.has(asset)){this.watched.add(asset);asset.addEventListener('dispose',this.changed);}}
 private signature(scene:T.Scene,camera:T.Camera){
  const r=this.renderer,gl=this.gl,n=this.normal;
  if(T.REVISION!=='183'||r.xr.enabled||r.capabilities.precision!=='highp'||r.capabilities.logarithmicDepthBuffer||r.capabilities.reversedDepthBuffer||r.clippingPlanes.length||gl.isContextLost()||scene.overrideMaterial||scene.onBeforeRender!==T.Object3D.prototype.onBeforeRender||scene.onAfterRender!==T.Object3D.prototype.onAfterRender)return null;
  const out:unknown[]=[camera,camera.type,gl.drawingBufferWidth,gl.drawingBufferHeight,...camera.matrixWorldInverse.elements,...camera.projectionMatrix.elements,camera.layers.mask,r.localClippingEnabled,r.shadowMap.enabled,r.shadowMap.type,r.toneMapping,r.outputColorSpace,scene.environment,scene.environment?.version,scene.environment?.mapping,scene.fog,scene.fog?.constructor,scene.environmentIntensity,...scene.environmentRotation.toArray()];
  const materials=new Set<T.Material>([n]);let unsupported=false;
  scene.traverseVisible(object=>{
   if(object.onBeforeRender!==T.Object3D.prototype.onBeforeRender||object.onAfterRender!==T.Object3D.prototype.onAfterRender)unsupported=true;
   if(object instanceof T.Mesh){
    if(object.onBeforeShadow!==T.Object3D.prototype.onBeforeShadow||object.onAfterShadow!==T.Object3D.prototype.onAfterShadow)unsupported=true;
    for(const material of Array.isArray(object.material)?object.material:[object.material]){
     if(material.onBeforeCompile!==T.Material.prototype.onBeforeCompile||material.onBeforeRender!==T.Material.prototype.onBeforeRender||material.customProgramCacheKey!==T.Material.prototype.customProgramCacheKey)unsupported=true;
     if(opaqueDepthMaterial(material))materials.add(material);
    }
   }
   if(object instanceof T.Light)out.push(object,object.type,object.layers.mask,object.castShadow,object.intensity,...object.color.toArray(),...object.matrixWorld.elements);
  });
  for(const material of materials){const signature=materialDepthSignature(material);if(!signature)return null;out.push(...signature);}
  return unsupported?null:out;
 }
 render(scene:T.Scene,camera:T.Camera,allowed:boolean,draw:()=>void){
  const r=this.renderer,gl=this.gl,start=performance.now();
  const report={kind:'original-program-occlusion-cache',generation:this.generation,rebuilt:false,pending:false,ready:false,occluders:0,excludedChanged:0,skipped:0,savedTriangles:0,programFallbacks:0,depthControls:null as unknown,passes:[] as {samples:number;skipped:number;savedTriangles:number}[],prepareMs:0,error:'',limits:'DEV only; original program/uniform setup retained. Only proven camera-pass GL triangle submissions omitted. Original shadows/transparent draws and full mechanical solver retained. Stable FPS and full-product acceptance remain open.'};this.lastReport=report;
  scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
  const signature=allowed&&!this.disposed?this.signature(scene,camera):null;
  if(!signature){this.invalidate();draw();return report;}
  if(!same(signature,this.global)){this.invalidate();this.global=signature;}
  const rows=this.observations.observe(scene,camera).rows,current=new Map(rows.map(row=>[row.mesh,row]));
  for(const [mesh,values] of this.retained)if(!current.has(mesh)||!same(values,current.get(mesh)!.values)){this.excluded.add(mesh);report.excludedChanged++;}
  if(report.excludedChanged)this.invalidate();
  if(this.passes.some(pass=>!same(pass.signature,targetSignature(pass.target))||[...pass.programs.values()].some(records=>records.some(row=>row.program.program!==row.linked))))this.invalidate();
  if(this.pending){
   const result=this.queries?.poll();
   if(result){
    if('controlsPassed' in result.summary&&result.summary.controlsPassed&&result.summary.queryError===0&&result.summary.passes.length===this.passes.length){
     const byUuid=new Map(rows.map(row=>[row.mesh.uuid,row.mesh]));
     for(const resultRow of result.results){const mesh=resultRow.meshUuid?byUuid.get(resultRow.meshUuid):null;if(mesh&&resultRow.volume)this.passes[resultRow.pass].proofs.set(mesh,{volume:resultRow.volume,zero:!resultRow.anySamplesPassed});}
     this.ready=true;this.pending=false;
     this.controlSummary=result.summary;
    }else{report.error='Asynchronous controls failed or partial pass set';this.invalidate();}
   }
  }
  for(const pass of this.passes){for(const mesh of pass.programs.keys())if(!current.has(mesh)){pass.proofs.delete(mesh);pass.programs.delete(mesh);}}
  if(!this.ready&&!this.pending){
   const stable=rows.filter(row=>row.stableFrames>=2&&!this.excluded.has(row.mesh));
   if(!stable.length){draw();return report;}
   this.queries??=new OriginalReplayDepthQueries(r,scene,camera);this.queries.begin(rows,true);
   const records=new Map<T.WebGLRenderTarget,Map<T.Mesh,OriginalProgramDraw[]>>();
   let replay;
   try{replay=replayOriginalPassDepth(r,scene,camera,new Set(stable.map(row=>row.mesh)),draw,this.queries.consume,row=>{
    let meshes=records.get(row.target);if(!meshes){meshes=new Map();records.set(row.target,meshes);}const list=meshes.get(row.mesh)??[];list.push(row);meshes.set(row.mesh,list);
   });}catch(error){this.invalidate();throw error;}
   this.queries.finish();report.rebuilt=true;
   if(replay.errors.length||replay.programMismatches||replay.matrixMismatches||replay.passes.length!==3||records.size!==3){report.error='Original snapshot/program proof failed';this.invalidate();return report;}
   this.passes=[...records].map(([target,programs],i)=>{const pass=replay.passes[i];return {target,signature:targetSignature(target),programs,proofs:new Map(),samples:pass.actualSamples as number,depthBits:pass.actualDepthBits as number,viewport:pass.viewport as number[],normalOverride:pass.normalOverride as boolean};});
   for(const row of stable){this.retained.set(row.mesh,row.values);this.watch(row.mesh.geometry);for(const material of Array.isArray(row.mesh.material)?row.mesh.material:[row.mesh.material])this.watch(material);}
   for(const pass of this.passes)this.watch(pass.target);this.watch(this.normal);
   this.pending=true;report.pending=true;report.occluders=this.retained.size;report.prepareMs=performance.now()-start;return report;
  }
  report.generation=this.generation;report.ready=this.ready;report.pending=this.pending;report.occluders=this.retained.size;report.prepareMs=performance.now()-start;report.depthControls=this.controlSummary;
  if(!this.ready){draw();return report;}
  const volumes=new Map<string,Map<T.Mesh,RasterVolume|null>>(),matrix=new T.Matrix4(),passStates=new Map<Pass,boolean>();
  const original=r.renderBufferDirect,elements=gl.drawElements,arrays=gl.drawArrays;
  let active:{material:T.Material;records:OriginalProgramDraw[];pass:Pass}|null=null,omitted=0,omittedTriangles=0;
  const skip=(mode:number,count:number)=>{
   if(!active||mode!==gl.TRIANGLES||count<=0||count%3!==0)return false;
   const selected=(r.properties.get(active.material) as {currentProgram?:{program:WebGLProgram}}).currentProgram;
   if(!active.records.some(row=>selected===row.program&&selected.program===row.linked)){report.programFallbacks++;return false;}
   omitted++;omittedTriangles+=count/3;const index=this.passes.indexOf(active.pass);report.passes[index].skipped++;report.passes[index].savedTriangles+=count/3;return true;
  };
  report.passes=this.passes.map(p=>({samples:p.samples,skipped:0,savedTriangles:0}));
  try{
   gl.drawElements=function(mode,count,type,offset){if(!skip(mode,count))elements.call(gl,mode,count,type,offset);};
   gl.drawArrays=function(mode,first,count){if(!skip(mode,count))arrays.call(gl,mode,first,count);};
   r.renderBufferDirect=(...args)=>{
    const [passCamera,passScene,geometry,material,object]=args;active=null;omitted=0;omittedTriangles=0;
    const pass=this.passes.find(p=>p.target===r.getRenderTarget()&&p.normalOverride===(scene.overrideMaterial!==null));
    if(pass&&passCamera===camera&&passScene===scene&&current.has(object as T.Mesh)&&opaqueDepthMaterial(material)){
     if(!passStates.has(pass))passStates.set(pass,gl.getParameter(gl.SAMPLES)===pass.samples&&gl.getParameter(gl.DEPTH_BITS)===pass.depthBits&&same(Array.from(gl.getParameter(gl.VIEWPORT)),pass.viewport));
     const mesh=object as T.Mesh,proof=pass.proofs.get(mesh),records=pass.programs.get(mesh)?.filter(row=>row.material===material);
     if(passStates.get(pass)&&proof?.zero&&records?.length&&mesh.geometry===geometry){
      const viewportKey=pass.viewport.join(',');let passVolumes=volumes.get(viewportKey);if(!passVolumes){passVolumes=new Map();volumes.set(viewportKey,passVolumes);}
      if(!passVolumes.has(mesh)){matrix.multiplyMatrices(camera.matrixWorldInverse,mesh.matrixWorld);const v=this.bounds.volume(geometry,matrix,camera.projectionMatrix,pass.viewport,mesh.morphTargetInfluences);const [, ,width,height]=pass.viewport;passVolumes.set(mesh,v?{...v,left:Math.max(0,v.left),right:Math.min(width,v.right),bottom:Math.max(0,v.bottom),top:Math.min(height,v.top)}:null);}
      const volume=passVolumes.get(mesh);if(volume&&containsVolume(proof.volume,volume))active={material,records,pass};
     }
    }
    try{return original.apply(r,args);}finally{active=null;r.info.render.calls-=omitted;r.info.render.triangles-=omittedTriangles;report.skipped+=omitted;report.savedTriangles+=omittedTriangles;}
   };
   draw();
  }catch(error){this.invalidate();throw error;}
  finally{r.renderBufferDirect=original;gl.drawElements=elements;gl.drawArrays=arrays;}
  return report;
 }
 dispose(){if(this.disposed)return;this.disposed=true;this.invalidate();this.queries?.dispose();this.queries=null;this.observations.clear();}
}

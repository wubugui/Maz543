import * as T from 'three';
import {ConservativeRasterBounds,type RasterVolume} from './conservativeRasterBounds';
import {StaticOccluderObservations,createStaticOccluderScene,type OccluderObservation} from './staticOccluderScene';

const equal=(a:unknown[],b:unknown[])=>a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));
type Certificate={volume:RasterVolume;zero:boolean};
type Pending={query:WebGLQuery;mesh?:T.Mesh;volume?:RasterVolume;control?:boolean};
type Batch={generation:number;rows:Pending[]};
const DEPTH_GUARD=2**-18;
export function containsVolume(proof:RasterVolume,current:RasterVolume){
 return [...Object.values(proof),...Object.values(current)].every(Number.isFinite)&&current.left>=proof.left&&current.right<=proof.right&&current.bottom>=proof.bottom&&current.top<=proof.top&&current.nearDepth>=proof.nearDepth;
}
export function queryCertificate(volume:RasterVolume,width:number,height:number):RasterVolume|null{
 if(!Object.values(volume).every(Number.isFinite)||volume.right<=0||volume.top<=0||volume.left>=width||volume.bottom>=height)return null;
 const result={left:Math.max(0,volume.left-2),right:Math.min(width,volume.right+2),bottom:Math.max(0,volume.bottom-2),top:Math.min(height,volume.top+2),nearDepth:volume.nearDepth-2**-17};
 return result.nearDepth>DEPTH_GUARD&&result.nearDepth<1?result:null;
}
const clipped=(volume:RasterVolume,width:number,height:number):RasterVolume=>({...volume,left:Math.max(0,volume.left),right:Math.min(width,volume.right),bottom:Math.max(0,volume.bottom),top:Math.min(height,volume.top)});

/** DEV only. Proves coverage against a retained static depth image using the
 * exact GTAO normal material. Culls ONLY that material's vehicle-camera pass;
 * main color, transmission, shadows and mechanics remain original. */
export class NormalOcclusionCache{
 private readonly gl:WebGL2RenderingContext;private readonly renderer:T.WebGLRenderer;private readonly normal:T.MeshNormalMaterial;
 private observations=new StaticOccluderObservations();private bounds=new ConservativeRasterBounds();private excluded=new WeakSet<T.Mesh>();
 private retained=new Map<T.Mesh,unknown[]>();private certificates=new Map<T.Mesh,Certificate>();private pending:Batch[]=[];
 private volumes=new WeakMap<T.Mesh,{values:unknown[];volume:RasterVolume|null}>();private global:unknown[]=[];private generation=0;
 private target:T.WebGLRenderTarget|null=null;private controlTarget=new T.WebGLRenderTarget(1,1,{depthBuffer:true,stencilBuffer:false,samples:0});
 private watched=new Set<T.BufferGeometry>();private readonly changed=()=>this.invalidate();
 private queryScene=new T.Scene();private queryGeometry=new T.PlaneGeometry(2,2);private queryMaterial:T.ShaderMaterial;private quad:T.Mesh;
 private disposed=false;
 lastReport:Record<string,unknown>|undefined;
 constructor(renderer:T.WebGLRenderer,normal:T.MeshNormalMaterial){
  this.renderer=renderer;this.gl=renderer.getContext() as WebGL2RenderingContext;this.normal=normal;
  this.queryMaterial=new T.ShaderMaterial({uniforms:{rectangle:{value:new T.Vector4()},closestDepth:{value:0}},vertexShader:'uniform vec4 rectangle; uniform float closestDepth; void main(){gl_Position=vec4(mix(rectangle.xy,rectangle.zw,position.xy*0.5+0.5),closestDepth*2.0-1.0,1.0);}',fragmentShader:'void main(){gl_FragColor=vec4(1.0);}',side:T.DoubleSide,depthWrite:false,depthTest:true,depthFunc:T.LessEqualDepth,colorWrite:false,blending:T.NoBlending});
  this.quad=new T.Mesh(this.queryGeometry,this.queryMaterial);this.quad.frustumCulled=false;this.queryScene.add(this.quad);normal.addEventListener('dispose',this.changed);
 }
 invalidate(){
  this.generation++;for(const batch of this.pending)for(const row of batch.rows)this.gl.deleteQuery(row.query);this.pending=[];
  for(const geometry of this.watched)geometry.removeEventListener('dispose',this.changed);this.watched.clear();
  this.target?.dispose();this.target=null;this.retained.clear();this.certificates.clear();this.volumes=new WeakMap();
 }
 private poll(){
  const gl=this.gl;let controlsFailed=false;
  this.pending=this.pending.filter(batch=>{
   if(batch.rows.some(row=>!gl.getQueryParameter(row.query,gl.QUERY_RESULT_AVAILABLE)))return true;
   const values=batch.rows.map(row=>({row,positive:!!gl.getQueryParameter(row.query,gl.QUERY_RESULT)}));
   const controls=values.filter(item=>item.row.control!==undefined),valid=controls.length===2&&controls.every(item=>item.positive===item.row.control);
   if(valid&&batch.generation===this.generation)for(const {row,positive} of values)if(row.mesh&&row.volume)this.certificates.set(row.mesh,{volume:row.volume,zero:!positive});
   controlsFailed ||= !valid;for(const row of batch.rows)gl.deleteQuery(row.query);return false;
  });
  if(controlsFailed)this.invalidate();return controlsFailed;
 }
 private withState(run:()=>void){
  const r=this.renderer,gl=this.gl,target=r.getRenderTarget(),cube=r.getActiveCubeFace(),mip=r.getActiveMipmapLevel(),color=r.getClearColor(new T.Color()),alpha=r.getClearAlpha();
  const auto=r.autoClear,shadowAuto=r.shadowMap.autoUpdate,shadowNeeds=r.shadowMap.needsUpdate,normalWrite=this.normal.colorWrite;
  const depthMask=!!gl.getParameter(gl.DEPTH_WRITEMASK),colorMask=!!gl.getParameter(gl.COLOR_WRITEMASK)[0],depthClear=Number(gl.getParameter(gl.DEPTH_CLEAR_VALUE));
  try{r.autoClear=false;r.shadowMap.autoUpdate=false;r.shadowMap.needsUpdate=false;run();}
  finally{this.normal.colorWrite=normalWrite;r.autoClear=auto;r.shadowMap.autoUpdate=shadowAuto;r.shadowMap.needsUpdate=shadowNeeds;r.setClearColor(color,alpha);r.state.buffers.depth.setClear(depthClear);r.state.buffers.depth.setMask(depthMask);r.state.buffers.color.setMask(colorMask);r.setRenderTarget(target,cube,mip);}
 }
 private build(rows:OccluderObservation[],camera:T.Camera,width:number,height:number){
  const snapshot=createStaticOccluderScene(rows,this.normal),r=this.renderer;
  this.target=new T.WebGLRenderTarget(width,height,{depthBuffer:true,stencilBuffer:false,samples:0});
  try{this.withState(()=>{r.setRenderTarget(this.target);r.state.buffers.depth.setMask(true);r.state.buffers.depth.setClear(1);r.clear(true,true,true);this.normal.colorWrite=false;r.render(snapshot.scene,camera);if(this.gl.getParameter(this.gl.SAMPLES)!==0||this.gl.getParameter(this.gl.DEPTH_BITS)!==24)throw new Error('Unsupported normal proof depth target');});}
  finally{snapshot.dispose();}
  for(const row of rows){this.retained.set(row.mesh,row.values);const geometry=row.mesh.geometry;if(!this.watched.has(geometry)){this.watched.add(geometry);geometry.addEventListener('dispose',this.changed);}}
 }
 private query(rows:{mesh:T.Mesh;volume:RasterVolume}[],camera:T.Camera,width:number,height:number){
  const r=this.renderer,gl=this.gl,original=r.renderBufferDirect,batch:Batch={generation:this.generation,rows:[]};
  let controls=false;this.pending.push(batch);
  r.renderBufferDirect=(...args)=>{
   if(args[4]!==this.quad)return original.apply(r,args);
   const items:({mesh?:T.Mesh;volume?:RasterVolume;control?:boolean})[]=controls?[{control:true},{control:false}]:rows;
   for(const item of items){
    if(gl.getQuery(gl.ANY_SAMPLES_PASSED,gl.CURRENT_QUERY)||gl.getQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,gl.CURRENT_QUERY))continue;
    const query=gl.createQuery();if(!query)continue;
    const v=item.volume;
    this.queryMaterial.uniforms.rectangle.value.set(v?(v.left-2)*2/width-1:-1,v?(v.bottom-2)*2/height-1:-1,v?(v.right+2)*2/width-1:1,v?(v.top+2)*2/height-1:1);
    this.queryMaterial.uniforms.closestDepth.value=v?v.nearDepth-DEPTH_GUARD:(item.control?0.25:0.75);this.queryMaterial.uniformsNeedUpdate=true;
    batch.rows.push({...item,query});gl.beginQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,query);
    try{original.apply(r,args);}finally{gl.endQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE);}
   }
  };
  try{this.withState(()=>{r.setRenderTarget(this.target);r.render(this.queryScene,camera);r.setRenderTarget(this.controlTarget);r.state.buffers.depth.setMask(true);r.state.buffers.depth.setClear(.5);r.clear(false,true,false);controls=true;r.render(this.queryScene,camera);});}
  finally{r.renderBufferDirect=original;}
 }
 render(scene:T.Scene,camera:T.Camera,allowed:boolean,draw:()=>void){
  const r=this.renderer,gl=this.gl,n=this.normal,start=performance.now();
  const report={kind:'static-normal-occlusion-cache',rebuilt:false,occluders:0,excludedChanged:0,queried:0,pendingBatches:0,certificates:0,skipped:0,savedTriangles:0,controlsFailed:false,prepareMs:0,error:'',limits:'DEV-only normal-material camera pass. Original main/transmission/shadow draws and full mechanics retained. Query regions are conservative; leaving a certified region restores original drawing. Not full product performance acceptance.'};this.lastReport=report;
  let callback=false;scene.traverseVisible(object=>{if(object.onBeforeRender!==T.Object3D.prototype.onBeforeRender||object.onAfterRender!==T.Object3D.prototype.onAfterRender)callback=true;if(object instanceof T.Mesh){if(object.onBeforeShadow!==T.Object3D.prototype.onBeforeShadow||object.onAfterShadow!==T.Object3D.prototype.onAfterShadow)callback=true;for(const m of Array.isArray(object.material)?object.material:[object.material])if(m.onBeforeRender!==T.Material.prototype.onBeforeRender||m.onBeforeCompile!==T.Material.prototype.onBeforeCompile)callback=true;}});
  if(this.disposed||!allowed||callback||scene.onBeforeRender!==T.Object3D.prototype.onBeforeRender||scene.onAfterRender!==T.Object3D.prototype.onAfterRender||gl.isContextLost()||r.capabilities.precision!=='highp'||r.capabilities.logarithmicDepthBuffer||r.capabilities.reversedDepthBuffer||r.clippingPlanes.length||Object.getPrototypeOf(n)!==T.MeshNormalMaterial.prototype||n.side!==T.FrontSide||!n.colorWrite||!n.depthWrite||!n.depthTest||n.depthFunc!==T.LessEqualDepth||n.blending!==T.NoBlending||n.clippingPlanes?.length||n.alphaTest||n.alphaHash||n.alphaToCoverage||n.polygonOffset||n.stencilWrite||n.wireframe||n.displacementMap||n.flatShading||n.transparent||!n.visible||(n.precision&&n.precision!=='highp')||Object.keys(n.defines??{}).length||n.onBeforeRender!==T.Material.prototype.onBeforeRender||n.onBeforeCompile!==T.Material.prototype.onBeforeCompile||n.customProgramCacheKey!==T.Material.prototype.customProgramCacheKey){this.invalidate();draw();return report;}
  scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
  const width=gl.drawingBufferWidth,height=gl.drawingBufferHeight,global=[width,height,...camera.matrixWorldInverse.elements,...camera.projectionMatrix.elements,camera.layers.mask,n.version,n.side,n.depthFunc,n.colorWrite,n.depthWrite];
  if(!equal(global,this.global)){this.invalidate();this.global=global;}
  const observed=this.observations.observe(scene,camera),current=new Map(observed.rows.map(row=>[row.mesh,row]));
  for(const [mesh,values] of this.retained)if(!current.has(mesh)||!equal(values,current.get(mesh)!.values)){this.excluded.add(mesh);report.excludedChanged++;}
  if(report.excludedChanged)this.invalidate();
  report.controlsFailed=this.poll();
  for(const mesh of this.certificates.keys())if(!current.has(mesh))this.certificates.delete(mesh);
  const volumes=new Map<T.Mesh,RasterVolume>();
  try{
   if(!this.target){const stable=observed.rows.filter(row=>row.stableFrames>=2&&!this.excluded.has(row.mesh));if(stable.length){this.build(stable,camera,width,height);report.rebuilt=true;}}
   const matrix=new T.Matrix4();
   for(const row of observed.rows){
    let entry=this.volumes.get(row.mesh);
    if(!entry||!equal(entry.values,row.values)){matrix.multiplyMatrices(camera.matrixWorldInverse,row.mesh.matrixWorld);entry={values:row.values,volume:this.bounds.volume(row.mesh.geometry,matrix,camera.projectionMatrix,[0,0,width,height],row.mesh.morphTargetInfluences)};this.volumes.set(row.mesh,entry);}
    if(entry.volume&&entry.volume.right>0&&entry.volume.top>0&&entry.volume.left<width&&entry.volume.bottom<height)volumes.set(row.mesh,clipped(entry.volume,width,height));
   }
   if(this.target&&this.pending.length<2){
    const queued=new Set(this.pending.flatMap(batch=>batch.rows.flatMap(row=>row.mesh?[row.mesh]:[])));
    const requests=observed.rows.filter(row=>{const volume=volumes.get(row.mesh),proof=this.certificates.get(row.mesh);return volume&&!queued.has(row.mesh)&&(!proof||!containsVolume(proof.volume,volume));}).sort((a,b)=>b.triangles-a.triangles).slice(0,256).flatMap(row=>{const volume=queryCertificate(volumes.get(row.mesh)!,width,height);return volume?[{mesh:row.mesh,volume}]:[];});
    if(requests.length){this.query(requests,camera,width,height);report.queried=requests.length;}
   }
   const error=gl.getError();if(error)throw new Error(`WebGL ${error}`);
  }catch(error){report.error=String(error);this.invalidate();}
  report.prepareMs=performance.now()-start;report.occluders=this.retained.size;report.pendingBatches=this.pending.length;report.certificates=this.certificates.size;
  const original=r.renderBufferDirect;let passValid:boolean|undefined;
  r.renderBufferDirect=(...args)=>{
   const [passCamera,passScene,geometry,material,object,group]=args;
   if(this.target&&passCamera===camera&&passScene===scene&&scene.overrideMaterial===n&&material===n&&current.has(object as T.Mesh)){
    if(passValid===undefined){const viewport=Array.from(gl.getParameter(gl.VIEWPORT) as Int32Array);passValid=gl.getParameter(gl.SAMPLES)===0&&gl.getParameter(gl.DEPTH_BITS)===24&&equal(viewport,[0,0,width,height]);}
    const proof=this.certificates.get(object as T.Mesh),volume=volumes.get(object as T.Mesh);
    if(passValid&&proof?.zero&&volume&&containsVolume(proof.volume,volume)){
     const count=geometry.index?.count??geometry.attributes.position.count,first=Math.max(geometry.drawRange.start,group?.start??0),last=Math.min(count,geometry.drawRange.start+geometry.drawRange.count,group?group.start+group.count:Infinity);
     report.skipped++;report.savedTriangles+=Math.max(0,Math.floor((last-first)/3));return;
    }
   }
   return original.apply(r,args);
  };
  try{draw();}catch(error){this.invalidate();throw error;}finally{r.renderBufferDirect=original;}return report;
 }
 dispose(){if(this.disposed)return;this.disposed=true;this.invalidate();this.normal.removeEventListener('dispose',this.changed);this.controlTarget.dispose();this.queryScene.clear();this.queryGeometry.dispose();this.queryMaterial.dispose();this.observations.clear();this.bounds.clear();}
}

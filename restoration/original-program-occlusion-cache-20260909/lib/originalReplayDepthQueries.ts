import * as T from 'three';
import {ConservativeRasterBounds} from './conservativeRasterBounds';
import type {OccluderObservation} from './staticOccluderScene';
import {queryCertificate} from './normalOcclusionCache';
import type {RasterVolume} from './conservativeRasterBounds';

type Info={samples:number;depthBits:number;viewport:number[];normalOverride:boolean};
type Entry={query:WebGLQuery;pass:number;name?:string;meshUuid?:string;volume?:RasterVolume;triangles?:number;stable?:boolean;controlExpected?:boolean};
/** Finite async queries against exact original-program snapshots. No source
 * visibility or draw is changed; unavailable query results are never read. */
export class OriginalReplayDepthQueries{
 private renderer:T.WebGLRenderer;private scene:T.Scene;private camera:T.Camera;private gl:WebGL2RenderingContext;
 private bounds=new ConservativeRasterBounds();private sources:OccluderObservation[]=[];private entries:Entry[]=[];private passes:Info[]=[];private controls:T.WebGLRenderTarget[]=[];
 private geometry=new T.PlaneGeometry(2,2);private material:T.ShaderMaterial;private quad:T.Mesh;private queryScene=new T.Scene();private prepared=false;private submitted=false;private disposed=false;
 private certificates=false;
 constructor(renderer:T.WebGLRenderer,scene:T.Scene,camera:T.Camera){
  this.renderer=renderer;this.scene=scene;this.camera=camera;this.gl=renderer.getContext() as WebGL2RenderingContext;
  this.material=new T.ShaderMaterial({precision:'highp',uniforms:{rectangle:{value:new T.Vector4()},closestDepth:{value:0}},vertexShader:'uniform vec4 rectangle;uniform float closestDepth;void main(){gl_Position=vec4(mix(rectangle.xy,rectangle.zw,position.xy*.5+.5),closestDepth*2.-1.,1.);}',fragmentShader:'void main(){gl_FragColor=vec4(1.);}',side:T.DoubleSide,colorWrite:false,depthWrite:false,depthTest:true,depthFunc:T.LessEqualDepth,blending:T.NoBlending});
  this.quad=new T.Mesh(this.geometry,this.material);this.quad.frustumCulled=false;this.queryScene.add(this.quad);
 }
 begin(rows:OccluderObservation[],certificates=false){this.cancel();this.sources=rows;this.certificates=certificates;}
 consume=(target:T.WebGLRenderTarget,info:Info,direct:(...args:Parameters<T.WebGLRenderer['renderBufferDirect']>)=>void)=>{
  const gl=this.gl,r=this.renderer,pass=this.passes.length;this.passes.push(info);
  if(this.disposed||r.capabilities.precision!=='highp'||info.depthBits!==24||info.viewport[0]!==0||info.viewport[1]!==0)throw new Error('Unsupported original-depth query target');
  if(gl.getQuery(gl.ANY_SAMPLES_PASSED,gl.CURRENT_QUERY)||gl.getQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,gl.CURRENT_QUERY))throw new Error('Visibility query already active');
  if(!this.prepared){
   const auto=r.autoClear,shadowAuto=r.shadowMap.autoUpdate,shadowNeeds=r.shadowMap.needsUpdate;
   this.quad.layers.mask=this.camera.layers.mask;
   this.material.uniforms.rectangle.value.set(0,0,0,0);this.material.uniforms.closestDepth.value=0;this.material.uniformsNeedUpdate=true;
   try{r.autoClear=false;r.shadowMap.autoUpdate=false;r.shadowMap.needsUpdate=false;r.render(this.queryScene,this.camera);this.prepared=true;}
   finally{r.autoClear=auto;r.shadowMap.autoUpdate=shadowAuto;r.shadowMap.needsUpdate=shadowNeeds;}
  }
  if(gl.getParameter(gl.SAMPLES)!==info.samples||gl.getParameter(gl.DEPTH_BITS)!==info.depthBits)throw new Error('Snapshot query raster state changed during initialization');
  const issue=(entry:Omit<Entry,'query'|'pass'>,rectangle:number[],depth:number)=>{
   const query=gl.createQuery();if(!query)throw new Error('Cannot create visibility query');this.entries.push({...entry,query,pass});
   this.material.uniforms.rectangle.value.fromArray(rectangle);this.material.uniforms.closestDepth.value=depth;this.material.uniformsNeedUpdate=true;
   gl.beginQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,query);try{direct(this.camera,this.scene,this.geometry,this.material,this.quad,{start:0,count:6,materialIndex:0});}finally{gl.endQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE);}
  };
  const [, ,width,height]=info.viewport,matrix=new T.Matrix4();
  for(const row of this.sources){
   matrix.multiplyMatrices(this.camera.matrixWorldInverse,row.mesh.matrixWorld);
   const v=this.bounds.volume(row.mesh.geometry,matrix,this.camera.projectionMatrix,info.viewport,row.mesh.morphTargetInfluences);
   if(!v||v.right<=0||v.top<=0||v.left>=width||v.bottom>=height||v.nearDepth<=2**-18||v.nearDepth>=1)continue;
   const proof=this.certificates?queryCertificate(v,width,height):v;if(!proof)continue;
   issue({name:row.mesh.name,triangles:row.triangles,stable:row.stableFrames>=2,...(this.certificates?{meshUuid:row.mesh.uuid,volume:proof}:{})},[(proof.left-2)*2/width-1,(proof.bottom-2)*2/height-1,(proof.right+2)*2/width-1,(proof.top+2)*2/height-1],proof.nearDepth-2**-18);
  }
  const control=new T.WebGLRenderTarget(1,1,{samples:info.samples,depthBuffer:true,stencilBuffer:false});this.controls.push(control);r.setRenderTarget(control);
  if(gl.getParameter(gl.SAMPLES)!==info.samples||gl.getParameter(gl.DEPTH_BITS)!==info.depthBits)throw new Error('Control sample/depth mismatch');
  r.state.buffers.depth.setMask(true);r.state.buffers.depth.setClear(.5);r.clear(false,true,false);
  issue({controlExpected:true},[-1,-1,1,1],.25);issue({controlExpected:false},[-1,-1,1,1],.75);
  r.setRenderTarget(target);
 };
 finish(){this.submitted=true;for(const control of this.controls)control.dispose();this.controls=[];this.sources=[];}
 poll(){
  if(!this.submitted)return null;const gl=this.gl;
  if(gl.isContextLost()){this.cancel();return {summary:{error:'Context lost; original-depth queries discarded'},results:[]};}
  if(this.entries.some(row=>!gl.getQueryParameter(row.query,gl.QUERY_RESULT_AVAILABLE)))return null;
  const results=this.entries.map(({query,...row})=>({...row,anySamplesPassed:!!gl.getQueryParameter(query,gl.QUERY_RESULT)}));
  const passes=this.passes.map((info,pass)=>{const rows=results.filter(row=>row.pass===pass),controls=rows.filter(row=>row.controlExpected!==undefined),volumes=rows.filter(row=>row.controlExpected===undefined),zero=volumes.filter(row=>!row.anySamplesPassed);return {...info,queried:volumes.length,zeroVolumes:zero.length,zeroTriangles:zero.reduce((sum,row)=>sum+(row.triangles??0),0),movingZeroVolumes:zero.filter(row=>!row.stable).length,controlsPassed:controls.length===2&&controls.every(row=>row.anySamplesPassed===row.controlExpected),largestZero:[...zero].sort((a,b)=>(b.triangles??0)-(a.triangles??0)).slice(0,8)};});
  const summary={kind:'original-program-static-depth-volume-queries',initializationDraws:this.prepared?1:0,passes,controlsPassed:passes.length===3&&passes.every(p=>p.controlsPassed),queryError:gl.getError(),limits:'Actual conservative volume queries on exact-program snapshots. Potential only: no source product draw skipped, no cross-frame reuse or FPS gain established.'};
  this.cancel();return {summary,results};
 }
 cancel(){for(const row of this.entries)this.gl.deleteQuery(row.query);for(const control of this.controls)control.dispose();this.entries=[];this.controls=[];this.passes=[];this.sources=[];this.prepared=false;this.submitted=false;this.bounds.clear();}
 dispose(){if(this.disposed)return;this.disposed=true;this.cancel();this.queryScene.clear();this.geometry.dispose();this.material.dispose();}
}

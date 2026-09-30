import * as T from 'three';
import {ConservativeRasterBounds} from './conservativeRasterBounds';
import {StaticOccluderObservations,createStaticOccluderScene} from './staticOccluderScene';

/** Finite DEV experiment: depth from currently stable opaque components,
 * queried with outward screen/depth volumes. Never skips a product draw. */
export function createStaticOcclusionProbe(renderer:T.WebGLRenderer,scene:T.Scene,camera:T.Camera,host:HTMLDivElement,document:Pick<Document,'createElement'>){
 const gl=renderer.getContext() as WebGL2RenderingContext,observations=new StaticOccluderObservations(),bounds=new ConservativeRasterBounds();
 const button=document.createElement('button'),output=document.createElement('pre'),rawOutput=document.createElement('pre');
 button.textContent='统计静态车体遮挡';button.style.cssText='position:absolute;z-index:11;left:12px;top:145px;padding:7px;background:#263d32;color:white';
 output.setAttribute('aria-label','静态遮挡体诊断');output.style.cssText='position:absolute;z-index:10;left:12px;top:185px;max-width:90%;max-height:45%;overflow:auto;background:#111e;color:#ddd;padding:12px;font-size:10px;pointer-events:none';
 output.textContent='有限开发诊断；使用独立深度快照与向外扩张查询体，保留所有产品绘制。';host.appendChild(button);host.appendChild(output);
 rawOutput.style.cssText='display:none';rawOutput.setAttribute('data-static-occlusion-results','1');host.appendChild(rawOutput);
 type Row={query:WebGLQuery;samples:number;actualSamples:number;name:string;triangles:number;stableFrames:number;control?:'near-pass'|'far-fail'};
 const queries:Row[]=[],targets:T.WebGLRenderTarget[]=[];let armed=false,disposed=false,pending=false;
 let report:Record<string,unknown>={};
 const release=()=>{for(const row of queries)gl.deleteQuery(row.query);queries.length=0;for(const target of targets)target.dispose();targets.length=0;};
 button.onclick=()=>{if(disposed||pending)return;armed=true;rawOutput.textContent='';output.textContent='等待下一完整姿态的静态遮挡体快照。';};
 return {
  afterFrame(loaded:boolean,allowed:boolean){
   if(disposed||!loaded)return;
   const observation=observations.observe(scene,camera);
   if(!armed)return;armed=false;
   if(!allowed||renderer.clippingPlanes.length||renderer.capabilities.precision!=='highp'||renderer.capabilities.logarithmicDepthBuffer||renderer.capabilities.reversedDepthBuffer||gl.isContextLost()){
    output.textContent='当前显示方式或图形状态不适合该诊断，所有绘制保持原样。';return;
   }
   const start=performance.now(),width=gl.drawingBufferWidth,height=gl.drawingBufferHeight,viewport=[0,0,width,height],modelView=new T.Matrix4();
   const stable=observation.rows.filter(row=>row.stableFrames>=2),snapshot=createStaticOccluderScene(stable);
   const candidates=observation.rows.flatMap(row=>{
    modelView.multiplyMatrices(camera.matrixWorldInverse,row.mesh.matrixWorld);
    const volume=bounds.volume(row.mesh.geometry,modelView,camera.projectionMatrix,viewport,row.mesh.morphTargetInfluences);
    if(!volume||volume.nearDepth<=0||volume.nearDepth>=1||volume.right<0||volume.top<0||volume.left>width||volume.bottom>height)return [];
    return [{...row,volume}];
   });
   const queryScene=new T.Scene(),geometry=new T.PlaneGeometry(2,2),material=new T.ShaderMaterial({
    uniforms:{rectangle:{value:new T.Vector4()},closestDepth:{value:0}},
    vertexShader:'uniform vec4 rectangle; uniform float closestDepth; void main(){ vec2 p=mix(rectangle.xy,rectangle.zw,position.xy*0.5+0.5); gl_Position=vec4(p,closestDepth*2.0-1.0,1.0); }',
    fragmentShader:'void main(){gl_FragColor=vec4(1.0);}',side:T.DoubleSide,depthTest:true,depthWrite:false,depthFunc:T.LessEqualDepth,colorWrite:false,blending:T.NoBlending,
   });
   const quad=new T.Mesh(geometry,material);quad.frustumCulled=false;queryScene.add(quad);
   const previousTarget=renderer.getRenderTarget(),previousCube=renderer.getActiveCubeFace(),previousMip=renderer.getActiveMipmapLevel(),previousClear=renderer.getClearColor(new T.Color()),previousAlpha=renderer.getClearAlpha();
   const previousAuto=renderer.autoClear,previousShadowAuto=renderer.shadowMap.autoUpdate,previousShadowNeeds=renderer.shadowMap.needsUpdate;
   const previousDepthMask=!!gl.getParameter(gl.DEPTH_WRITEMASK),previousColorMask=!!gl.getParameter(gl.COLOR_WRITEMASK)[0],previousDepthClear=Number(gl.getParameter(gl.DEPTH_CLEAR_VALUE));
   const originalDraw=renderer.renderBufferDirect,before=new Uint8Array(width*height*4),after=new Uint8Array(before.length);
   renderer.setRenderTarget(null);gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,before);const beforeReadbackError=gl.getError();
   const passes:Record<string,unknown>[]=[];let currentSamples=0,actualSamples=0,error:unknown,controls=false;
   release();pending=true;
   renderer.renderBufferDirect=function(...args){
    if(args[4]!==quad)return originalDraw.apply(renderer,args);
    const items=controls?([
      {mesh:{name:'near-control'},triangles:0,stableFrames:0,control:'near-pass' as const,volume:{left:0,bottom:0,right:width,top:height,nearDepth:.25}},
      {mesh:{name:'far-control'},triangles:0,stableFrames:0,control:'far-fail' as const,volume:{left:0,bottom:0,right:width,top:height,nearDepth:.75}},
    ]):candidates.map(row=>({...row,control:undefined}));
    for(const row of items){
     if(gl.getQuery(gl.ANY_SAMPLES_PASSED,gl.CURRENT_QUERY)||gl.getQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,gl.CURRENT_QUERY))continue;
     const query=gl.createQuery();if(!query)continue;
     material.uniforms.rectangle.value.set(row.volume.left*2/width-1,row.volume.bottom*2/height-1,row.volume.right*2/width-1,row.volume.top*2/height-1);
     material.uniforms.closestDepth.value=row.volume.nearDepth;material.uniformsNeedUpdate=true;
     queries.push({query,samples:currentSamples,actualSamples,name:row.mesh.name,triangles:row.triangles,stableFrames:row.stableFrames,control:row.control});
     gl.beginQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,query);
     try{originalDraw.apply(renderer,args);}finally{gl.endQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE);}
    }
   };
   try{
    renderer.autoClear=false;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=false;renderer.setClearColor(0xffffff,1);
    for(const samples of [4,2,0]){
     currentSamples=samples;
     controls=false;
     const target=new T.WebGLRenderTarget(width,height,{samples,depthBuffer:true,stencilBuffer:false});targets.push(target);renderer.setRenderTarget(target);
     renderer.state.buffers.depth.setMask(true);renderer.clear(true,true,true);
     actualSamples=Number(gl.getParameter(gl.SAMPLES));
     const priorCalls=renderer.info.render.calls,priorTriangles=renderer.info.render.triangles;
     renderer.render(snapshot.scene,camera);
     passes.push({requestedSamples:samples,actualSamples,depthBits:Number(gl.getParameter(gl.DEPTH_BITS)),depthDraws:renderer.info.render.calls-priorCalls,depthTriangles:renderer.info.render.triangles-priorTriangles});
     renderer.render(queryScene,camera);
     // Independent positive/negative controls, after all snapshot queries.
     renderer.state.buffers.depth.setMask(true);renderer.state.buffers.depth.setClear(.5);renderer.clear(false,true,false);
     controls=true;renderer.render(queryScene,camera);renderer.state.buffers.depth.setClear(previousDepthClear);
    }
   }catch(value){error=value;pending=false;release();}
   finally{
    renderer.renderBufferDirect=originalDraw;renderer.autoClear=previousAuto;renderer.shadowMap.autoUpdate=previousShadowAuto;renderer.shadowMap.needsUpdate=previousShadowNeeds;
    renderer.state.buffers.depth.setClear(previousDepthClear);renderer.state.buffers.depth.setMask(previousDepthMask);renderer.state.buffers.color.setMask(previousColorMask);
    renderer.setClearColor(previousClear,previousAlpha);renderer.setRenderTarget(null);gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,after);
    renderer.setRenderTarget(previousTarget,previousCube,previousMip);snapshot.dispose();queryScene.clear();geometry.dispose();material.dispose();
   }
   let differentPixels=0;for(let i=0;i<before.length;i+=4)if(before[i]!==after[i]||before[i+1]!==after[i+1]||before[i+2]!==after[i+2]||before[i+3]!==after[i+3])differentPixels++;
   report={kind:'static-occluder-volume-probe',boundsMode:'correlated-corners',width,height,snapshotMeshes:observation.rows.length,stableOccluders:stable.length,movingOrNew:observation.rows.length-stable.length,unsupportedMeshes:observation.unsupported,queryCandidates:candidates.length,passes,
    snapshotAndQuerySubmitMs:performance.now()-start,beforeReadbackError,afterReadbackError:gl.getError(),displayDifferentPixels:differentPixels,
    estimatedTemporaryTargetBytes:width*height*([4,2,0].reduce((n,s)=>n+8*(s+1),0)),
    limits:'Finite isolated depth snapshot using stock normal materials and full shared geometry. No product draw skipped. Stable means two observed equal input frames only; not future immobility. Volume zero results do not yet authorize color/transmission/shadow culling, cross-frame reuse, shader precision parity or steady-state FPS gains.'};
   if(error){output.textContent=JSON.stringify({...report,error:String(error)},null,2);return;}
   output.textContent=`等待 ${queries.length} 个静态深度查询；原显示像素差 ${differentPixels}。`;
  },
  poll(){
   if(disposed||!pending)return;
   if(gl.isContextLost()){pending=false;release();output.textContent='图形上下文中断，已释放本次诊断资源。';return;}
   if(queries.some(row=>!gl.getQueryParameter(row.query,gl.QUERY_RESULT_AVAILABLE)))return;
   const results=queries.map(({query,...row})=>({...row,anySamplesPassed:!!gl.getQueryParameter(query,gl.QUERY_RESULT)}));
   const controlResults=results.filter(row=>row.control),controlsPassed=controlResults.length===6&&controlResults.every(row=>row.anySamplesPassed===(row.control==='near-pass'));
   const passes=[4,2,0].map(samples=>{const list=results.filter(row=>row.samples===samples&&!row.control),zero=list.filter(row=>!row.anySamplesPassed);return {requestedSamples:samples,queried:list.length,zeroVolumes:zero.length,zeroVolumeTriangles:zero.reduce((sum,row)=>sum+row.triangles,0),zeroStableVolumes:zero.filter(row=>row.stableFrames>=2).length,zeroMovingVolumes:zero.filter(row=>row.stableFrames<2).length};});
   const summary={...report,controlsPassed,controlResults,visibility:passes,largestZeroVolumes:results.filter(row=>!row.control&&!row.anySamplesPassed).sort((a,b)=>b.triangles-a.triangles).slice(0,24)};
   output.textContent=JSON.stringify(summary,null,2);rawOutput.textContent=JSON.stringify({...summary,results},null,2);
   pending=false;release();
  },
  dispose(){if(disposed)return;disposed=true;pending=false;armed=false;release();observations.clear();bounds.clear();button.onclick=null;button.remove();output.remove();rawOutput.remove();},
 };
}

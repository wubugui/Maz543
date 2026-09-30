import * as T from 'three';

/** One actual camera-frame diagnostic. No draw is skipped or reordered.
 * Zero samples proves only occlusion by depth written earlier in that pass;
 * it does not authorize hiding moving geometry or skipping shadow/AO draws. */
export function createOcclusionProfile(renderer:T.WebGLRenderer,scene:T.Scene,camera:T.Camera,host:HTMLDivElement,document:Pick<Document,'createElement'>,getMainTarget:()=>T.WebGLRenderTarget|null=()=>null){
  const gl=renderer.getContext() as WebGL2RenderingContext;
  const button=document.createElement('button'),output=document.createElement('pre');
  button.textContent='记录一次实体可见性';button.style.cssText='position:absolute;z-index:11;left:12px;top:145px;padding:7px;background:#263d32;color:white';
  output.setAttribute('aria-label','实体遮挡诊断');output.style.cssText='position:absolute;z-index:10;left:12px;top:185px;max-width:90%;max-height:45%;overflow:auto;background:#111e;color:#ddd;padding:12px;font-size:10px';
  output.textContent='只记录原始不透明绘制的查询结果，保留全部绘制与精度。';host.appendChild(button);host.appendChild(output);
  type Row={query:WebGLQuery;targetId:number;name:string;material:string;triangles:number;castShadow:boolean};
  type Target={id:number;kind:string;width:number;height:number;samples:number;actualSamples:number;viewport:number[];textureName:string;caller:string};
  const targets=new Map<T.WebGLRenderTarget|null,Target>();
  let armed=false,pending=false,disposed=false,unqueried=0,captureMs=0,queryError=0;
  const rows:Row[]=[];
  button.onclick=()=>{if(disposed||pending)return;armed=true;output.textContent='等待完整模型的下一帧。';};
  const release=()=>{for(const row of rows)gl.deleteQuery(row.query);rows.length=0;};
  return {
    shouldCapture(loaded:boolean){return !disposed&&armed&&loaded;},
    capture(render:()=>void){
      if(disposed||!armed){render();return;}
      armed=false;pending=true;unqueried=0;queryError=0;release();targets.clear();
      const mainTarget=getMainTarget();
      const original=renderer.renderBufferDirect,start=performance.now();
      renderer.renderBufferDirect=function(...args){
        const [passCamera,passScene,geometry,material,object,group]=args;
        const eligible=passCamera===camera&&passScene===scene&&!scene.overrideMaterial&&object instanceof T.Mesh&&object.constructor===T.Mesh&&!material.transparent&&material.depthTest&&material.depthWrite&&!(material as T.MeshStandardMaterial).wireframe;
        if(!eligible)return original.apply(this,args);
        if(gl.getQuery(gl.ANY_SAMPLES_PASSED,gl.CURRENT_QUERY)||gl.getQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,gl.CURRENT_QUERY)){unqueried++;return original.apply(this,args);}
        const query=gl.createQuery();if(!query){unqueried++;return original.apply(this,args);}
        const target=renderer.getRenderTarget();let targetInfo=targets.get(target);
        if(!targetInfo){targetInfo={id:targets.size,kind:target===mainTarget?'main-color':'auxiliary-camera',width:target?.width??gl.drawingBufferWidth,height:target?.height??gl.drawingBufferHeight,samples:target?.samples??0,actualSamples:Number(gl.getParameter(gl.SAMPLES)),viewport:Array.from(gl.getParameter(gl.VIEWPORT)),textureName:target?.texture.name??'',caller:new Error().stack??''};targets.set(target,targetInfo);}
        const count=geometry.index?.count??geometry.attributes.position.count;
        const first=Math.max(geometry.drawRange.start,group?.start??0),last=Math.min(count,geometry.drawRange.start+geometry.drawRange.count,group?group.start+group.count:Infinity);
        rows.push({query,targetId:targetInfo.id,name:object.name,material:material.name,triangles:Math.max(0,Math.floor((last-first)/3)),castShadow:object.castShadow});
        gl.beginQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,query);
        try{return original.apply(this,args);}finally{gl.endQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE);}
      };
      try{render();captureMs=performance.now()-start;queryError=gl.getError();output.textContent=`等待 ${rows.length} 个原始绘制查询完成；未跳过任何绘制。`;}
      catch(error){pending=false;release();throw error;}
      finally{renderer.renderBufferDirect=original;}
    },
    poll(){
      if(!pending||disposed)return;
      // Never request a result until it is available; never spin or gl.finish.
      if(rows.some(row=>!gl.getQueryParameter(row.query,gl.QUERY_RESULT_AVAILABLE)))return;
      const results=rows.map(row=>({targetId:row.targetId,name:row.name,material:row.material,triangles:row.triangles,castShadow:row.castShadow,anySamplesPassed:!!gl.getQueryParameter(row.query,gl.QUERY_RESULT)}));
      const hidden=results.filter(row=>!row.anySamplesPassed),sum=(list:typeof results)=>list.reduce((total,row)=>total+row.triangles,0);
      const passes=[...targets.values()].map(target=>{const all=results.filter(row=>row.targetId===target.id),zero=all.filter(row=>!row.anySamplesPassed);return {...target,draws:all.length,triangles:sum(all),zeroSampleDraws:zero.length,zeroSampleTriangles:sum(zero)};});
      output.textContent=JSON.stringify({kind:'original-camera-pass-occlusion-query',passes,draws:results.length,triangles:sum(results),zeroSampleDraws:hidden.length,zeroSampleTriangles:sum(hidden),unqueried,queryError,captureSubmitMs:captureMs,largestZeroSampleDraws:[...hidden].sort((a,b)=>b.triangles-a.triangles).slice(0,30),results,
        limits:'Unchanged opaque camera draws, separated by actual render target; may include transmission prepass. Conservative ANY_SAMPLES query may report false visibility. Zero samples is not cross-frame visibility, complete occlusion, shadow/AO eligibility, saved work, or steady-state FPS. No source or draw modified.'},null,2);
      pending=false;release();
    },
    dispose(){if(disposed)return;disposed=true;armed=false;pending=false;release();button.onclick=null;button.remove();output.remove();},
  };
}

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {measureRenderTargets} from '../lib/renderTargetTiming.ts';
const scene=new T.Scene(),camera=new T.PerspectiveCamera(),shadow=new T.OrthographicCamera(),geometry=new T.BoxGeometry(),material=new T.MeshStandardMaterial(),depthMaterial=new T.MeshDepthMaterial(),mesh=new T.Mesh(geometry,material),target=new T.WebGLRenderTarget(100,80,{samples:4});
let current=null,cube=0,mip=0,finishes=0;const trace=[];
const gl={drawingBufferWidth:100,drawingBufferHeight:80,SAMPLES:'samples',DEPTH_BITS:'depth',finish(){finishes++;},getParameter(key){return key==='samples'?(current?.samples??0):24;},getError:()=>0};
const renderer={getContext:()=>gl,getRenderTarget:()=>current,getActiveCubeFace:()=>cube,getActiveMipmapLevel:()=>mip,setRenderTarget(t,c=0,m=0){assert.equal(this,renderer);current=t;cube=c;mip=m;trace.push(['target',t,c,m]);},renderBufferDirect(...args){assert.equal(this,renderer);trace.push(['draw',...args]);}};
const originalTarget=renderer.setRenderTarget,originalDraw=renderer.renderBufferDirect;
function draw(){renderer.setRenderTarget(target);renderer.setRenderTarget(target);renderer.renderBufferDirect(shadow,null,geometry,depthMaterial,mesh,null);renderer.setRenderTarget(null);renderer.renderBufferDirect(camera,scene,geometry,material,mesh,null);}
draw();const expected=trace.slice();trace.length=0;
const result=measureRenderTargets(renderer,scene,camera,draw);assert.deepEqual(trace,expected,'All original calls and arguments preserved in order');assert.equal(renderer.setRenderTarget,originalTarget);assert.equal(renderer.renderBufferDirect,originalDraw);assert.equal(result.segments.length,3);assert.equal(finishes,4);assert.equal(result.segments[1].draws,1);assert.equal(result.segments[1].triangles,12);assert.equal(result.segments[1].kinds['shadow-depth-camera'],1);assert.equal(result.segments[2].kinds['vehicle-color'],1);assert.equal(result.segments[1].requestedSamples,4);assert.equal(result.segments[1].endFramebufferSamples,4);assert.ok(result.segments.every(row=>row.synchronizedMs>=0));
assert.throws(()=>measureRenderTargets(renderer,scene,camera,()=>{throw new Error('fixture draw failed');}),/fixture draw failed/);assert.equal(renderer.setRenderTarget,originalTarget);assert.equal(renderer.renderBufferDirect,originalDraw);
{
 const clock=globalThis.performance,finish=gl.finish,parameter=gl.getParameter;let ticks=0;
 try{globalThis.performance={now:()=>ticks};gl.finish=()=>{ticks+=2;};gl.getParameter=(key)=>{ticks+=5;return parameter(key);};
  const timed=measureRenderTargets(renderer,scene,camera,draw);assert.equal(timed.initialStateRoundTripMs,12,'Initial state round trip precedes capture');assert.equal(timed.captureMs,36);assert.equal(timed.attributedMs,36);assert.equal(timed.unattributedMs,0);assert.ok(timed.segments.every(row=>row.stateReadWaitMs===10&&row.synchronizedMs===12),'Driver-state waits belong inside each target interval');
 }finally{globalThis.performance=clock;gl.finish=finish;gl.getParameter=parameter;}
}
let sourceDisposals=0;for(const r of [geometry,material,depthMaterial,target])r.addEventListener('dispose',()=>sourceDisposals++);measureRenderTargets(renderer,scene,camera,draw);assert.equal(sourceDisposals,0);geometry.dispose();material.dispose();depthMaterial.dispose();target.dispose();
const report={passed:true,originalCallsReceiverArgumentsAndOrderPreserved:true,targetTransitionsAndDrawCountsChecked:true,shadowAndCameraClassified:true,hooksRestoredAfterSuccessAndFailure:true,sourceResourcesNotDisposed:true,limits:'Controlled transport and real Three resources. Synchronization deliberately intrusive; actual target timings and unchanged pixels require browser measurement.'};
await fs.mkdir('outputs/render-target-timing',{recursive:true});await fs.writeFile('outputs/render-target-timing/tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));

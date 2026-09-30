import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
registerHooks({
 resolve(s,c,next){if(s.endsWith('.worker?worker'))return {url:'mazmock:'+ (s.includes('mechanics')?'mechanics':'render'),shortCircuit:true};try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}},
 load(url,c,next){if(url.startsWith('mazmock:'))return {format:'module',source:`export default function(){return globalThis.__workerFactory(${JSON.stringify(url.slice(8))});}`,shortCircuit:true};return next(url,c);},
});
const {createRenderWorkerClient}=await import('../lib/renderWorkerClient.ts');
const {INITIAL}=await import('../lib/mechanics.ts');
let active;
class Target{
 listeners=new Map();
 addEventListener(type,fn){if(active.fault==='listener'&&type==='wheel')throw new Error('listener failure');let list=this.listeners.get(type);if(!list)this.listeners.set(type,list=new Set());list.add(fn);}
 removeEventListener(type,fn){this.listeners.get(type)?.delete(fn);}
 emit(type,event={}){for(const fn of this.listeners.get(type)??[])fn({type,...event});}
 get listenerCount(){return [...this.listeners.values()].reduce((sum,list)=>sum+list.size,0);}
}
class Element extends Target{
 style={};dataset={};children=[];captures=new Set();clientWidth=1212;clientHeight=773;onclick=null;
 constructor(tag){super();this.tag=tag;active.nodes.push(this);}
 appendChild(node){this.children.push(node);node.parent=this;return node;}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(node=>node!==this);this.parent=null;}
 setAttribute(){}
 getBoundingClientRect(){return {left:17.125,top:69.75};}
 setPointerCapture(id){this.captures.add(id);}
 hasPointerCapture(id){return this.captures.has(id);}
 releasePointerCapture(id){this.captures.delete(id);}
 transferControlToOffscreen(){if(active.fault==='transfer')throw new Error('transfer failure');return {};}
}
function fixture(fault){
 const f=active={fault,nodes:[],workers:[],ports:[],observers:[],frames:new Map(),timers:new Map(),errors:[],next:0};
 globalThis.document=Object.assign(new Target(),{hidden:false,createElement:tag=>new Element(tag)});
 globalThis.window=Object.assign(new Target(),{innerWidth:1552,devicePixelRatio:1.75,location:{search:'?render-worker=1'}});
 globalThis.requestAnimationFrame=fn=>{const id=f.next++;f.frames.set(id,fn);return id;};
 globalThis.cancelAnimationFrame=id=>f.frames.delete(id);
 globalThis.setTimeout=(fn,ms)=>{const id=f.next++;f.timers.set(id,{fn,ms});return id;};
 globalThis.clearTimeout=id=>f.timers.delete(id);
 globalThis.MessageChannel=class{
  constructor(){if(fault==='channel')throw new Error('channel failure');this.port1={closed:0,close(){this.closed++;}};this.port2={closed:0,close(){this.closed++;}};f.ports.push(this.port1,this.port2);}
 };
 globalThis.ResizeObserver=class{
  disconnected=0;
  constructor(callback){this.callback=callback;f.observers.push(this);}
  observe(){if(fault==='observe')throw new Error('observe failure');}
  disconnect(){this.disconnected++;}
 };
 globalThis.__workerFactory=kind=>{
  if(fault===kind+'-constructor')throw new Error(kind+' constructor failure');
  const worker={kind,messages:[],terminated:0,onmessage:null,onerror:null,onmessageerror:null,
   postMessage(data,transfer){if(f.fault===kind+'-'+data.type)throw new Error(kind+' '+data.type+' failure');this.messages.push({data,transfer});},
   terminate(){this.terminated++;},
   emit(data){this.onmessage?.({data});},
  };f.workers.push(worker);return worker;
 };
 f.host=new Element('host');f.unrelated=new Element('unrelated');f.host.appendChild(f.unrelated);
 f.bindings={host:f.host,latest:{current:structuredClone(INITIAL)},selection:{current:''},callbacks:{current:{onReady(){},onSelect(){},onTelemetry(){},onError(message){f.errors.push(message);}}},api:{current:null},simulationWorker:{current:null},simulationGeneration:{current:0}};
 f.render=()=>f.workers.find(worker=>worker.kind==='render');f.mechanics=()=>f.workers.find(worker=>worker.kind==='mechanics');
 return f;
}
function clean(f,{renderStopped=true,preserveApi=false}={}){
 assert.deepEqual(f.host.children,[f.unrelated],'only owned DOM removed');
 for(const node of f.nodes){assert.equal(node.listenerCount,0);assert.equal(node.captures.size,0);}
 assert.equal(document.listenerCount,0);assert.equal(window.listenerCount,0);
 assert.equal(f.frames.size,0);
 for(const observer of f.observers)assert.equal(observer.disconnected,1);
 for(const port of f.ports)assert.equal(port.closed,1);
 for(const worker of f.workers)assert.equal(worker.terminated,worker.kind==='render'&&!renderStopped?0:1,`${worker.kind} ownership`);
 if(!preserveApi)assert.equal(f.bindings.api.current,null);
}
const failures=[];
for(const fault of ['render-constructor','mechanics-constructor','channel','transfer','listener','observe','mechanics-reset','mechanics-connect-renderer','render-init']){
 const f=fixture(fault);assert.throws(()=>createRenderWorkerClient(f.bindings),/failure/);clean(f);assert.equal(f.timers.size,0);failures.push(fault);
}
// Normal handoff: physics/listeners/RAF/DOM stop now, render context gets a
// bounded chance to dispose; its acknowledgement cancels only its own timer.
{
 const f=fixture(),client=createRenderWorkerClient(f.bindings),render=f.render(),canvas=f.nodes.find(node=>node.tag==='canvas');
 assert.equal(render.messages[0].transfer.length,2);assert.equal(f.mechanics().messages[1].transfer.length,1);
 render.emit({type:'dom',commands:[{op:'create',id:4,tag:'button'},{op:'append',id:4}]});
 render.emit({type:'frame-request',id:12});assert.equal(f.frames.size,1);
 canvas.emit('pointerdown',{pointerId:17,clientX:317.125,clientY:269.75});assert.ok(canvas.hasPointerCapture(17));
 const forwarded=render.messages.find(message=>message.data.type==='input').data.event;assert.equal(forwarded.clientX,317.125);assert.equal(forwarded.clientY,269.75);
 const pending=f.bindings.api.current.exportModel(),rejection=assert.rejects(pending,/已关闭/);
 client.dispose();await rejection;clean(f,{renderStopped:false});assert.equal(f.timers.size,1);
 render.emit({type:'disposed'});clean(f);assert.equal(f.timers.size,0);client.dispose();clean(f);
}
// The bounded shutdown timer and a failed shutdown message both terminate the
// owned renderer once. They cannot clear a replacement viewport's API.
for(const mode of ['timeout','dispose-post-failure']){
 const f=fixture(),client=createRenderWorkerClient(f.bindings),replacement={tag:'replacement'};
 f.bindings.api.current=replacement;if(mode==='dispose-post-failure')f.fault='render-dispose';
 const originalWarn=console.warn;console.warn=()=>{};try{client.dispose();}finally{console.warn=originalWarn;}
 if(mode==='timeout'){const [id,timer]=[...f.timers][0];assert.equal(timer.ms,10000);f.timers.delete(id);timer.fn();}
 clean(f,{preserveApi:true});assert.equal(f.bindings.api.current,replacement);assert.equal(f.timers.size,0);
}
const fatalCases=['render-error','mechanics-error','render-messageerror','mechanics-messageerror','fatal-message','unexpected-disposed','unsupported-overlay','render-state','mechanics-controls'];
for(const fault of fatalCases){
 const f=fixture(),client=createRenderWorkerClient(f.bindings),render=f.render(),mechanics=f.mechanics();
 const pending=f.bindings.api.current.exportModel(),rejection=assert.rejects(pending);
 const lateMessage=render.onmessage;
 if(fault==='render-error')render.onerror({message:'render crashed'});
 else if(fault==='mechanics-error')mechanics.onerror({message:'mechanics crashed'});
 else if(fault==='render-messageerror')render.onmessageerror({});
 else if(fault==='mechanics-messageerror')mechanics.onmessageerror({});
 else if(fault==='fatal-message')render.emit({type:'fatal',message:'init failed'});
 else if(fault==='unexpected-disposed')render.emit({type:'disposed'});
 else if(fault==='unsupported-overlay')render.emit({type:'dom',commands:[{op:'create',id:5,tag:'iframe'}]});
 else{f.fault=fault;client.update();}
 await rejection;clean(f);assert.equal(f.errors.length,1);assert.equal(f.timers.size,0);
 lateMessage({data:{type:'dom',commands:[{op:'create',id:99,tag:'button'},{op:'append',id:99}]}});
 client.update();client.dispose();clean(f);assert.equal(f.errors.length,1,'late messages and disposal cannot revive failed clients');
}
const report={passed:true,synchronousRollback:failures,fatalCleanup:fatalCases,normalDisposeAcknowledged:true,boundedShutdown:true,failedShutdownPost:true,sharedHostPreserved:true,replacementApiPreserved:true,pendingExportRejected:true,lateMessagesIgnored:true,fractionalInputRetained:true,limits:'Fault injection runs the actual client with deterministic browser/Worker mocks; full browser lifecycle and GPU context recovery require separate evidence.'};
await fs.mkdir('outputs/worker-lifecycle',{recursive:true});await fs.writeFile('outputs/worker-lifecycle/client-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));

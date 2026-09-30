import RenderWorker from './viewport.worker?worker';
import MechanicalWorker from './mechanics.worker?worker';
import {INITIAL,type Telemetry} from './mechanics';
import type {ViewportBindings} from './vehicleViewport';
import type {DomCommand,InputPayload,RenderInput,RenderOutput,ViewportMetrics} from './viewportProtocol';

/** Main-thread owner of the canvas and overlays. It forwards input/RAF only;
 * all Three objects, original geometry, rendering and export stay in worker. */
export function createRenderWorkerClient({host,latest,selection,callbacks,api}:ViewportBindings){
  const canvas=document.createElement('canvas');canvas.style.width='100%';canvas.style.height='100%';canvas.style.touchAction='none';
  let worker:Worker|undefined,mechanics:Worker|undefined,channel:MessageChannel|undefined,observer:ResizeObserver|undefined;
  let disposed=false,nextCall=1,shutdownTimer:ReturnType<typeof setTimeout>|undefined;
  let workerTerminated=false,ownedApi:typeof api.current=null;
  let generation=1,lastTelemetry=0,renderStats:Telemetry['renderStats'],viewScale:Telemetry['viewScale'];
  const elements=new Map<number,HTMLElement>([[0,canvas]]),raf=new Map<number,number>();
  const pending=new Map<number,{resolve:()=>void;reject:(error:Error)=>void}>();
  const cleanups:(()=>void)[]=[];
  const pointers=new Set<number>();
  const cleanupErrors:unknown[]=[];
  const safely=(action:()=>void)=>{try{action();}catch(error){cleanupErrors.push(error);}};
  const terminateRenderer=()=>{
    if(workerTerminated)return;workerTerminated=true;
    if(shutdownTimer!==undefined){clearTimeout(shutdownTimer);shutdownTimer=undefined;}
    if(worker){worker.onmessage=null;worker.onerror=null;worker.onmessageerror=null;safely(()=>worker!.terminate());}
  };
  const rejectPending=(message:string)=>{for(const call of pending.values())call.reject(new Error(message));pending.clear();};
  const stop=(immediate:boolean,message='三维运行时已关闭')=>{
    if(disposed)return;disposed=true;if(api.current===ownedApi)api.current=null;
    if(mechanics){mechanics.onmessage=null;mechanics.onerror=null;mechanics.onmessageerror=null;safely(()=>mechanics!.terminate());}
    if(observer)safely(()=>observer!.disconnect());
    for(const cleanup of cleanups)safely(cleanup);cleanups.length=0;
    for(const id of pointers)safely(()=>{if(canvas.hasPointerCapture(id))canvas.releasePointerCapture(id);});pointers.clear();
    raf.forEach(handle=>safely(()=>cancelAnimationFrame(handle)));raf.clear();
    elements.forEach(element=>safely(()=>{element.onclick=null;element.remove();}));elements.clear();
    if(channel){safely(()=>channel!.port1.close());safely(()=>channel!.port2.close());}
    rejectPending(message);
    if(immediate||!worker)terminateRenderer();
    else{
      // Only this component-owned worker is terminated. Normal unmount allows
      // its renderer to release GPU resources; a dead worker cannot acknowledge.
      shutdownTimer=setTimeout(terminateRenderer,10000);
      try{worker.postMessage({type:'dispose'} satisfies RenderInput);}catch(error){cleanupErrors.push(error);terminateRenderer();}
    }
    if(cleanupErrors.length)console.warn('MAZ viewport cleanup:',cleanupErrors);
  };
  const fail=(message:string)=>{if(disposed)return;stop(true,message);callbacks.current.onError(message);};
  const send=(data:RenderInput)=>{if(!disposed)try{worker!.postMessage(data);}catch(error){fail(`独立三维显示通信失败：${String(error)}`);}};
  const sendMechanics=(data:unknown)=>{if(!disposed)try{mechanics!.postMessage(data);}catch(error){fail(`独立机械计算通信失败：${String(error)}`);}};
  const metrics=():ViewportMetrics=>{const rect=canvas.getBoundingClientRect();return {width:host.clientWidth,height:host.clientHeight,left:rect.left,top:rect.top,innerWidth:window.innerWidth,devicePixelRatio:window.devicePixelRatio};};
  const apply=(command:DomCommand)=>{
    if(command.op==='create'){
      if(!['button','pre','a'].includes(command.tag))throw new Error(`Unsupported viewport element: ${command.tag}`);
      const element=document.createElement(command.tag);elements.set(command.id,element);
      if(command.tag==='button')element.onclick=()=>send({type:'click',id:command.id});return;
    }
    const element=elements.get(command.id);if(!element)return;
    if(command.op==='append')host.appendChild(element);
    else if(command.op==='remove'){element.remove();elements.delete(command.id);}
    else if(command.op==='click')element.click();
    else if(command.op==='set'){
      if(command.field==='style')Reflect.set(element.style,command.key,command.value);
      else if(command.field==='dataset')element.dataset[command.key]=command.value;
      else if(command.field==='attribute')element.setAttribute(command.key,command.value);
      else if(['className','textContent','href','download'].includes(command.key))Reflect.set(element,command.key,command.value);
    }
  };
  try{
  host.appendChild(canvas);
  worker=new RenderWorker();mechanics=new MechanicalWorker();channel=new MessageChannel();
  const offscreen=canvas.transferControlToOffscreen();
  worker.onmessage=({data}:MessageEvent<RenderOutput>)=>{
    if(data.type==='disposed'){if(disposed)terminateRenderer();else fail('独立三维显示意外关闭');return;}
    if(disposed)return;
    try{
    switch(data.type){
      case 'dom':for(const command of data.commands)apply(command);break;
      case 'frame-request':raf.set(data.id,requestAnimationFrame(()=>{raf.delete(data.id);send({type:'frame',id:data.id});}));break;
      case 'frame-cancel':{const handle=raf.get(data.id);if(handle!==undefined)cancelAnimationFrame(handle);raf.delete(data.id);break;}
      case 'ready':callbacks.current.onReady(data.parts,data.count);break;
      case 'select':callbacks.current.onSelect(data.id);break;
      case 'telemetry':renderStats=data.telemetry.renderStats;viewScale=data.telemetry.viewScale;break;
      case 'error':callbacks.current.onError(data.message);break;
      case 'fatal':fail(data.message);break;
      case 'export-progress':if(process.env.NODE_ENV==='development')console.info('MAZ worker export:',data.stage);break;
      case 'api-result':{const call=pending.get(data.id);pending.delete(data.id);if(data.error)call?.reject(new Error(data.error));else call?.resolve();break;}
    }
    }catch(error){fail(`独立三维显示消息处理失败：${String(error)}`);}
  };
  worker.onerror=event=>fail(`独立三维显示无法运行：${event.message}`);
  worker.onmessageerror=()=>fail('独立三维显示消息无法解码');
  mechanics.onmessage=({data})=>{
    if(disposed||data.type!=='state'||data.generation!==generation)return;
    const now=performance.now();if(now-lastTelemetry>150){lastTelemetry=now;callbacks.current.onTelemetry({...data.telemetry,renderStats,viewScale});}
  };
  mechanics.onerror=event=>fail(`独立机械计算无法运行：${event.message}`);
  mechanics.onmessageerror=()=>fail('独立机械计算消息无法解码');
  const listen=(target:EventTarget,type:string,fn:(event:any)=>void,options?:AddEventListenerOptions)=>{target.addEventListener(type,fn,options);cleanups.push(()=>target.removeEventListener(type,fn,options));};
  const input=(target:'canvas'|'document',event:Event)=>{
    const payload:InputPayload={type:event.type};
    for(const key of ['pointerId','pointerType','clientX','clientY','pageX','pageY','button','buttons','ctrlKey','metaKey','shiftKey','altKey','deltaX','deltaY','deltaZ','deltaMode','code','key','repeat']){
      const value=Reflect.get(event,key);if(['number','string','boolean'].includes(typeof value))payload[key]=value;
    }
    send({type:'input',target,event:payload,metrics:metrics()});
  };
  listen(canvas,'pointerdown',(event:PointerEvent)=>{pointers.add(event.pointerId);canvas.setPointerCapture(event.pointerId);input('canvas',event);});
  // Match DOM ordering: the canvas selection listener runs before document's
  // OrbitControls pointerup listener. No pointer samples are rounded/dropped.
  listen(canvas,'pointerup',(event:PointerEvent)=>input('canvas',event));
  listen(canvas,'pointercancel',(event:PointerEvent)=>input('canvas',event));
  listen(document,'pointermove',(event:PointerEvent)=>{if(pointers.has(event.pointerId))input('document',event);});
  const endPointer=(event:PointerEvent)=>{if(!pointers.delete(event.pointerId))return;input('document',event);if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);};
  listen(document,'pointerup',endPointer);listen(document,'pointercancel',endPointer);
  listen(canvas,'wheel',(event:WheelEvent)=>{event.preventDefault();input('canvas',event);},{passive:false});
  listen(canvas,'contextmenu',(event:Event)=>{event.preventDefault();input('canvas',event);});
  for(const type of ['keydown','keyup'])listen(document,type,(event:KeyboardEvent)=>input('document',event),{capture:true});
  listen(document,'visibilitychange',()=>{sendMechanics({type:'pause',generation,paused:document.hidden});send({type:'visibility',hidden:document.hidden});});
  observer=new ResizeObserver(()=>send({type:'size',metrics:metrics()}));observer.observe(host);
  listen(window,'resize',()=>send({type:'size',metrics:metrics()}));
  const call=(method:'view'|'focus'|'reset'|'exportModel',arg?:string)=>new Promise<void>((resolve,reject)=>{
    if(disposed){reject(new Error('三维运行时已关闭'));return;}const id=nextCall++;pending.set(id,{resolve,reject});send({type:'api',id,method,arg});
  });
  const invoke=(method:'view'|'focus'|'reset',arg?:string)=>{void call(method,arg).catch(error=>{if(!disposed)callbacks.current.onError(String(error));});};
  ownedApi={view:name=>invoke('view',name),focus:id=>invoke('focus',id),reset:()=>{if(disposed)return;generation++;sendMechanics({type:'reset',generation,controls:INITIAL,paused:document.hidden});invoke('reset');},exportModel:()=>call('exportModel')};api.current=ownedApi;
  mechanics.postMessage({type:'reset',generation,controls:latest.current,paused:document.hidden});
  mechanics.postMessage({type:'connect-renderer',port:channel.port1},[channel.port1]);
  worker.postMessage({type:'init',canvas:offscreen,simulation:channel.port2,metrics:metrics(),hidden:document.hidden,search:window.location.search,controls:latest.current,selection:selection.current} satisfies RenderInput,[offscreen,channel.port2]);
  return {
    update(){if(disposed)return;sendMechanics({type:'controls',controls:latest.current,generation});send({type:'state',controls:latest.current,selection:selection.current});},
    dispose(){stop(false);},
  };
  }catch(error){stop(true);throw error;}
}

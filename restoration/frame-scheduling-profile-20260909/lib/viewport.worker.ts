import {createVehicleViewport,type ViewerAPI} from './vehicleViewport';
import {createWorkerViewportHost} from './workerViewportHost';
import type {RenderInput,RenderOutput} from './viewportProtocol';
import type {Controls} from './mechanics';
import type {SimulationConnection} from './viewportEnvironment';

const scope=globalThis as unknown as {onmessage:((event:MessageEvent<RenderInput>)=>void)|null;postMessage:(data:RenderOutput)=>void};
const send=(data:RenderOutput)=>scope.postMessage(data);
const latest={current:null as unknown as Controls},selection={current:''},api={current:null as ViewerAPI|null};
const simulationWorker={current:null as SimulationConnection|null},simulationGeneration={current:0};
let host:ReturnType<typeof createWorkerViewportHost>|undefined,dispose:(()=>void)|undefined;
scope.onmessage=async({data})=>{
  try{
    switch(data.type){
      case 'init':{
        latest.current=data.controls;selection.current=data.selection;
        const useNativeFrames=process.env.NODE_ENV==='development'&&new URLSearchParams(data.search).get('native-raf')==='1';
        const nativeFrames=useNativeFrames&&typeof globalThis.requestAnimationFrame==='function'&&typeof globalThis.cancelAnimationFrame==='function'?{request:globalThis.requestAnimationFrame.bind(globalThis),cancel:globalThis.cancelAnimationFrame.bind(globalThis)}:undefined;
        host=createWorkerViewportHost(data.canvas,data.metrics,data.hidden,data.search,send,nativeFrames);
        // Main thread owns physics controls/reset/visibility directly. Drawing
        // cannot delay these commands or the inspector's live instrumentation.
        const port=data.simulation;
        const connection:SimulationConnection={onmessage:null,onerror:null,postMessage(){},terminate(){port.close();}};
        port.onmessage=event=>connection.onmessage?.call(connection as Worker,event);
        host.environment.createSimulation=()=>connection;
        dispose=createVehicleViewport({host:host.host,environment:host.environment,latest,selection,api,simulationWorker,simulationGeneration,callbacks:{current:{
          onReady:(parts,count)=>send({type:'ready',parts:parts.map(part=>{const {group,...metadata}=part as typeof part&{group?:unknown};return metadata;}),count}),
          onSelect:id=>send({type:'select',id}),onTelemetry:telemetry=>send({type:'telemetry',telemetry}),onError:message=>send({type:'error',message}),
          onExportProgress:stage=>send({type:'export-progress',stage}),
        }}});
        break;
      }
      case 'state':latest.current=data.controls;selection.current=data.selection;simulationWorker.current?.postMessage({type:'controls',controls:data.controls,generation:simulationGeneration.current});break;
      case 'size':host?.updateMetrics(data.metrics);break;
      case 'visibility':host?.visibility(data.hidden);break;
      case 'input':host?.updateMetrics(data.metrics);host?.input(data.target,data.event);break;
      case 'click':host?.click(data.id);break;
      case 'frame':host?.frame(data.id);break;
      case 'api':{
        try{if(!api.current)throw new Error('三维运行时尚未就绪');
          if(data.method==='exportModel'){
            if(process.env.NODE_ENV==='development'){const {probeWorkerExportTransport}=await import('./exportTransportProbe');probeWorkerExportTransport(stage=>send({type:'export-progress',stage}));}
            await api.current.exportModel();
          }
          else if(data.method==='reset')api.current.reset();else api.current[data.method](data.arg??'');
          host?.flush();send({type:'api-result',id:data.id});
        }catch(error){send({type:'api-result',id:data.id,error:String(error)});}
        break;
      }
      case 'dispose':try{dispose?.();}finally{simulationWorker.current?.terminate();host?.flush();send({type:'disposed'});}break;
    }
  }catch(error){send({type:'error',message:`独立三维显示错误：${error instanceof Error?error.stack||error.message:String(error)}`});}
};

'use client';
import {useEffect,useRef,type RefObject} from 'react';
import {createVehicleViewport,type ViewerAPI} from '@/lib/vehicleViewport';
import {createRenderWorkerClient} from '@/lib/renderWorkerClient';
import type {PartSummary} from '@/lib/viewportProtocol';
import type {Controls,Telemetry} from '@/lib/mechanics';
export type {ViewerAPI} from '@/lib/vehicleViewport';
type Props={state:Controls;selected:string;api:RefObject<ViewerAPI|null>;onReady:(parts:PartSummary[],count:number)=>void;onSelect:(id:string)=>void;onTelemetry:(t:Telemetry)=>void;onError:(s:string)=>void};
export default function VehicleViewer({state,selected,api,onReady,onSelect,onTelemetry,onError}:Props){
  const container=useRef<HTMLDivElement>(null),latest=useRef(state),selection=useRef(selected);
  const simulationWorker=useRef<Worker|null>(null),simulationGeneration=useRef(0);
  const renderClient=useRef<ReturnType<typeof createRenderWorkerClient>|null>(null);
  const callbacks=useRef({onReady,onSelect,onTelemetry,onError});
  useEffect(()=>{latest.current=state;selection.current=selected;callbacks.current={onReady,onSelect,onTelemetry,onError};renderClient.current?.update();simulationWorker.current?.postMessage({type:'controls',controls:state,generation:simulationGeneration.current});},[state,selected,onReady,onSelect,onTelemetry,onError]);
  useEffect(()=>{
    if(!container.current)return;
    const bindings={host:container.current,latest,selection,callbacks,api,simulationWorker,simulationGeneration};
    // Keep experimental until full-size drawing, picking and export are verified.
    if(process.env.NODE_ENV==='development'&&new URLSearchParams(location.search).get('render-worker')==='1'){
      try{
        if(!HTMLCanvasElement.prototype.transferControlToOffscreen)throw new Error('浏览器不支持 OffscreenCanvas');
        const client=createRenderWorkerClient(bindings);renderClient.current=client;
        return ()=>{renderClient.current=null;client.dispose();};
      }catch(error){
        // A transferred canvas cannot be reused. The failed client has removed
        // its canvas/workers/listeners; the original renderer creates its own.
        // Do not silently restart mechanics after an asynchronous runtime error.
        callbacks.current.onError(`独立显示启动失败，已回到普通显示：${String(error)}`);
      }
    }
    return createVehicleViewport(bindings);
  },[api]);
  return <div className="three-surface" ref={container}/>;
}

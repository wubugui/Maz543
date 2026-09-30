'use client';
import {useEffect,useRef,type RefObject} from 'react';
import {createVehicleViewport,type ViewerAPI} from '@/lib/vehicleViewport';
import {createRenderWorkerClient} from '@/lib/renderWorkerClient';
import {productionWorkerFixture,productionWorkerFixtureIdentity} from '@/lib/productionWorkerFixture';
import {createViewportLifecycleAudit} from '@/lib/viewportLifecycleAudit';
import {bindViewportDocumentLifetime} from '@/lib/viewportDocumentLifetime';
import type {PartSummary} from '@/lib/viewportProtocol';
import type {Controls,Telemetry} from '@/lib/mechanics';
export type {ViewerAPI} from '@/lib/vehicleViewport';
type Props={state:Controls;selected:string;api:RefObject<ViewerAPI|null>;onReady:(parts:PartSummary[],count:number)=>void;onSelect:(id:string)=>void;onTelemetry:(t:Telemetry)=>void;onError:(s:string)=>void};
export default function VehicleViewer({state,selected,api,onReady,onSelect,onTelemetry,onError}:Props){
  const container=useRef<HTMLDivElement>(null),latest=useRef(state),selection=useRef(selected);
  const simulationWorker=useRef<Worker|null>(null),simulationGeneration=useRef(0);
  const renderClient=useRef<ReturnType<typeof createRenderWorkerClient>|null>(null);
  const lifecycle=useRef<ReturnType<typeof createViewportLifecycleAudit>>(null);
  const callbacks=useRef({onReady,onSelect,onTelemetry,onError});
  useEffect(()=>{latest.current=state;selection.current=selected;callbacks.current={onReady:(parts,count)=>{lifecycle.current?.record('native-ready',{count});onReady(parts,count);},onSelect,onTelemetry:t=>{lifecycle.current?.setTelemetry(t);onTelemetry(t);},onError};renderClient.current?.update();simulationWorker.current?.postMessage({type:'controls',controls:state,generation:simulationGeneration.current});},[state,selected,onReady,onSelect,onTelemetry,onError]);
  useEffect(()=>{
    if(!container.current)return;
    const audit=createViewportLifecycleAudit(container.current);lifecycle.current=audit;
    const bindings={host:container.current,latest,selection,callbacks,api,simulationWorker,simulationGeneration,lifecycle:audit?.record};
    // Keep experimental until full-size drawing, picking and export are verified.
    const builtWorker=process.env.NODE_ENV==='development'&&new URLSearchParams(location.search).get('worker-build')==='1';
    if(process.env.NODE_ENV==='development'&&(new URLSearchParams(location.search).get('render-worker')==='1'||builtWorker)){
      try{
        if(!HTMLCanvasElement.prototype.transferControlToOffscreen)throw new Error('浏览器不支持 OffscreenCanvas');
        const client=createRenderWorkerClient(bindings,builtWorker?productionWorkerFixture:undefined);renderClient.current=client;
        if(builtWorker)container.current.dataset.workerBuildAudit=productionWorkerFixtureIdentity;
        return bindViewportDocumentLifetime(window,()=>{audit?.record('viewer-effect-cleanup',{mode:'worker'});renderClient.current=null;try{client.dispose();}finally{audit?.dispose();lifecycle.current=null;}},audit?.record);
      }catch(error){
        // A transferred canvas cannot be reused. The failed client has removed
        // its canvas/workers/listeners; the original renderer creates its own.
        // Do not silently restart mechanics after an asynchronous runtime error.
        callbacks.current.onError(`独立显示启动失败，已回到普通显示：${String(error)}`);
      }
    }
    try{const dispose=createVehicleViewport(bindings);return bindViewportDocumentLifetime(window,()=>{audit?.record('viewer-effect-cleanup',{mode:'main'});try{dispose?.();audit?.record('main-viewport-disposed');}finally{audit?.dispose();lifecycle.current=null;}},audit?.record);}
    catch(error){audit?.record('main-viewport-create-failed',{error:String(error)});audit?.dispose();lifecycle.current=null;throw error;}
  },[api]);
  return <div className="three-surface" ref={container}/>;
}

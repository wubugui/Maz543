import type {BufferGeometry} from 'three';
import type {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';

type DecoderWorker=Worker&{_callbacks:Record<string,{reject:(error:unknown)=>void}>};
type Implementation=DRACOLoader&{
  _initDecoder:()=>Promise<void>;
  _getWorker:(taskID:number,taskCost:number)=>Promise<DecoderWorker>;
  decodeGeometry:(buffer:ArrayBuffer,config:unknown)=>Promise<BufferGeometry>;
  workerPool:DecoderWorker[];
};

/** Per-instance r183 lifecycle guard. Stock dispose() does not cancel pending
 * decoder initialization or reject in-flight decode callbacks. A late library
 * fetch can otherwise create a new decoder Worker after viewport unmount.
 * No codec, attributes, quantization, task order or worker limit is changed.
 * These narrow internal interfaces must be revalidated on a Three upgrade. */
export function protectDracoLifetime(loader:DRACOLoader){
  const source=loader as Implementation;
  for(const method of ['_initDecoder','_getWorker','decodeGeometry'] as const)if(typeof source[method]!=='function')throw new Error(`Unsupported Draco lifecycle interface: ${method}`);
  if(!Array.isArray(source.workerPool))throw new Error('Unsupported Draco worker ownership interface');
  const originalInit=source._initDecoder,originalWorker=source._getWorker,originalDecode=source.decodeGeometry,originalDispose=source.dispose;
  const pending=new Set<(error:unknown)=>void>(),guardedWorkers=new WeakSet<DecoderWorker>();let closed=false;
  const cancellation=Object.assign(new Error('The owning viewport has closed; Draco decoding was cancelled.'),{name:'AbortError'});
  const stopWorkers=()=>{
    for(const worker of source.workerPool){
      // Settle the stock promises too, so parser/attribute buffers are not held
      // by callbacks waiting forever for a terminated decoder.
      for(const callback of Object.values(worker._callbacks))callback.reject(cancellation);
      worker.onmessage=null;
    }
    originalDispose.call(source);
  };
  source._initDecoder=function(){
    if(closed)return Promise.reject(cancellation);
    return originalInit.call(source).then(()=>{
      if(closed){stopWorkers();throw cancellation;} // Also revoke a late-created source Blob URL.
    });
  };
  source._getWorker=function(id,cost){
    if(closed)return Promise.reject(cancellation);
    return originalWorker.call(source,id,cost).then(worker=>{
      if(closed){stopWorkers();throw cancellation;}
      if(!guardedWorkers.has(worker)){
        const post=worker.postMessage;
        worker.postMessage=function(...args:[message:unknown,transferOrOptions?:Transferable[]|StructuredSerializeOptions]){
          // Disposal may occur in a microtask between _getWorker resolving and
          // stock decodeGeometry registering/posting its task. Throwing here
          // settles that stock promise instead of posting to a dead Worker.
          if(closed)throw cancellation;
          return Reflect.apply(post,worker,args);
        };
        guardedWorkers.add(worker);
      }
      return worker;
    });
  };
  source.decodeGeometry=function(buffer,config){
    if(closed)return Promise.reject(cancellation);
    return new Promise((resolve,reject)=>{
      pending.add(reject);
      let task:Promise<BufferGeometry>;
      try{task=originalDecode.call(source,buffer,config);}catch(error){pending.delete(reject);reject(error);return;}
      task.then(geometry=>{
        pending.delete(reject);
        if(closed){geometry.dispose();reject(cancellation);}else resolve(geometry);
      },error=>{pending.delete(reject);reject(error);});
    });
  };
  source.dispose=function(){
    if(closed)return source;
    closed=true;for(const reject of pending)reject(cancellation);pending.clear();stopWorkers();return source;
  };
  return {loader,get closed(){return closed;},get pendingDecodes(){return pending.size;}};
}

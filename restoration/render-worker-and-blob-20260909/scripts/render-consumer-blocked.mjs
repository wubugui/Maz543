import {parentPort} from 'node:worker_threads';
parentPort.on('message',data=>{
  if(data.type==='port')data.port.on('message',state=>parentPort.postMessage({type:'render-state',state}));
  if(data.type==='block'){
    parentPort.postMessage({type:'blocked'});
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,2000);
    parentPort.postMessage({type:'unblocked'});
  }
});

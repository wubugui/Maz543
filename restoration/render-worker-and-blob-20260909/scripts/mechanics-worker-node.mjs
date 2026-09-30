import {parentPort} from 'node:worker_threads';
import {registerHooks} from 'node:module';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
globalThis.postMessage=data=>parentPort.postMessage(data);
parentPort.on('message',data=>globalThis.onmessage?.({data}));
await import('../lib/mechanics.worker.ts');

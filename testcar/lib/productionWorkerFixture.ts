import type {RenderWorkerFactories} from './renderWorkerClient';

/** Generated DEV acceptance entry; the script verifies actual HTTP bytes. */
export const productionWorkerFixture:RenderWorkerFactories={
 render:()=>new Worker('/__worker-validation/viewport.worker-D81fNBfT.js',{name:'MAZ production render acceptance'}),
 mechanics:()=>new Worker('/__worker-validation/mechanics.worker-txGZjy8K.js',{name:'MAZ production mechanics acceptance'}),
};
export const productionWorkerFixtureIdentity="viewport.worker-D81fNBfT.js + mechanics.worker-txGZjy8K.js";

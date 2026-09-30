import {MechanicalTimeline,MECHANICAL_HZ} from './mechanicalTimeline';
import {INITIAL,type Controls} from './mechanics';

type Input={type:'reset';controls:Controls;paused:boolean;generation:number}|{type:'controls';controls:Controls;generation:number}|{type:'pause';paused:boolean;generation:number}|{type:'connect-renderer';port:MessagePort};
const scope=globalThis as unknown as {onmessage:((event:MessageEvent<Input>)=>void)|null;postMessage:(data:unknown)=>void};
let timeline=new MechanicalTimeline(performance.now(),INITIAL),generation=0,lastPublishedTick=-1;
let renderPort:MessagePort|undefined;
scope.onmessage=({data})=>{
  const now=performance.now();
  if(data.type==='connect-renderer'){
    renderPort?.close();renderPort=data.port;lastPublishedTick=-1;
  }else if(data.type==='reset'){
    generation=data.generation;timeline=new MechanicalTimeline(now,data.controls);timeline.setPaused(data.paused,now);lastPublishedTick=-1;
  }else if(data.generation===generation){
    if(data.type==='controls')timeline.setControls(data.controls,now);
    else timeline.setPaused(data.paused,now);
  }
};
function pulse(){
  const now=performance.now(),result=timeline.advanceTo(now);
  // Publish every completed solver tick, not a lower animation update rate.
  // The renderer samples the latest exact state whenever it can draw.
  if(timeline.tick!==lastPublishedTick){
    const state={type:'state',generation,telemetry:{...timeline.state,simulationStats:{mode:'worker',stepHz:MECHANICAL_HZ,backlogSeconds:result.backlogSeconds}}};
    scope.postMessage(state);renderPort?.postMessage(state);lastPublishedTick=timeline.tick;
  }
  setTimeout(pulse,result.backlogSeconds>0?0:1000/MECHANICAL_HZ);
}
pulse();

import {advance,INITIAL,INITIAL_TELEMETRY,type Controls,type Telemetry} from './mechanics';

export const MECHANICAL_HZ=240;
/** Rendering-independent clock. A delayed callback creates a retained backlog,
 * never a larger physics step or discarded elapsed time. Controls take effect
 * at the next fixed-step boundary; pauses exclude hidden-page wall-clock time.
 */
export class MechanicalTimeline{
  state:Telemetry=structuredClone(INITIAL_TELEMETRY);
  tick=0;
  private origin:number;
  private controls:Controls;
  private pausedAt:number|null=null;
  private pausedDuration=0;
  private events:{tick:number;controls:Controls}[]=[];
  constructor(now:number,controls:Controls=INITIAL){this.origin=now;this.controls=structuredClone(controls);}
  private elapsed(now:number){return Math.max(0,(this.pausedAt??now)-this.origin-this.pausedDuration);}
  targetTick(now:number){return Math.floor(this.elapsed(now)*MECHANICAL_HZ/1000);}
  setControls(controls:Controls,now:number){
    const event={tick:Math.ceil(this.elapsed(now)*MECHANICAL_HZ/1000),controls:structuredClone(controls)};
    if(this.events.at(-1)?.tick===event.tick)this.events[this.events.length-1]=event;else this.events.push(event);
  }
  setPaused(paused:boolean,now:number){
    if(paused&&this.pausedAt===null)this.pausedAt=now;
    else if(!paused&&this.pausedAt!==null){this.pausedDuration+=now-this.pausedAt;this.pausedAt=null;}
  }
  advanceTo(now:number,budget=480){
    const target=this.targetTick(now);let steps=0;
    while(this.tick<target&&steps<budget){
      while(this.events.length&&this.events[0].tick<=this.tick)this.controls=this.events.shift()!.controls;
      this.state=advance(this.state,this.controls,1/MECHANICAL_HZ);this.tick++;steps++;
    }
    return {steps,backlogSeconds:Math.max(0,target-this.tick)/MECHANICAL_HZ};
  }
}

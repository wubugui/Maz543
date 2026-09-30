import type {Controls,Telemetry} from './mechanics';
import type {PartInfo} from './maz543';

// Three objects stay in the rendering runtime. The inspector needs metadata only.
export type PartSummary=Omit<PartInfo,'group'>;
export type ViewportMetrics={width:number;height:number;left:number;top:number;innerWidth:number;devicePixelRatio:number};
export type InputPayload={type:string;[key:string]:string|number|boolean};
export type DomCommand=
  |{op:'create';id:number;tag:string}
  |{op:'set';id:number;field:'style'|'dataset'|'attribute'|'property';key:string;value:string}
  |{op:'append'|'remove'|'click';id:number};
export type RenderInput=
  |{type:'init';canvas:OffscreenCanvas;simulation:MessagePort;metrics:ViewportMetrics;hidden:boolean;search:string;controls:Controls;selection:string}
  |{type:'state';controls:Controls;selection:string}
  |{type:'size';metrics:ViewportMetrics}
  |{type:'visibility';hidden:boolean}
  |{type:'input';target:'canvas'|'document';event:InputPayload;metrics:ViewportMetrics}
  |{type:'click';id:number}
  |{type:'frame';id:number}
  |{type:'api';id:number;method:'view'|'focus'|'reset'|'exportModel';arg?:string}
  |{type:'dispose'};
export type RenderOutput=
  |{type:'dom';commands:DomCommand[]}
  |{type:'frame-request'|'frame-cancel';id:number}
  |{type:'ready';parts:PartSummary[];count:number}
  |{type:'select';id:string}
  |{type:'telemetry';telemetry:Telemetry}
  |{type:'error';message:string}
  |{type:'export-progress';stage:string}
  |{type:'api-result';id:number;error?:string}
  |{type:'disposed'};

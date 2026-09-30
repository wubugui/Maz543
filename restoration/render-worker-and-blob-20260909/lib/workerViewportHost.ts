import type {ViewportEnvironment} from './viewportEnvironment';
import type {DomCommand,InputPayload,RenderOutput,ViewportMetrics} from './viewportProtocol';

type Listener=(event:any)=>void;
/** The DOM subset actually used by OrbitControls and our overlays. No globals
 * are patched: loaders/exporters still detect the real worker environment. */
export class ViewportEventTarget{
  private listeners=new Map<string,Set<Listener>>();
  addEventListener(type:string,fn:Listener){let set=this.listeners.get(type);if(!set)this.listeners.set(type,set=new Set());set.add(fn);}
  removeEventListener(type:string,fn:Listener){this.listeners.get(type)?.delete(fn);}
  dispatch(data:InputPayload){const event={...data,target:this,currentTarget:this,preventDefault(){},stopPropagation(){}};for(const fn of [...(this.listeners.get(data.type)??[])])fn(event);}
}

export function createWorkerViewportHost(canvas:OffscreenCanvas,initial:ViewportMetrics,hidden:boolean,search:string,send:(data:RenderOutput)=>void){
  let metrics=initial,nextElement=1,nextFrame=1,queued=false;
  const commands:DomCommand[]=[],elements=new Map<number,RemoteElement>(),frames=new Map<number,FrameRequestCallback>();
  const resizeCallbacks=new Set<()=>void>();
  const flush=()=>{queued=false;if(commands.length)send({type:'dom',commands:commands.splice(0)});};
  const command=(value:DomCommand)=>{commands.push(value);if(!queued){queued=true;queueMicrotask(flush);}};
  class RemoteElement extends ViewportEventTarget{
    readonly id:number;style:Record<string,string>;dataset:Record<string,string>;
    onclick:(()=>void)|null=null;
    private properties:Record<string,string>={};
    constructor(id:number,tag?:string){super();this.id=id;elements.set(id,this);if(tag)command({op:'create',id,tag});
      const proxy=(field:'style'|'dataset')=>new Proxy<Record<string,string>>({}, {set:(target,key,value)=>{const name=String(key),text=String(value);if(target[name]!==text){target[name]=text;command({op:'set',id,field,key:name,value:text});}return true;}});
      this.style=proxy('style');this.dataset=proxy('dataset');
    }
    private setProperty(key:string,value:string){if(this.properties[key]!==value){this.properties[key]=value;command({op:'set',id:this.id,field:'property',key,value});}}
    get textContent(){return this.properties.textContent??'';}set textContent(value:string){this.setProperty('textContent',value);}
    get className(){return this.properties.className??'';}set className(value:string){this.setProperty('className',value);}
    get href(){return this.properties.href??'';}set href(value:string){this.setProperty('href',value);}
    get download(){return this.properties.download??'';}set download(value:string){this.setProperty('download',value);}
    setAttribute(key:string,value:string){command({op:'set',id:this.id,field:'attribute',key,value});}
    get clientWidth(){return metrics.width;}get clientHeight(){return metrics.height;}
    getBoundingClientRect(){return {left:metrics.left,top:metrics.top,width:metrics.width,height:metrics.height,right:metrics.left+metrics.width,bottom:metrics.top+metrics.height,x:metrics.left,y:metrics.top};}
    get ownerDocument(){return documentProxy;}getRootNode(){return documentProxy;}
    // The real canvas captures synchronously on pointerdown before forwarding.
    setPointerCapture(_id:number){}releasePointerCapture(_id:number){}
    remove(){command({op:'remove',id:this.id});elements.delete(this.id);}
    click(){command({op:'click',id:this.id});}
  }
  const input=new RemoteElement(0);
  const documentProxy=Object.assign(new ViewportEventTarget(),{hidden,createElement:(tag:string)=>new RemoteElement(nextElement++,tag)});
  const host={get clientWidth(){return metrics.width;},get clientHeight(){return metrics.height;},appendChild(element:unknown){if(element instanceof RemoteElement)command({op:'append',id:element.id});return element;}};
  class RemoteResizeObserver{
    private notify:()=>void;
    constructor(callback:()=>void){this.notify=callback;}
    observe(){resizeCallbacks.add(this.notify);}disconnect(){resizeCallbacks.delete(this.notify);}
  }
  const environment:ViewportEnvironment={
    canvas,input:input as unknown as HTMLElement,
    window:{get devicePixelRatio(){return metrics.devicePixelRatio;},get innerWidth(){return metrics.innerWidth;},location:{search} as Location},
    document:documentProxy as unknown as ViewportEnvironment['document'],
    ResizeObserver:RemoteResizeObserver as unknown as typeof ResizeObserver,
    requestAnimationFrame:callback=>{const id=nextFrame++;frames.set(id,callback);send({type:'frame-request',id});return id;},
    cancelAnimationFrame:id=>{frames.delete(id);send({type:'frame-cancel',id});},
  };
  return {host:host as unknown as HTMLDivElement,environment,
    updateMetrics(value:ViewportMetrics){const changed=value.width!==metrics.width||value.height!==metrics.height||value.innerWidth!==metrics.innerWidth;metrics=value;if(changed)for(const notify of resizeCallbacks)notify();},
    visibility(value:boolean){if(documentProxy.hidden===value)return;documentProxy.hidden=value;documentProxy.dispatch({type:'visibilitychange'});},
    input(target:'canvas'|'document',event:InputPayload){(target==='canvas'?input:documentProxy).dispatch(event);},
    click(id:number){elements.get(id)?.onclick?.();},
    frame(id:number){const callback=frames.get(id);frames.delete(id);callback?.(performance.now());},
    flush,
  };
}

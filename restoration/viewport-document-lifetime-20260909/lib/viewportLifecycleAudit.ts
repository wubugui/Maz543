import type {Telemetry} from './mechanics';

const STORAGE_KEY='maz543:viewport-lifecycle-audit:v1';
type Row={time:number;page:string;event:string;details:Record<string,unknown>};

/** Opt-in, bounded lifecycle journal. No timers, unload handlers, GC requests,
 * browser settings, model caches or simulation state changes. It intentionally
 * observes pagehide/pageshow persisted before choosing a retention fix. */
export function createViewportLifecycleAudit(host:HTMLElement){
  if(process.env.NODE_ENV!=='development'||new URLSearchParams(location.search).get('lifecycle-audit')!=='1')return null;
  const page=crypto.randomUUID(),output=document.createElement('pre'),button=document.createElement('button');
  output.dataset.viewportLifecycleAudit='1';output.setAttribute('aria-label','页面资源生命周期记录');
  output.style.cssText='position:absolute;z-index:12;left:12px;top:185px;max-height:32%;max-width:85%;overflow:auto;background:#111e;color:#ddd;font-size:11px;padding:8px';
  button.textContent='记录页面资源现场';button.style.cssText='position:absolute;z-index:13;left:12px;top:145px;padding:7px;background:#263d32;color:white';
  host.appendChild(output);host.appendChild(button);
  let rows:Row[]=[],closed=false,telemetry:Record<string,unknown>|null=null;
  const read=()=>{try{const value=JSON.parse(sessionStorage.getItem(STORAGE_KEY)??'[]');if(Array.isArray(value))rows=value.slice(-95);}catch{/* Storage restrictions must not affect the vehicle. */}};
  const navigation=()=>performance.getEntriesByType('navigation').map(entry=>{
    const nav=entry as PerformanceNavigationTiming&{notRestoredReasons?:{toJSON?:()=>unknown};activationStart?:number};
    return {type:nav.type,activationStart:nav.activationStart,notRestoredReasons:nav.notRestoredReasons?.toJSON?.()??null};
  });
  const record=(event:string,details:Record<string,unknown>={})=>{
    read();rows.push({time:Date.now(),page,event,details});rows=rows.slice(-96);
    try{sessionStorage.setItem(STORAGE_KEY,JSON.stringify(rows));}catch{/* Best effort diagnostic only. */}
    if(!closed)output.textContent=JSON.stringify({page,query:location.search,events:rows,limits:'Page lifecycle events and legacy JS heap snapshot. Heap excludes most driver/GPU allocations; process memory is measured separately. No resource policy changed.'},null,2);
  };
  const snapshot=()=>{
    const memory=(performance as Performance&{memory?:{usedJSHeapSize:number;totalJSHeapSize:number;jsHeapSizeLimit:number}}).memory;
    record('snapshot',{hidden:document.hidden,navigation:navigation(),telemetry,jsHeap:memory?{used:memory.usedJSHeapSize,total:memory.totalJSHeapSize,limit:memory.jsHeapSizeLimit}:null,
      canvases:[...host.querySelectorAll('canvas')].map(canvas=>({width:canvas.width,height:canvas.height,connected:canvas.isConnected}))});
  };
  const onPageHide=(event:PageTransitionEvent)=>record('pagehide',{persisted:event.persisted,hidden:document.hidden});
  const onPageShow=(event:PageTransitionEvent)=>record('pageshow',{persisted:event.persisted,navigation:navigation()});
  const onVisibility=()=>record('visibilitychange',{hidden:document.hidden});
  const onFreeze=()=>record('freeze');const onResume=()=>record('resume');
  window.addEventListener('pagehide',onPageHide);window.addEventListener('pageshow',onPageShow);
  document.addEventListener('visibilitychange',onVisibility);document.addEventListener('freeze',onFreeze);document.addEventListener('resume',onResume);
  button.onclick=snapshot;record('viewer-effect-enter',{query:location.search,navigation:navigation()});
  return {record,snapshot,setTelemetry(t:Telemetry){telemetry={time:t.time,engineRPM:t.rpm,render:t.renderStats,backlog:t.simulationStats?.backlogSeconds};},
    dispose(){if(closed)return;record('audit-listeners-dispose');closed=true;button.onclick=null;button.remove();output.remove();telemetry=null;
      window.removeEventListener('pagehide',onPageHide);window.removeEventListener('pageshow',onPageShow);
      document.removeEventListener('visibilitychange',onVisibility);document.removeEventListener('freeze',onFreeze);document.removeEventListener('resume',onResume);},
  };
}

/** Finite development capture. Wall time in the rendering thread includes
 * driver stalls; it is not GPU execution time. No finish/readback or mutation. */
export function createFramePhaseProfile(host:HTMLDivElement,document:Pick<Document,'createElement'>){
  const button=document.createElement('button'),output=document.createElement('pre');
  button.textContent='记录接下来 12 帧';button.style.cssText='position:absolute;z-index:11;left:12px;top:145px;padding:7px;background:#263d32;color:white';
  output.setAttribute('aria-label','逐帧阶段耗时诊断');output.style.cssText='position:absolute;z-index:10;left:12px;top:185px;max-width:90%;max-height:45%;overflow:auto;background:#111e;color:#ddd;padding:12px;font-size:10px';
  output.textContent='手动开始有限采样；保留原渲染、精度和求解。';host.appendChild(button);host.appendChild(output);
  let remaining=0;const samples:Record<string,unknown>[]=[];
  button.onclick=()=>{samples.length=0;remaining=12;output.textContent='正在记录 12 个完整模型帧。';};
  return {
    begin(loaded:boolean){return loaded&&remaining>0?performance.now():undefined;},
    finish(start:number,updateEnd:number,cacheBegin:number,cacheEnd:number,drawEnd:number,details:Record<string,unknown>){
      samples.push({startMs:start,updateMs:updateEnd-start,queryPollMs:cacheBegin-updateEnd,cacheMs:cacheEnd-cacheBegin,submitMs:drawEnd-cacheEnd,frameWorkMs:drawEnd-start,...details});remaining--;
      if(!remaining)output.textContent=JSON.stringify({kind:'render-thread-wall-time',limits:'Includes synchronous driver waits. Not GPU duration or end-to-end UI latency. No finish/readback or precision reduction.',samples},null,2);
    },
    dispose(){button.onclick=null;button.remove();output.remove();},
  };
}

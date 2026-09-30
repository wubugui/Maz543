'use client';
import { useRef, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { ArrowDownToLine, ArrowUpRight, Box, ChevronRight, Crosshair, Expand, Gauge, Info, Layers3, LoaderCircle, Maximize, MousePointer2, Power, RotateCcw, Settings2, SlidersHorizontal, X } from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import type { ViewerAPI } from './vehicle-viewer';
import type { PartInfo } from '@/lib/maz543';
import { INITIAL, INITIAL_TELEMETRY, type Controls, type Telemetry } from '@/lib/mechanics';
const VehicleViewer=dynamic(()=>import('./vehicle-viewer'),{ssr:false});

export default function Workshop(){
  const [state,setState]=useState<Controls>({...INITIAL}),[t,setT]=useState<Telemetry>({...INITIAL_TELEMETRY});
  const [parts,setParts]=useState<PartInfo[]>([]),[count,setCount]=useState(0),[selected,setSelected]=useState('');
  const [info,setInfo]=useState(false),[exporting,setExporting]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const [panel,setPanel]=useState<'controls'|'parts'>('controls'),[mobileOpen,setMobileOpen]=useState(false);
  const api=useRef<ViewerAPI|null>(null),workbench=useRef<HTMLElement>(null);
  const set=useCallback(<K extends keyof Controls>(key:K,value:Controls[K])=>setState(s=>({...s,[key]:value})),[]);
  const ready=useCallback((p:PartInfo[],n:number)=>{setParts(p);setCount(n);},[]);
  const current=parts.find(p=>p.id===selected);
  const reset=()=>{setState({...INITIAL});setSelected('');api.current?.reset();};
  const demo=(id:string)=>{
    if(id==='engine'){setState(s=>({...s,running:true,throttle:20,gear:0,mode:'xray',focus:'engine',explode:0,slow:true}));setSelected('engine');requestAnimationFrame(()=>api.current?.focus('engine'));}
    if(id==='steering'){setState(s=>({...s,mode:'solid',focus:'',steering:26,explode:0}));setSelected('suspension');api.current?.view('top');}
    if(id==='suspension'){setState(s=>({...s,mode:'xray',focus:'',terrain:85,explode:0}));setSelected('suspension');api.current?.view('side');}
  };
  async function exportFile(){if(!api.current)return;setExporting(true);try{await api.current.exportModel();setNotice('已导出当前姿态的 GLB；交互逻辑保留在浏览器模型中。');}catch{setNotice('导出未成功，请恢复整车后重试。');}finally{setExporting(false);setTimeout(()=>setNotice(''),7000);}}
  const range=(label:string,key:'throttle'|'brake'|'steering'|'terrain'|'explode'|'doors',unit='%',min=0,max=100)=> <div className="range-field"><div><label id={`label-${key}`}>{label}</label><output>{state[key]}<span>{unit}</span></output></div><Slider aria-labelledby={`label-${key}`} min={min} max={max} step={1} value={[state[key]]} onValueChange={v=>set(key,Array.isArray(v)?v[0]:v)}/></div>;
  const toggle=(label:string,key:'slow'|'lights'|'labels'|'wireframe')=><label className="switch-field"><span>{label}</span><Switch checked={state[key]} onCheckedChange={v=>set(key,v)} aria-label={label}/></label>;
  return <main className="workshop" ref={workbench}>
    <header className="topbar"><a className="brand" href="/" aria-label="MAZ-543 机械解构"><span className="brand-icon"><Box size={21}/></span><span>机械解构<span className="brand-divider">/</span><b>MAZ–543A</b></span></a><div className="top-meta"><i/> Blender 三维工作台 <span className="version">02 / Blender 资产</span></div><div className="header-actions"><button className="quiet-button" onClick={()=>setInfo(true)}><Info size={16}/><span>模型说明</span></button><button className="export-button" onClick={exportFile} disabled={!count||exporting}>{exporting?<LoaderCircle size={16} className="spin"/>:<ArrowDownToLine size={16}/>}<span>导出 GLB</span></button></div></header>
    <section className="workspace">
      <div className="viewport">
        <VehicleViewer state={state} selected={selected} api={api} onReady={ready} onSelect={setSelected} onTelemetry={setT} onError={setError}/>
        <div className="scene-title"><div className="eyebrow">MINSK AUTOMOBILE PLANT <span>8×8</span></div><h1>MAZ<span>–</span>543A</h1><p>双驾驶室 · 四轴全轮驱动底盘</p></div>
        <div className="view-mode"><Tabs value={state.mode} onValueChange={v=>set('mode',v as Controls['mode'])}><TabsList><TabsTrigger value="solid"><Box size={14}/>外观</TabsTrigger><TabsTrigger value="xray"><Layers3 size={14}/>透视</TabsTrigger><TabsTrigger value="section"><SlidersHorizontal size={14}/>纵剖</TabsTrigger></TabsList></Tabs></div>
        {!count&&!error&&<div className="loading-model"><LoaderCircle className="spin"/><span>正在装配三维模型…</span></div>}
        {error&&<div className="model-error"><Info/><p>{error}</p><button className="export-button" onClick={()=>location.reload()}>重新加载</button></div>}
        <div className="camera-rail" aria-label="视角"><button title="立体视角" aria-label="立体视角" onClick={()=>api.current?.view('perspective')}><Box size={18}/></button><button title="正视" onClick={()=>api.current?.view('front')}>前</button><button title="侧视" onClick={()=>api.current?.view('side')}>侧</button><button title="俯视" onClick={()=>api.current?.view('top')}>顶</button><span/><button aria-label="重置模型" title="重置模型" onClick={reset}><RotateCcw size={17}/></button><button aria-label="全屏" title="全屏" onClick={()=>{if(document.fullscreenElement)document.exitFullscreen?.();else workbench.current?.requestFullscreen?.().catch(()=>setNotice('当前浏览器不支持全屏。'));}}><Maximize size={17}/></button></div>
        {state.focus&&<button className="exit-isolate" onClick={()=>{set('focus','');api.current?.view('perspective');}}><X size={14}/>退出单独查看</button>}
        {current&&<div className="selection-card"><div className="selection-top"><span style={{background:current.color}}/><small>已选组件</small><button aria-label="取消选择" onClick={()=>setSelected('')}><X size={14}/></button></div><h3>{current.name}</h3><p>{current.english}</p><div className="selection-actions"><button onClick={()=>api.current?.focus(current.id)}><Crosshair size={14}/>聚焦</button><button onClick={()=>{set('focus',state.focus?'':current.id);api.current?.focus(current.id);}}><Expand size={14}/>{state.focus?'显示整车':'单独查看'}</button><button onClick={()=>{setPanel('parts');setMobileOpen(true);}}>详情<ChevronRight size={14}/></button></div></div>}
        <div className="scene-bottom"><div className="drag-hint"><MousePointer2 size={14}/><span>拖动旋转<span> · </span>滚轮缩放<span> · </span>点击部件</span></div><div className="scale"><i/><span>1 m</span></div></div>
        <div className="scene-stats"><div><span>驱动形式</span><strong>8 × 8</strong></div><div><span>参考轴距</span><strong>7,700<small> mm</small></strong></div><div><span>发动机</span><strong>V12<small> / 60°</small></strong></div><div><span>参考功率</span><strong>525<small> hp</small></strong></div></div>
        <button className="mobile-controls" onClick={()=>setMobileOpen(!mobileOpen)}><Settings2 size={17}/>{mobileOpen?'关闭控制':'打开控制'}</button>
      </div>
      <aside className={`inspector ${mobileOpen?'mobile-open':''}`}>
        <Tabs className="inspector-tabs" value={panel} onValueChange={v=>setPanel(v as 'controls'|'parts')}><TabsList variant="line"><TabsTrigger value="controls"><Settings2 size={16}/>机械控制</TabsTrigger><TabsTrigger value="parts"><Layers3 size={16}/>组件结构</TabsTrigger></TabsList></Tabs>
        <div className="inspector-scroll">{panel==='controls'?<>
          <section className="control-section"><div className="section-heading"><h2>动力系统</h2><span className={state.running?'status running':'status'}><i/>{state.running?'运行中':'已关闭'}</span></div>
            <div className="rpm-display"><div><strong>{Math.round(t.rpm).toLocaleString()}</strong><span>RPM</span></div><div className="rpm-bars">{Array.from({length:28},(_,i)=><i key={i} className={i<Math.round(t.rpm/2000*28)?'lit':''}/>)}</div><div className="rpm-scale"><span>0</span><span>1,000</span><span>2,000</span></div></div>
            <button className={`ignition ${state.running?'is-running':''}`} onClick={()=>set('running',!state.running)}><Power size={17}/>{state.running?'关闭发动机':'启动发动机'}<span>{state.running?'STOP':'START'}</span></button>
            {range('油门','throttle')}
            <div className="gear-field"><div className="field-title"><span>变速箱</span><small>{state.gear===0?'空挡':state.gear<0?'倒挡':`${state.gear} 挡`}</small></div><RadioGroup className="gears" value={String(state.gear)} onValueChange={v=>set('gear',Number(v))} aria-label="变速箱挡位">{[[-1,'R'],[0,'N'],[1,'1'],[2,'2'],[3,'3']].map(([v,l])=><label key={v} className={state.gear===v?'active':''}><RadioGroupItem value={String(v)} aria-label={`${l} 挡`}/><span>{l}</span></label>)}</RadioGroup></div>
            {range('制动','brake')}{toggle('发动机慢动作 ×0.035','slow')}
            <div className="speed-strip"><Gauge size={17}/><span>演示车速</span><strong>{Math.abs(t.speed*3.6).toFixed(1)}<small>km/h</small></strong></div>
          </section>
          <section className="control-section"><div className="section-heading"><h2>转向与悬架</h2><span className="section-number">02</span></div>{range('双前轴转向','steering','°',-30,30)}{range('悬架台架激励','terrain')}
            <div className="control-note">模型固定在观察台上；车轮转动与地面滚动表示行驶。</div>
          </section>
          <section className="control-section"><div className="section-heading"><h2>拆解与观察</h2><span className="section-number">03</span></div>{range('总成分离','explode')}{range('驾驶室开门','doors')}{toggle('车灯','lights')}{toggle('部件标签','labels')}{toggle('网格线框','wireframe')}</section>
          <section className="control-section demo-section"><h2>机构演示</h2><button onClick={()=>demo('engine')}><span>01</span>V12 曲柄连杆<ArrowUpRight size={15}/></button><button onClick={()=>demo('steering')}><span>02</span>双前轴转向<ArrowUpRight size={15}/></button><button onClick={()=>demo('suspension')}><span>03</span>八轮独立悬架<ArrowUpRight size={15}/></button></section>
        </>:<>
          <section className="control-section parts-intro"><h2>底盘总成</h2><p>选择组件检查结构，或在模型上直接点击。</p></section>
          <div className="parts-list">{parts.map((p,i)=><button key={p.id} onClick={()=>setSelected(p.id)} className={selected===p.id?'selected':''}><span className="part-index">{String(i+1).padStart(2,'0')}</span><span className="part-dot" style={{background:p.color}}/><span><b>{p.name}</b><small>{p.english}</small></span><ChevronRight size={15}/></button>)}</div>
          {current&&<section className="control-section part-details"><div className="eyebrow">COMPONENT DETAILS</div><h2>{current.name}</h2><p>{current.detail}</p><h4>运动方式</h4><p>{current.motion}</p><div className="fidelity"><Info size={14}/>{current.fidelity}</div><button className="ignition" onClick={()=>{set('focus',current.id);api.current?.focus(current.id);}}><Crosshair size={16}/>单独查看此组件</button></section>}
        </>}</div>
        <div className="inspector-footer"><i/><span>{count?`${count.toLocaleString()} 个几何实例`:'模型装配中'}</span><button onClick={()=>setInfo(true)}>精度说明<ArrowUpRight size={13}/></button></div>
      </aside>
    </section>
    <footer className="statusbar"><span><i/>MAZ–543A / 双驾驶室参考底盘</span><span>运动学演示 · 部分内构简化</span><button onClick={()=>setInfo(true)}>资料与建模边界<ArrowUpRight size={13}/></button></footer>
    {notice&&<div className="toast" role="status">{notice}<button onClick={()=>setNotice('')} aria-label="关闭提示"><X size={15}/></button></div>}
    <Dialog open={info} onOpenChange={setInfo}><DialogContent className="reference-dialog"><DialogTitle>模型依据与精度范围</DialogTitle><DialogDescription>按 MAZ-543A 量产双驾驶室照片统一外观的 Blender 参考重建。</DialogDescription><div className="reference-body"><p>本模型包含主要底盘总成及部分内部运动机构。它尚未达到原厂 CAD 精度，也未包含全车所有零件。</p><dl><div><dt>有资料依据</dt><dd>四轴全驱、前两轴转向、7,700 mm 总轴距、2,375 mm 轮距、双驾驶室、V12 柴油机、独立扭杆悬架、三速行星变速箱及两速分动箱。</dd></div><div><dt>估算与简化</dt><dd>车身曲面、胎纹、紧固件数量、管路路径、内部安装尺寸、齿形齿比、配气相位与悬架几何。车身按实车照片和侧视图校正；前后悬、安装细节和附件未按原厂公差标定。轮胎按 ВИ-203 产品规格重建，不代表某一出厂年份的原装胎型。</dd></div><div><dt>仿真边界</dt><dd>活塞使用曲柄连杆几何，转向使用共同瞬时中心；悬架为位移驱动演示。车速采用简化响应模型。没有求解轮胎接地力、真实液力变矩器、流体、热力、电路或材料应力。</dd></div><div><dt>导出内容</dt><dd>GLB 包含当前可见模型、部件层级与姿态，不包含网页控制逻辑和机械动画。可在 Blender 等软件继续细化。</dd></div></dl><h3>Blender 资产</h3><p>外壳与轮胎在 Blender 4.5 LTS 中重建，采用独立开口网格、倒角、曲面轮胎、4K 基础色及 2K 法线与 ORM 贴图。浏览器加载实际导出的 GLB，机械内构仍有简化。</p><h3>参考资料</h3><a href="https://www.barnaultransmash.ru/d12a-525a" target="_blank" rel="noreferrer">D12A-525A 发动机生产厂规格<ArrowUpRight size={15}/></a><a href="https://rtyre.ru/uploads/booklets/Vi-203.pdf" target="_blank" rel="noreferrer">BELSHINA VI-203 轮胎产品单页<ArrowUpRight size={15}/></a><a href="https://commons.wikimedia.org/wiki/File:MAZ-543_special_purpose_truck,_Strategic_Missile_Forces_Museum.JPG" target="_blank" rel="noreferrer">MAZ-543A 实车正面照片<ArrowUpRight size={15}/></a><a href="https://djvu.online/file/zjMdLY3MFjmTL" target="_blank" rel="noreferrer">《MAZ-543 轮式底盘及其改型：技术说明》· 1977<ArrowUpRight size={15}/></a><p className="source-note">原始技术说明扫描件；布局、传动与悬架参考。</p><a href="https://en.volmaz.ru/articles/maz-543.html" target="_blank" rel="noreferrer">MAZ-543 驾驶室与车型照片参考<ArrowUpRight size={15}/></a><p>进一步达到精确外形与全内构仿真，需要指定车辆版本的尺寸图、零件目录、装配关系及实测材料和动力参数。</p></div></DialogContent></Dialog>
  </main>;
}

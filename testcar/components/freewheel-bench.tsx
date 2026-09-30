'use client';
import {useEffect,useRef,useState} from 'react';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import type {FreewheelFit,FreewheelState} from '@/lib/converterFreewheel';
import {freewheelCoilPositions} from '@/lib/converterFreewheelGeometry';
import styles from './freewheel-bench.module.css';
type Sample=FreewheelState&{frame:number;torque:number};
type Bench={fit:FreewheelFit&{rowX:number[]};samples:Sample[];coilVertexOrder:number[]};
type Reading={time:number;omega:number;torque:number;length:number;force:number;gap:number;normal:number};
const initial:Reading={time:0,omega:0,torque:-2,length:0,force:0,gap:0,normal:0};
const VERSION='continuous-freewheel-20260908';
export default function FreewheelBench(){
  const mount=useRef<HTMLDivElement>(null),play=useRef({time:0,running:false,speed:.25,row:'front',retainers:false});
  const [running,setRunning]=useState(false),[speed,setSpeed]=useState(.25),[row,setRow]=useState('front'),[retainers,setRetainers]=useState(false);
  const [reading,setReading]=useState(initial),[ready,setReady]=useState(false),[error,setError]=useState('');
  const cameraReset=useRef<()=>void>(()=>{});
  const seek=(value:number)=>{play.current.time=value;play.current.running=false;setRunning(false);setReading(r=>({...r,time:value}));};
  useEffect(()=>{
    const host=mount.current;if(!host)return;
    let disposed=false,handle=0,resizeHandle=0,model:T.Group|undefined,lastTime=performance.now(),lastPublish=0,previousPose=-1;
    const abort=new AbortController(),scene=new T.Scene();scene.background=new T.Color('#172027');
    const camera=new T.PerspectiveCamera(33,1,.001,10);camera.position.set(-.34,.09,.16);
    let renderer:T.WebGLRenderer;
    try{renderer=new T.WebGLRenderer({antialias:true});}catch{setError('三维显示未能启动，请重新加载。');return;}
    renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
    host.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label','双排滚柱单向离合器三维台架');
    const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,0,0);controls.enableDamping=true;controls.minDistance=.08;controls.maxDistance=.8;
    cameraReset.current=()=>{camera.position.set(-.34,.09,.16);controls.target.set(0,0,0);controls.update();};
    const room=new RoomEnvironment(),pmrem=new T.PMREMGenerator(renderer),environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;scene.environmentIntensity=1.1;room.dispose();
    const key=new T.DirectionalLight('#fff5df',3);key.position.set(-.2,.3,.2);scene.add(key,new T.HemisphereLight('#d5ebff','#242833',1.8));
    const resize=new ResizeObserver(()=>{cancelAnimationFrame(resizeHandle);resizeHandle=requestAnimationFrame(()=>{if(disposed)return;const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/Math.max(1,h);camera.updateProjectionMatrix();});});resize.observe(host);
    const disposeModel=(root:T.Object3D)=>{const geometry=new Set<T.BufferGeometry>(),materials=new Set<T.Material>();root.traverse(o=>{if(o instanceof T.Mesh){geometry.add(o.geometry);(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m));}});geometry.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());};
    const contextLost=(e:Event)=>{e.preventDefault();setError('三维显示连接中断，请重新加载台架。');play.current.running=false;setRunning(false);};renderer.domElement.addEventListener('webglcontextlost',contextLost);
    Promise.all([new GLTFLoader().loadAsync(`/models/maz543a-freewheel-bench.glb?v=${VERSION}`),fetch(`/models/maz543a-freewheel-bench.json?v=${VERSION}`,{signal:abort.signal}).then(r=>{if(!r.ok)throw Error('trace load');return r.json() as Promise<Bench>;})]).then(([gltf,data])=>{
      if(disposed){disposeModel(gltf.scene);return;}
      model=gltf.scene;scene.add(model);
      const outer=['front','rear'].map(r=>model!.getObjectByName(`CV_${r}_outer`)!);
      const rollers=['front','rear'].flatMap((r,i)=>Array.from({length:data.fit.rollerCount},(_,j)=>({ob:model!.getObjectByName(`CV_${r}_roller_${j}`)!,x:data.fit.rowX[i]})));
      const coilGeometry=new Set<T.BufferGeometry>(),retainerObjects:T.Object3D[]=[];
      model.traverse(o=>{if(o.name.includes('_engagement_spring_')&&o instanceof T.Mesh)coilGeometry.add(o.geometry);if(o.name.includes('_retainer_'))retainerObjects.push(o);});
      if(outer.some(o=>!o)||rollers.some(o=>!o.ob)||coilGeometry.size!==1||data.coilVertexOrder.length!==1932)throw Error('incomplete bench model');
      setReady(true);
      const animate=(now:number)=>{
        if(disposed)return;const dt=Math.min(.05,(now-lastTime)/1000);lastTime=now;const p=play.current;
        if(p.running){p.time=Math.min(2,p.time+dt*p.speed);if(p.time>=2){p.running=false;setRunning(false);}}
        outer.forEach((o,i)=>o.visible=p.row==='both'||p.row===(i===0?'front':'rear'));retainerObjects.forEach(o=>o.visible=p.retainers);
        const frame=Math.min(199,Math.floor(p.time*100)),t=p.time*100-frame,a=data.samples[frame],b=data.samples[frame+1];
        const lerp=(x:number,y:number)=>x+(y-x)*t;
        if(previousPose!==p.time){
          // Interpolate the recorded local centre, not its world-space chord.
          const local=(s:Sample)=>{const c=Math.cos(s.q[3]),sn=Math.sin(s.q[3]);return [c*s.q[0]+sn*s.q[1],-sn*s.q[0]+c*s.q[1]];};
          const la=local(a),lb=local(b),y=lerp(la[0],lb[0]),z=lerp(la[1],lb[1]),angle=lerp(a.q[3],b.q[3]),spin=lerp(a.q[2],b.q[2]);
          outer.forEach(o=>o.quaternion.setFromAxisAngle(T.Object3D.DEFAULT_UP.clone().set(1,0,0),angle));
          rollers.forEach(({ob,x})=>{ob.position.set(x,y,z);ob.quaternion.setFromAxisAngle(new T.Vector3(1,0,0),spin-angle);});
          const points=freewheelCoilPositions(data.fit,y,z,lerp(a.springLength,b.springLength));
          coilGeometry.forEach(g=>{const attribute=g.getAttribute('position') as T.BufferAttribute;data.coilVertexOrder.forEach((source,i)=>attribute.setXYZ(i,points[source*3],points[source*3+1],points[source*3+2]));attribute.needsUpdate=true;g.computeVertexNormals();g.computeBoundingSphere();});
          previousPose=p.time;
        }
        if(now-lastPublish>80){setReading({time:p.time,omega:lerp(a.v[3],b.v[3]),torque:p.time<.4?-2:p.time<1.2?2:-2,length:lerp(a.springLength,b.springLength),force:lerp(a.springAxialForce,b.springAxialForce),gap:lerp(a.gaps[1],b.gaps[1]),normal:lerp(a.normalForce[1],b.normalForce[1])});lastPublish=now;}
        controls.update();renderer.render(scene,camera);handle=requestAnimationFrame(animate);
      };handle=requestAnimationFrame(animate);
    }).catch(()=>{if(!disposed)setError('台架模型或运动记录未能加载，请重新加载。');});
    return ()=>{disposed=true;abort.abort();cancelAnimationFrame(handle);cancelAnimationFrame(resizeHandle);resize.disconnect();controls.dispose();if(model)disposeModel(model);environment.dispose();pmrem.dispose();renderer.domElement.removeEventListener('webglcontextlost',contextLost);renderer.dispose();renderer.domElement.remove();};
  },[]);
  const phase=reading.normal>1e-3&&Math.abs(reading.omega)<.001?'楔紧保持':Math.abs(reading.omega)>.001?'越程转动':'初始静止';
  return <main className={styles.bench}>
    <header><a href="/">← 整车工作台</a><span>MAZ–543A · 变矩器机构</span></header>
    <div className={styles.body}>
      <section className={styles.view} aria-label="单向离合器检查">
        <div className={styles.caption}><h1>滚柱单向离合器</h1><p>共用固定内圈 · 两套独立外圈</p></div>
        <div ref={mount} className={styles.canvas}/>
        {!ready&&!error&&<p className={styles.loading}>正在装载机构…</p>}
        {error&&<div role="alert" className={styles.loading}>{error}<button onClick={()=>location.reload()}>重新加载</button></div>}
        <div className={styles.viewFooter}><span>拖动旋转 · 滚轮缩放</span><button onClick={()=>cameraReset.current()}>复位视角</button></div>
      </section>
      <aside className={styles.controls}>
        <div className={styles.heading}><h2>受力运动回放</h2><strong>{phase}</strong></div>
        <p className={styles.note}>旧参数接触试验：反向保持 → 正向越程 → 减速楔紧。新图件复核发现，圆线弹簧与原图弯带形状不符，正在重建。此回放保留作对照，不代表原车结构；尚未接入导轮流体与整车。</p>
        <p className={styles.note}><a href="/strip-spring">查看新弯带弹簧的接触研究 →</a></p>
        <div className={styles.buttons}><button disabled={!ready||!!error} onClick={()=>{const next=!play.current.running;if(next&&play.current.time>=2)play.current.time=0;play.current.running=next;setRunning(next);}}>{running?'暂停检查':'播放运动'}</button><button disabled={!ready} onClick={()=>seek(0)}>回到起点</button></div>
        <label className={styles.time}>试验时刻 <output>{reading.time.toFixed(3)} s / 2.000 s</output><input aria-label="试验时刻" type="range" min="0" max="2" step="0.001" value={reading.time} disabled={!ready} onChange={e=>seek(Number(e.target.value))}/></label>
        <div className={styles.fields}><label>回放速度<select aria-label="回放速度" value={speed} onChange={e=>{const v=Number(e.target.value);play.current.speed=v;setSpeed(v);}}><option value="0.1">0.1 ×</option><option value="0.25">0.25 ×</option><option value="1">1 ×</option></select></label><label>观察排<select aria-label="观察排" value={row} onChange={e=>{play.current.row=e.target.value;setRow(e.target.value);}}><option value="front">前排</option><option value="rear">后排</option><option value="both">两排</option></select></label></div>
        <label className={styles.check}><input type="checkbox" checked={retainers} onChange={e=>{play.current.retainers=e.target.checked;setRetainers(e.target.checked);}}/>显示轴向保持环</label>
        <dl className={styles.readings}><div><dt>外载扭矩 / 每排</dt><dd>{reading.torque.toFixed(1)} <small>N·m</small></dd></div><div><dt>外圈转速</dt><dd>{(reading.omega*30/Math.PI).toFixed(1)} <small>RPM</small></dd></div><div><dt>单根弹簧轴向力</dt><dd>{reading.force.toFixed(3)} <small>N</small></dd></div><div><dt>弹簧轴向长度</dt><dd>{(reading.length*1000).toFixed(3)} <small>mm</small></dd></div><div><dt>滚柱与楔面间隙</dt><dd>{(Math.max(0,reading.gap)*1000).toFixed(4)} <small>mm</small></dd></div><div><dt>单滚柱楔面法向力</dt><dd>{Math.max(0,reading.normal).toFixed(2)} <small>N</small></dd></div></dl>
        <p className={styles.note}>固定内圈提供支承反力。滚柱在弹簧作用下靠向楔面，接触摩擦产生单向保持；正向外载超过当前预载后连续越程。</p>
      </aside>
    </div>
  </main>;
}

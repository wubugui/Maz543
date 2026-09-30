'use client';
import {useEffect,useRef,useState} from 'react';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import styles from './freewheel-bench.module.css';

type Equilibrium={index:number;betaRad:number;forceN:number;energyJ:number;stressPa:number;rollerPosition:[number,number,number]};
type Study={kind:string;rows:Equilibrium[]};
export default function StripSpringStudy(){
  const hostRef=useRef<HTMLDivElement>(null),view=useRef({index:0,pocket:true}),reset=useRef(()=>{});
  const [data,setData]=useState<Study|null>(null),[index,setIndex]=useState(0),[pocket,setPocket]=useState(true),[error,setError]=useState('');
  const seek=(next:number)=>{view.current.index=next;setIndex(next);};
  useEffect(()=>{
    const host=hostRef.current;if(!host)return;
    let disposed=false,frame=0,resizeFrame=0,model:T.Group|undefined;
    const abort=new AbortController(),scene=new T.Scene();scene.background=new T.Color('#172027');
    let renderer:T.WebGLRenderer;try{renderer=new T.WebGLRenderer({antialias:true});}catch{setError('三维显示未能启动，请重新加载。');return;}
    renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
    host.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label','弯带弹簧与滚柱静态平衡三维研究件');
    const camera=new T.PerspectiveCamera(34,1,.0001,2),controls=new OrbitControls(camera,renderer.domElement);
    controls.enableDamping=true;controls.minDistance=.025;controls.maxDistance=.2;
    reset.current=()=>{camera.position.set(-.085,.077,-.018);controls.target.set(0,.065,-.007);controls.update();};reset.current();
    const room=new RoomEnvironment(),pmrem=new T.PMREMGenerator(renderer),environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;scene.environmentIntensity=1;
    room.dispose();const light=new T.DirectionalLight('#fff5df',3);light.position.set(-.06,.1,-.04);scene.add(light,new T.HemisphereLight('#d5ebff','#242833',1.5));
    const resize=new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(disposed)return;renderer.setSize(host.clientWidth,host.clientHeight,false);camera.aspect=host.clientWidth/Math.max(1,host.clientHeight);camera.updateProjectionMatrix();});});resize.observe(host);
    const disposeModel=(root:T.Object3D)=>{const meshes=new Set<T.BufferGeometry>(),materials=new Set<T.Material>();root.traverse(o=>{if(o instanceof T.Mesh){meshes.add(o.geometry);(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m));}});meshes.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());};
    const lost=(e:Event)=>{e.preventDefault();setError('三维显示连接中断，请重新加载。');};renderer.domElement.addEventListener('webglcontextlost',lost);
    Promise.all([new GLTFLoader().loadAsync('/models/maz543a-strip-study.glb?v=strip-20260908'),fetch('/models/maz543a-strip-study.json?v=strip-20260908',{signal:abort.signal}).then(r=>{if(!r.ok)throw Error('study data');return r.json() as Promise<Study>;})]).then(([gltf,study])=>{
      if(disposed){disposeModel(gltf.scene);return;}model=gltf.scene;scene.add(model);
      const states=study.rows.map(r=>model!.getObjectByName(`CS_equilibrium_${String(r.index).padStart(2,'0')}`));
      const roller=model.getObjectByName('CS_roller_12_5x22'),outer=model.getObjectByName('CS_outer_pocket');
      if(study.kind!=='independent-static-equilibria'||states.length!==26||states.some(o=>!o)||!roller||!outer)throw Error('incomplete equilibria');
      setData(study);
      const animate=()=>{if(disposed)return;const current=view.current;states.forEach((o,i)=>{o!.visible=i===current.index;});outer.visible=current.pocket;roller.position.fromArray(study.rows[current.index].rollerPosition);controls.update();renderer.render(scene,camera);frame=requestAnimationFrame(animate);};animate();
    }).catch(()=>{if(!disposed)setError('研究件或平衡记录未能加载，请重新加载。');});
    return()=>{disposed=true;abort.abort();cancelAnimationFrame(frame);cancelAnimationFrame(resizeFrame);resize.disconnect();controls.dispose();if(model)disposeModel(model);environment.dispose();pmrem.dispose();renderer.domElement.removeEventListener('webglcontextlost',lost);renderer.dispose();renderer.domElement.remove();};
  },[]);
  const row=data?.rows[index];
  return <main className={styles.bench}>
    <header><a href="/freewheel">← 单向离合器台架</a><a href="/">整车工作台</a></header>
    <div className={styles.body}>
      <section className={styles.view} aria-label="弯带研究件检查">
        <div className={styles.caption}><h1>弯带弹簧接触</h1><p>26 个独立静态平衡 · 图件形状研究</p></div>
        <div ref={hostRef} className={styles.canvas}/>
        {!data&&!error&&<p className={styles.loading}>正在装载研究件…</p>}
        {error&&<div role="alert" className={styles.loading}>{error}<button onClick={()=>location.reload()}>重新加载</button></div>}
        <div className={styles.viewFooter}><span>拖动旋转 · 滚轮缩放</span><button onClick={()=>reset.current()}>复位视角</button></div>
      </section>
      <aside className={styles.controls}>
        <div className={styles.heading}><h2>逐个平衡位置</h2><strong>研究中</strong></div>
        <p className={styles.note}>原图呈卷曲、弯带轮廓，旧圆线螺旋弹簧假设已撤回。这里展示重建弯带在滚柱挤压下的平衡变形；尚未接入连续运动与整车。</p>
        <label className={styles.time}>平衡位置 <output>{index+1} / 26</output><input aria-label="平衡位置" type="range" min="0" max="25" step="1" value={index} disabled={!data||!!error} onChange={e=>seek(Number(e.target.value))}/></label>
        <div className={styles.buttons}><button disabled={!data||index===0||!!error} onClick={()=>seek(index-1)}>上一位置</button><button disabled={!data||index===25||!!error} onClick={()=>seek(index+1)}>下一位置</button></div>
        <label className={styles.check}><input type="checkbox" checked={pocket} onChange={e=>{view.current.pocket=e.target.checked;setPocket(e.target.checked);}}/>显示外圈口袋</label>
        <dl className={styles.readings}>
          <div><dt>滚柱相对角</dt><dd>{row?(row.betaRad*180/Math.PI).toFixed(3):'—'} <small>°</small></dd></div>
          <div><dt>弹簧接触反力</dt><dd>{row?row.forceN.toFixed(2):'—'} <small>N</small></dd></div>
          <div><dt>弯曲储能</dt><dd>{row?(row.energyJ*1000).toFixed(3):'—'} <small>mJ</small></dd></div>
          <div><dt>最大增量弯曲应力</dt><dd>{row?(row.stressPa/1e6).toFixed(1):'—'} <small>MPa</small></dd></div>
        </dl>
        <p className={styles.note}>带宽 16 mm、厚度 0.30 mm、杨氏模量 210 GPa、自由曲线及固定座均为研究假设。滚柱采用目录尺寸线索 12.5 × 22 mm，早期 543A 适用性仍待核实。</p>
        <p className={styles.note}>各位置单独求平衡，没有赋予运动时间。应力随压缩上升，材料与弹性范围未确认，不能视为强度合格或原车性能。</p>
      </aside>
    </div>
  </main>;
}

'use client';
import {useEffect,useRef,useState} from 'react';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import styles from './freewheel-bench.module.css';

const groups=[['pump','泵轮与输入侧'],['turbine','涡轮与输出侧'],['front_reactor','前导轮与单向离合器'],['rear_reactor','后导轮与单向离合器'],['fixed_support','固定内圈与支承']] as const;
const descriptions:Record<string,string>={
  all:'泵轮、涡轮和两只独立导轮构成工作轮组。两只导轮各有单向离合器，共用一个固定内圈。',
  pump:'输入轴经闭锁壳体和旋转外罩连接泵轮。闭锁机构的止推盘也属于输入侧。',
  turbine:'涡轮通过轮毂连接涡轮轴，涡轮轴同时是行星变速箱输入轴。闭锁摩擦片随涡轮侧转动。',
  front_reactor:'前导轮通过自己的外圈、滚柱单向离合器连接固定内圈。手册记载它先进入自由旋转阶段。',
  rear_reactor:'后导轮具有独立的单向离合器。原车两只导轮均可沿泵轮方向越程，反向受到约束。',
  fixed_support:'两套单向离合器共用固定内圈，内圈经导轮支承连接固定壳体。涡轮轴穿过中心。',
};
type Asset={kind:string;meshCount:number;parts:{name:string}[]};
export default function ConverterAssembly(){
  const hostRef=useRef<HTMLDivElement>(null),reset=useRef(()=>{});
  const [ready,setReady]=useState(false),[error,setError]=useState(''),[selected,setSelected]=useState('all');
  const [explode,setExplode]=useState(0),[walls,setWalls]=useState(false),[cover,setCover]=useState(false),[section,setSection]=useState(false),[retainers,setRetainers]=useState(false);
  const [pump,setPump]=useState(0),[turbine,setTurbine]=useState(0);
  const state=useRef({selected,explode,walls,cover,section,retainers,pump,turbine});state.current={selected,explode,walls,cover,section,retainers,pump,turbine};
  useEffect(()=>{if(ready)reset.current();},[selected,ready]);
  useEffect(()=>{
    const host=hostRef.current;if(!host)return;let disposed=false,frame=0,model:T.Group|undefined;
    const abort=new AbortController(),scene=new T.Scene();scene.background=new T.Color('#172027');
    let renderer:T.WebGLRenderer;try{renderer=new T.WebGLRenderer({antialias:true});}catch{setError('三维显示未能启动。');return;}
    renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;renderer.localClippingEnabled=true;
    host.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label','四工作轮变矩器内部总成三维检查');
    const camera=new T.PerspectiveCamera(36,1,.005,10),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.08;controls.maxDistance=3.5;
    reset.current=()=>{const selected=state.current.selected;const target=model&&(selected==='all'?model:model.getObjectByName('CA_'+selected));
      if(target){target.updateWorldMatrix(true,true);const sphere=new T.Box3().setFromObject(target).getBoundingSphere(new T.Sphere());const distance=Math.max(.22,sphere.radius/Math.sin(T.MathUtils.degToRad(camera.fov/2))*1.12);controls.target.copy(sphere.center);camera.position.copy(sphere.center).addScaledVector(new T.Vector3(-1.15,.66,-.80).normalize(),distance);}
      else{camera.position.set(-1.15,.66,-.80);controls.target.set(0,0,0);}controls.update();};reset.current();
    const room=new RoomEnvironment(),pmrem=new T.PMREMGenerator(renderer),environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;room.dispose();
    const light=new T.DirectionalLight('#fff5df',3);light.position.set(-1,1,-1);scene.add(light,new T.HemisphereLight('#d5ebff','#202932',1.2));
    const resize=new ResizeObserver(()=>{if(disposed)return;renderer.setSize(host.clientWidth,host.clientHeight,false);camera.aspect=host.clientWidth/Math.max(1,host.clientHeight);camera.updateProjectionMatrix();});resize.observe(host);
    const disposeModel=(root:T.Object3D)=>{const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>();root.traverse(o=>{if(o instanceof T.Mesh){geometries.add(o.geometry);(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m));}});geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());};
    const lost=(event:Event)=>{event.preventDefault();setError('三维显示连接中断，请重新加载。');};renderer.domElement.addEventListener('webglcontextlost',lost);
    Promise.all([new GLTFLoader().loadAsync('/models/maz543a-converter-assembly.glb?v=four-wheel-20260908'),fetch('/models/maz543a-converter-assembly.json?v=four-wheel-20260908',{signal:abort.signal}).then(r=>{if(!r.ok)throw Error('assembly data');return r.json() as Promise<Asset>;})]).then(([gltf,data])=>{
      if(disposed){disposeModel(gltf.scene);return;}model=gltf.scene;scene.add(model);
      const roots=groups.map(([key])=>model!.getObjectByName('CA_'+key));
      if(data.kind!=='source-topology-assembly-inspection'||data.meshCount!==180||roots.some(r=>!r)||data.parts.some(p=>!model!.getObjectByName(p.name)))throw Error('assembly parts missing');
      const meshes:T.Mesh[]=[];model.traverse(o=>{if(o instanceof T.Mesh)meshes.push(o);});
      const plane=new T.Plane(new T.Vector3(0,0,1),0);let previousSection:boolean|undefined;
      setReady(true);
      const draw=()=>{if(disposed)return;const s=state.current;
        const offsets=[.18,-.20,-.085,.035,.28];roots.forEach((ob,i)=>{ob!.visible=s.selected==='all'||s.selected===groups[i][0];ob!.position.x=offsets[i]*s.explode;});
        roots[0]!.rotation.x=s.pump*Math.PI/180;roots[1]!.rotation.x=s.turbine*Math.PI/180;
        for(const mesh of meshes){if(mesh.userData.shellRole)mesh.visible=s.walls;if(mesh.userData.inspectionHide==='housing')mesh.visible=s.cover;if(mesh.name.endsWith('_thrust_ring'))mesh.visible=s.retainers;}
        if(previousSection!==s.section){for(const mesh of meshes)for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){material.clippingPlanes=s.section?[plane]:[];material.needsUpdate=true;}previousSection=s.section;}
        controls.update();renderer.render(scene,camera);frame=requestAnimationFrame(draw);
      };draw();
    }).catch(()=>{if(!disposed)setError('变矩器总成未能完整加载，请重新加载。');});
    return()=>{disposed=true;abort.abort();cancelAnimationFrame(frame);resize.disconnect();controls.dispose();if(model)disposeModel(model);environment.dispose();pmrem.dispose();renderer.domElement.removeEventListener('webglcontextlost',lost);renderer.dispose();renderer.domElement.remove();};
  },[]);
  return <main className={styles.bench}>
    <header><a href="/">← 整车工作台</a><a href="/strip-spring">弯带接触研究 →</a></header>
    <div className={styles.body}>
      <section className={styles.view} aria-label="变矩器总成检查">
        <div className={styles.caption}><h1>变矩器内部总成</h1><p>一个泵轮 · 一个涡轮 · 两个导轮</p></div><div ref={hostRef} className={styles.canvas}/>
        {!ready&&!error&&<p className={styles.loading}>正在装载内部总成…</p>}
        {error&&<div role="alert" className={styles.loading}>{error}<button onClick={()=>location.reload()}>重新加载</button></div>}
        <div className={styles.viewFooter}><span>拖动旋转 · 滚轮缩放</span><button onClick={()=>reset.current()}>复位视角</button></div>
      </section>
      <aside className={styles.controls}>
        <div className={styles.heading}><h2>装配结构检查</h2><strong>重建中</strong></div>
        <p className={styles.note}>依据手册图 42 和零件目录重建的 180 个实体。这里检查装配与转动关系；完整液力工作过程仍在开发。</p>
        <div className={styles.fields}><label>查看总成<select aria-label="查看总成" value={selected} disabled={!ready||!!error} onChange={e=>setSelected(e.target.value)}><option value="all">全部总成</option>{groups.map(([key,name])=><option key={key} value={key}>{name}</option>)}</select></label></div>
        <p className={styles.note}>{descriptions[selected]}</p>
        <label className={styles.time}>轴向拆开 <output>{Math.round(explode*100)}%</output><input aria-label="轴向拆开" type="range" min="0" max="1" step=".01" value={explode} disabled={!ready||!!error} onChange={e=>setExplode(Number(e.target.value))}/></label>
        <label className={styles.check}><input type="checkbox" checked={walls} onChange={e=>setWalls(e.target.checked)}/>显示流道壁与芯环</label>
        <label className={styles.check}><input type="checkbox" checked={cover} onChange={e=>setCover(e.target.checked)}/>显示旋转外罩</label>
        <label className={styles.check}><input type="checkbox" checked={retainers} onChange={e=>setRetainers(e.target.checked)}/>显示导轮保持环</label>
        <label className={styles.check}><input type="checkbox" checked={section} onChange={e=>setSection(e.target.checked)}/>半剖查看</label>
        <label className={styles.time}>泵轮侧装配转角 <output>{pump}°</output><input aria-label="泵轮侧装配转角" type="range" min="0" max="360" value={pump} disabled={!ready||!!error} onChange={e=>setPump(Number(e.target.value))}/></label>
        <label className={styles.time}>涡轮侧装配转角 <output>{turbine}°</output><input aria-label="涡轮侧装配转角" type="range" min="0" max="360" value={turbine} disabled={!ready||!!error} onChange={e=>setTurbine(Number(e.target.value))}/></label>
        <p className={styles.note}>转角用于检查轴、轮毂和盘片的装配层级，不代表油流驱动。导轮越程、闭锁接合和变矩特性尚未接入本总成。</p>
        <p className={styles.note}>叶片数、型线、流道和安装尺寸为重建参数，尚非原厂数据。滚柱采用目录尺寸线索 12.5 × 22 mm；弯带为拟合初始平衡，真实固定座、材料及强度仍待核实。</p>
      </aside>
    </div>
  </main>;
}

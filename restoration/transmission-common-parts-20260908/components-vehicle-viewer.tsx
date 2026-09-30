'use client';
import { useEffect, useRef, type RefObject } from 'react';
import * as T from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { createMAZ543, type PartInfo } from '@/lib/maz543';
import { advance, INITIAL_TELEMETRY, type Controls, type Telemetry } from '@/lib/mechanics';
import { startingPose,STARTING } from '@/lib/starting';
import { d12Pose } from '@/lib/d12';
import { suspensionPose,SUSPENSION } from '@/lib/suspension';
import { coolingPose, COOLING, releaseSpringWeights } from '@/lib/cooling';
import { cardanPose } from '@/lib/cardan';
import {planetaryPose,PLANETARY,transmissionSpringWeights,CLUTCH_PACKS,type ClutchName} from '@/lib/transmission';

export type ViewerAPI = { view: (name:string)=>void; focus:(id:string)=>void; exportModel:()=>Promise<void>; reset:()=>void };
type Props = { state:Controls; selected:string; api:RefObject<ViewerAPI|null>; onReady:(parts:PartInfo[],count:number)=>void; onSelect:(id:string)=>void; onTelemetry:(t:Telemetry)=>void; onError:(s:string)=>void };
export default function VehicleViewer({state,selected,api,onReady,onSelect,onTelemetry,onError}:Props) {
  const container=useRef<HTMLDivElement>(null),latest=useRef(state),selection=useRef(selected);
  const callbacks=useRef({onReady,onSelect,onTelemetry,onError});
  useEffect(()=>{latest.current=state;selection.current=selected;callbacks.current={onReady,onSelect,onTelemetry,onError};},[state,selected,onReady,onSelect,onTelemetry,onError]);
  useEffect(()=>{
    if(!container.current)return;const host:HTMLDivElement=container.current;
    let renderer:T.WebGLRenderer;
    try{renderer=new T.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});}catch{callbacks.current.onError('此设备未能初始化 WebGL 2。请启用浏览器硬件加速后重新打开。');return;}
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.75));renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.localClippingEnabled=true;
    renderer.toneMapping=T.AgXToneMapping;renderer.toneMappingExposure=1;host.appendChild(renderer.domElement);
    renderer.info.autoReset=false;
    renderer.domElement.setAttribute('aria-label','MAZ-543 三维模型：拖动旋转，滚轮缩放，点击选择部件');
    const scene=new T.Scene();scene.background=new T.Color('#242a28');scene.fog=new T.Fog('#242a28',65,115);
    const renderInspection=process.env.NODE_ENV==='development'?new URLSearchParams(window.location.search).get('inspect'):null;
    const camera=new T.PerspectiveCamera(35,1,.05,120);camera.position.set(-12,7.5,12);
    const orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(-.2,1.1,0);orbit.enableDamping=true;orbit.dampingFactor=.08;orbit.minDistance=.15;orbit.maxDistance=60;orbit.maxPolarAngle=Math.PI*.51;orbit.update();
    const pmrem=new T.PMREMGenerator(renderer),room=new RoomEnvironment();const env=pmrem.fromScene(room,.05);scene.environment=env.texture;scene.environmentIntensity=.55;room.dispose();
    const ambient=new T.HemisphereLight('#dce5e8','#46493c',.38);scene.add(ambient);
    const key=new T.DirectionalLight('#fff8ea',2.6);key.position.set(-7,13,7);key.castShadow=true;key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-10;key.shadow.camera.right=10;key.shadow.camera.top=9;key.shadow.camera.bottom=-9;key.shadow.normalBias=.016;key.shadow.bias=-.00006;key.shadow.camera.far=40;scene.add(key,key.target);
    const rim=new T.DirectionalLight('#c8d9e3',1.9);rim.position.set(3,6,-9);scene.add(rim);
    const fill=new T.DirectionalLight('#ede6d6',.7);fill.position.set(-9,3,-3);scene.add(fill);
    const floor=new T.Mesh(new T.PlaneGeometry(160,160),new T.MeshStandardMaterial({color:'#181d1b',roughness:.93,metalness:.025}));floor.rotation.x=-Math.PI/2;floor.position.y=-.008;floor.receiveShadow=true;scene.add(floor);
    const grid=new T.GridHelper(80,80,'#68736d','#505b56');grid.position.y=-.007;(grid.material as T.Material).transparent=true;(grid.material as T.Material).opacity=.11;scene.add(grid);
    const model=createMAZ543();scene.add(model.root);
    const padGeometry=new T.BoxGeometry(1.24,.10,.88),padMaterial=new T.MeshStandardMaterial({color:'#303b36',roughness:.7,metalness:.45});
    const testPads=Array.from({length:8},(_,i)=>{const pad=new T.Mesh(padGeometry,padMaterial);pad.position.set(SUSPENSION.axles[Math.floor(i/2)],-.05,(i%2?1:-1)*SUSPENSION.track/2);pad.receiveShadow=true;pad.visible=false;scene.add(pad);return pad;});
    let renderedRoot=model.root,displayParts=model.parts,exportMaterials=model.originalMaterials,disposed=false,needsFocus=false;
    const bindings:{source:T.Object3D;target:T.Object3D}[]=[];
    const ghost=new T.MeshStandardMaterial({color:'#a6bab1',transparent:true,opacity:.055,depthWrite:false,roughness:.6,side:T.DoubleSide});
    const clip=new T.Plane(new T.Vector3(0,0,-1),0),clipMaterials=new Map<T.Material,T.Material>();
    const nativeMeshes:T.Mesh[]=[],nativeGhost=new Set<T.Mesh>(),d12Nodes=new Map<string,T.Object3D>();let nativeStyle='';
    let d12Root:T.Object3D|null=null;
    const suspensionNodes=new Map<string,T.Object3D>();
    const coolingNodes=new Map<string,T.Object3D>();
    const cardanNodes=new Map<string,T.Object3D>();let cardanRoot:T.Object3D|null=null;
    const transmissionNodes=new Map<string,T.Object3D>();let transmissionRoot:T.Object3D|null=null,driveHolder:T.Object3D|undefined;
    const driveVisibility=new Map<T.Object3D,boolean>();
    let lastDriveView='';
    const coolingSprings:{mesh:T.Mesh;pitch:number;radius:number}[]=[];
    const startingNodes=new Map<string,T.Object3D>();let startingRoot:T.Group|null=null,startEngine:T.Group|null=null,preoilRoot:T.Object3D|undefined;
    const torsionMeshes:{mesh:T.Mesh;base:Float32Array;normal:Float32Array;tangent?:Float32Array}[]=[];
    const wheelBindings:{carrier:T.Object3D;brake?:T.Object3D;source:T.Group}[]=[];
    const draco=new DRACOLoader();draco.setDecoderPath('/draco/');draco.setWorkerLimit(2);const loader=new GLTFLoader();loader.setDRACOLoader(draco);
    Promise.all([loader.loadAsync('/models/maz543a-blender.glb?v=cab-profile-1'),loader.loadAsync('/models/d12a525a-engine.glb?v=water-1'),loader.loadAsync('/models/maz543a-suspension.glb?v=s543-1'),loader.loadAsync('/models/maz543a-starting.glb?v=start-4'),loader.loadAsync('/models/maz543a-cooling.glb?v=spring-round-wire-20260908'),loader.loadAsync('/models/maz543a-cardan.glb?v=cardan-2'),loader.loadAsync('/models/maz543a-transmission.glb?v=transmission-direct-area-20260908')]).then(([gltf,engineGltf,suspensionGltf,startingGltf,coolingGltf,cardanGltf,transmissionGltf])=>{
      if(disposed)return;
      renderedRoot=(gltf.scene.getObjectByName('MAZ543_REFERENCE_CHASSIS')||gltf.scene) as T.Group;
      driveHolder=renderedRoot.getObjectByName('drive');
      if(!driveHolder)throw new Error('Missing transmission mounting assembly');
      for(const name of ['drive_0002','drive_pivot_002','drive_pivot_007','drive_pivot_012']){
        const obsolete=driveHolder.getObjectByName(name);if(obsolete)obsolete.removeFromParent();
      }
      transmissionRoot=transmissionGltf.scene.getObjectByName('S543_TRANSMISSION')||transmissionGltf.scene;
      transmissionRoot.position.set(...PLANETARY.position);driveHolder.add(transmissionRoot);
      transmissionRoot.traverse(o=>transmissionNodes.set(o.name,o));
      for(const pack of Object.keys(CLUTCH_PACKS))for(let j=0;j<8;j++){
        const spring=transmissionNodes.get(`TX_${pack}_return_spring_${j}`);
        if(!(spring instanceof T.Mesh)||!spring.morphTargetInfluences||spring.morphTargetDictionary?.Pitch===undefined||spring.morphTargetDictionary.Radius===undefined)throw new Error(`Transmission spring ${pack}/${j}: missing circular-wire morphs`);
      }
      for(const child of driveHolder.children)driveVisibility.set(child,child.visible);
      const engineHolder=renderedRoot.getObjectByName('engine');
      if(!engineHolder)throw new Error('Missing engine mounting assembly');
      // Remove the superseded seed engine, keeping its chassis mounting transform.
      const obsoleteGeometries=new Set<T.BufferGeometry>();
      for(const child of [...engineHolder.children]){child.traverse(o=>{if(o instanceof T.Mesh)obsoleteGeometries.add(o.geometry);});engineHolder.remove(child);}
      obsoleteGeometries.forEach(g=>g.dispose());
      d12Root=engineGltf.scene.getObjectByName('D12A_525A')||engineGltf.scene;engineHolder.add(d12Root);
      d12Root.traverse(o=>{d12Nodes.set(o.name,o);});
      const coolingHolder=renderedRoot.getObjectByName('cooling');
      if(!coolingHolder)throw new Error('Missing cooling mounting assembly');
      const coolingRoot=coolingGltf.scene.getObjectByName('S543_COOLING')||coolingGltf.scene;coolingHolder.add(coolingRoot);
      coolingRoot.traverse(o=>{coolingNodes.set(o.name,o);});
      for(let side=0;side<2;side++){
        const spring=coolingNodes.get(`COOL_release_spring_${side}`);
        if(!(spring instanceof T.Mesh)||!spring.morphTargetInfluences||spring.morphTargetDictionary?.Pitch===undefined||spring.morphTargetDictionary.Radius===undefined)
          throw new Error(`Cooling spring ${side}: required round-wire morph targets are missing`);
        coolingSprings.push({mesh:spring,pitch:spring.morphTargetDictionary.Pitch,radius:spring.morphTargetDictionary.Radius});
      }
      cardanRoot=cardanGltf.scene.getObjectByName('S543_CARDAN')||cardanGltf.scene;
      cardanRoot.position.set(-4.8,1.9,0);cardanRoot.visible=false;coolingHolder.add(cardanRoot);
      cardanRoot.traverse(o=>{cardanNodes.set(o.name,o);});
      startingRoot=new T.Group();startingRoot.name='starting';startingRoot.userData.partId='starting';renderedRoot.add(startingRoot);
      startEngine=new T.Group();startEngine.name='STARTING_ENGINE_MOUNT';startEngine.position.copy(engineHolder.position);startingRoot.add(startEngine);
      for(const name of ['C5_STARTER','C5_FLYWHEEL_RING']){const ob=startingGltf.scene.getObjectByName(name);if(!ob)throw new Error('Missing '+name);startEngine.add(ob);}
      preoilRoot=startingGltf.scene.getObjectByName('MZN_PREOIL');if(!preoilRoot)throw new Error('Missing preoil pump');preoilRoot.position.set(...STARTING.pumpPosition);startingRoot.add(preoilRoot);
      startingRoot.traverse(o=>{startingNodes.set(o.name,o);});
      const suspensionHolder=renderedRoot.getObjectByName('suspension');
      if(!suspensionHolder)throw new Error('Missing suspension assembly');
      for(const child of [...suspensionHolder.children])suspensionHolder.remove(child);
      const suspensionRoot=suspensionGltf.scene.getObjectByName('S543_SUSPENSION')||suspensionGltf.scene;suspensionHolder.add(suspensionRoot);
      suspensionRoot.traverse(o=>{suspensionNodes.set(o.name,o);if(o instanceof T.Mesh&&o.userData.s543Role==='torsion'){
        o.geometry=o.geometry.clone();const a=o.geometry.getAttribute('position'),n=o.geometry.getAttribute('normal'),t=o.geometry.getAttribute('tangent');torsionMeshes.push({mesh:o,base:new Float32Array(a.array),normal:new Float32Array(n.array),tangent:t?new Float32Array(t.array):undefined});
      }});
      for(const w of model.wheels){const carrier=renderedRoot.getObjectByName(w.carrier.name);if(carrier)wheelBindings.push({carrier,brake:renderedRoot.getObjectByName(w.brake.name),source:w.carrier});}
      scene.remove(model.root);scene.add(renderedRoot);exportMaterials=new Map();
      renderedRoot.traverse(o=>{const source=model.root.getObjectByName(o.name);if(source&&!o.userData.coolingLegacyAux)bindings.push({source,target:o});if(o instanceof T.Mesh){o.castShadow=true;o.receiveShadow=true;nativeMeshes.push(o);exportMaterials.set(o.name,o.material as T.Material);
        if(o.userData.surface==='exterior'||model.ghostNames.has(o.name)||/BL_.*(?:Tyre|Rim|Hub|Wheel|Merged_wheels)/.test(o.name)||o.userData.s543Role==='cover')nativeGhost.add(o);
        const material=o.material as T.MeshStandardMaterial;
        if(material.map)material.map.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
        if(renderInspection==='no-normal')material.normalMap=null;
        if(renderInspection==='no-baked-ao')material.aoMapIntensity=0;
      }});
      displayParts=model.parts.map(p=>({...p,...(p.id==='engine'?{
        name:'D12A-525A 柴油机',detail:'Blender 重建的双缸列发动机：12 组空心活塞与销、6 组主副连杆、7 道主轴承、48 个气门和四根凸轮轴。外部按原厂及 525A 维修照片核对；安装尺寸与配气曲线仍待标定。',
        motion:'主连杆带动铰接副连杆，四凸轮轴以曲轴半速旋转；气门与双层弹簧同步运动。可切换整机、打开气门室盖、全部内构，并暂停观察。',fidelity:'型号照片与结构图有据 · 尺寸和物理标定未完成'}:p.id==='suspension'?{
        detail:'按 543 技术说明和实车近照重建：16 根扭杆及保护管、叉形摆臂、花键套、青铜衬套、轮架和 8 支带内部活塞的双筒减振器。',
        motion:'四连杆闭合约束带动轮端；扭杆弹力、减振力和轮胎接地力共同驱动车身起伏、俯仰及侧倾。台架输入停止后可观察自由衰减。',fidelity:'结构有据 · 安装尺寸、刚度与阻尼待标定'}:p.id==='cooling'?{
        name:'双风扇冷却系统',detail:'按原车图 27—31 重建的双十二叶风扇、滑环供电电磁离合器、滚针轴承、散热芯和联动百叶窗。下传动箱按实物照和目录重建；上下齿轮箱已有独立内构；万向轴、安装闭合及完整管路仍待完成。',
        motion:'两侧风扇独立通断并保留惯性；水泵与风扇负载反馈曲轴，十四个冷却节点传递热量。手动百叶窗和暖风支路改变散热。',fidelity:'结构与控制关系有据 · 尺寸、齿比、热流体参数待标定'}:{}),group:(renderedRoot.getObjectByName(p.id)||p.group) as T.Group}));
      const drivePart=displayParts.find(p=>p.id==='drive');if(drivePart)Object.assign(drivePart,{detail:'Blender 两排行星重建：共用行星架、三个长行星轮、三个短行星轮及四组摩擦盘。齿数从原车速比推导，尺寸与整车安装仍待标定。',motion:'两排行星轮常啮合，各挡位通过固定或连接不同构件建立转速约束。盘片已有滑动齿槽与轴向压紧姿态；液力、摩擦扭矩和差速机构仍未完成。',fidelity:'拓扑及速比有据 · 齿数推导与尺寸拟合'});
      displayParts.push({id:'starting',name:'电启动与预润滑',english:'C5 / MZN-2',color:'#c2a779',group:startingRoot,
        detail:'按原车剖面重建的惯性启动驱动和预润滑齿轮泵：螺旋花键、缓冲弹簧、摩擦片、11齿小齿轮、双齿轮、油封与独立加热夹套。预润滑电机四极定子按拆解照片拟合；电枢绕组与刷架仍未完成。',
        motion:'独立搭铁、预润滑和启动按钮驱动电气与轴系计算；发动机带转后驱动退出，断油后靠惯性停转。',fidelity:'拓扑与小齿轮齿数有据 · 电机曲线、尺寸及流体参数待标定'});
      nativeStyle=''; // Apply the current inspection layer to asynchronously loaded meshes.
      const count=nativeMeshes.reduce((n,m)=>n+(m.userData.detail_meshes||1),0);callbacks.current.onError('');callbacks.current.onReady(displayParts,count);
      needsFocus=true;
    }).catch(()=>{if(!disposed)callbacks.current.onError('Blender 模型未能加载。请刷新重试；需要下载完整三维资产与贴图。');});
    let t={...INITIAL_TELEMETRY};model.update(latest.current,t);
    const selector=new T.Box3Helper(new T.Box3(),0xe5a369);(selector.material as T.LineBasicMaterial).transparent=true;(selector.material as T.LineBasicMaterial).opacity=.35;selector.visible=false;scene.add(selector);
    const labelNodes=new Map<string,HTMLButtonElement>();
    for(const p of model.parts){const el=document.createElement('button');el.className='model-label';el.textContent=p.name;el.onclick=()=>callbacks.current.onSelect(p.id);el.style.display='none';host.appendChild(el);labelNodes.set(p.id,el);}
    let transition:{position:T.Vector3;target:T.Vector3}|null=null;
    const views:Record<string,[number,number,number]>={perspective:[-12,7.5,12],front:[-17,3,0],side:[0,3,18],top:[0,19,.001],rear:[15,4,8],under:[-9,.35,10]};
    function view(name:string){
      if(name==='front'){
        // Frame the front projection around the nose, not the middle of the
        // eleven-metre chassis. Otherwise zooming reaches the cab roof before
        // the front facade is large enough to inspect.
        const bounds=visibleBounds(renderedRoot);if(bounds.isEmpty())return;
        bounds.max.x=bounds.min.x;frame(renderedRoot,new T.Vector3(-1,0,0),bounds);return;
      }
      frame(renderedRoot,new T.Vector3(...(views[name]||views.perspective)).normalize());
    }
    function visibleBounds(object:T.Object3D){const bounds=new T.Box3();object.updateWorldMatrix(true,true);object.traverseVisible(o=>{if(o instanceof T.Mesh){if(!o.geometry.boundingBox)o.geometry.computeBoundingBox();if(o.geometry.boundingBox)bounds.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld));}});return bounds;}
    function focus(id:string){
      if(id==='drive'&&latest.current.transmissionView==='booster'&&transmissionRoot){
        transmissionRoot.updateWorldMatrix(true,false);
        const pack=CLUTCH_PACKS[latest.current.transmissionClutch],first=pack.gear===1,direct=pack.gear===3;
        const bounds=new T.Box3(new T.Vector3(direct?-.268:first?.204:pack.start-.04,direct?.086:pack.inner-.005,-.025),new T.Vector3(direct?-.145:first?.269:pack.start+.012,direct?.123:pack.outer+.02,.025)).applyMatrix4(transmissionRoot.matrixWorld);
        frame(transmissionRoot,new T.Vector3(-.45,.3,1).normalize(),bounds);return;
      }
      if(id==='drive'&&latest.current.transmissionView==='clutch'&&transmissionRoot){
        const pack=CLUTCH_PACKS[latest.current.transmissionClutch],lo=pack.start-(pack.direction===1?.016:pack.count*.0021+.008),hi=pack.start+(pack.direction===1?pack.count*.0021+.008:.016);
        transmissionRoot.updateWorldMatrix(true,false);
        const bounds=new T.Box3(new T.Vector3(lo,pack.inner-.008,-.025),new T.Vector3(hi,pack.outer+.024,.025)).applyMatrix4(transmissionRoot.matrixWorld);
        frame(transmissionRoot,new T.Vector3(-.7,.4,1).normalize(),bounds);return;
      }
      if(id==='drive'&&latest.current.transmissionView!=='assembly'&&transmissionRoot){frame(transmissionRoot,new T.Vector3(-.7,.5,1).normalize());return;}
      if(id==='cooling'&&latest.current.coolingView==='spring'){const spring=coolingNodes.get('COOL_release_spring_0');if(spring){frame(spring,new T.Vector3(.6,.35,1).normalize());return;}}
      if(id==='cooling'&&latest.current.coolingView==='cardan'&&cardanRoot){frame(cardanRoot,new T.Vector3(-.5,.5,1).normalize());return;}
      if(id==='cooling'&&latest.current.coolingView==='upper'){const upper=coolingNodes.get('COOL_upper_drive_0');if(upper){frame(upper,new T.Vector3(-1,.4,1).normalize());return;}}
      if(id==='cooling'&&latest.current.coolingView==='lower'){const lower=coolingNodes.get('COOL_lower_drive');if(lower){frame(lower,new T.Vector3(-1,.5,.9).normalize());return;}}
      if(id==='cooling-clutch'||id==='cooling'&&latest.current.coolingView==='clutch'){
        const mount=coolingNodes.get('COOL_fan_mount_0');if(mount){const center=mount.getWorldPosition(new T.Vector3());frame(mount,new T.Vector3(1,.4,1).normalize(),new T.Box3(center.clone().add(new T.Vector3(-.05,-.12,-.12)),center.clone().add(new T.Vector3(.23,.12,.12))));return;}
      }
      if(id==='water-impeller'){
        const bounds=new T.Box3();renderedRoot.updateWorldMatrix(true,true);
        renderedRoot.traverseVisible(o=>{if(o instanceof T.Mesh&&o.userData.waterPump&&(o.material as T.Material).name.startsWith('D12_water_stainless'))bounds.union(visibleBounds(o));});
        if(!bounds.isEmpty()){frame(renderedRoot,new T.Vector3(-.5,-.6,1).normalize(),bounds);return;}
      }
      if(id==='water-seal'){
        const bounds=new T.Box3();renderedRoot.updateWorldMatrix(true,true);
        renderedRoot.traverseVisible(o=>{if(o instanceof T.Mesh&&o.userData.waterPump&&['11','12','13','14','15','16'].includes(o.userData.figureItem))bounds.union(visibleBounds(o));});
        if(!bounds.isEmpty()){frame(renderedRoot,new T.Vector3(-.45,.2,1).normalize(),bounds);return;}
      }
      if(id==='timing-crank'||id==='timing-pumps'){
        const bounds=new T.Box3();renderedRoot.updateWorldMatrix(true,true);
        const ids=id==='timing-crank'?['crank27','upper18','lower18','generator_takeoff18','upper12','inclined18_L','inclined18_R']:['lower23','oil36','oil20','fuel23','fuel11','fuel21'];
        renderedRoot.traverseVisible(o=>{if(o instanceof T.Mesh&&ids.includes(o.userData.timingGearId))bounds.union(visibleBounds(o));});
        if(!bounds.isEmpty()){frame(renderedRoot,new T.Vector3(-1,.35,.7).normalize(),bounds);return;}
      }
      if(id==='cam-gears'){
        const bounds=new T.Box3();renderedRoot.updateWorldMatrix(true,true);
        renderedRoot.traverseVisible(o=>{if(o instanceof T.Mesh&&o.userData.camTrain&&o.userData.sourceId==='MAZ-1973-F7')bounds.union(visibleBounds(o));});
        if(!bounds.isEmpty()){frame(renderedRoot,new T.Vector3(-1,.38,.6).normalize(),bounds);return;}
      }
      const part=displayParts.find(p=>p.id===id);if(!part){view('perspective');return;}
      if(id==='cooling'){frame(part.group,new T.Vector3(1,.38,1).normalize());return;}
      if(id==='engine'&&latest.current.engineView==='waterpump'){frame(part.group,new T.Vector3(-.4,.17,1).normalize());return;}
      frame(part.group,id==='engine'&&['camdrive','timing','waterpump'].includes(latest.current.engineView)?new T.Vector3(-1,.6,.9).normalize():id==='starting'?(latest.current.startingView==='stator'?new T.Vector3(-1,.55,-.7):new T.Vector3(1,.7,-1)).normalize():camera.position.clone().sub(orbit.target).normalize());
    }
    function frame(object:T.Object3D,direction:T.Vector3,boundsOverride?:T.Box3){
      const bounds=boundsOverride??visibleBounds(object);if(bounds.isEmpty())return;const center=bounds.getCenter(new T.Vector3());
      // Millimetre-scale gear detail needs a fitted shadow camera. The chassis
      // shadow box and 16 mm normal bias erase these small contact shadows.
      if(['cooling','drive'].includes(latest.current.focus)||latest.current.focus==='engine'&&['camdrive','timing','waterpump'].includes(latest.current.engineView)){
        const radius=Math.max(.09,bounds.getSize(new T.Vector3()).length()*.6);
        key.target.position.copy(center);key.position.copy(center).addScaledVector(new T.Vector3(-7,13,7).normalize(),10);
        key.shadow.camera.left=key.shadow.camera.bottom=-radius;key.shadow.camera.right=key.shadow.camera.top=radius;
        key.shadow.camera.near=.1;key.shadow.camera.far=15;key.shadow.normalBias=Math.max(.00005,radius*.0005);key.shadow.bias=-radius*.00001;
      }else{
        key.target.position.set(0,0,0);key.position.set(-7,13,7);key.shadow.camera.left=-10;key.shadow.camera.right=10;key.shadow.camera.top=9;key.shadow.camera.bottom=-9;
        key.shadow.camera.near=.5;key.shadow.camera.far=40;key.shadow.normalBias=.016;key.shadow.bias=-.00006;
      }
      key.target.updateMatrixWorld();key.shadow.camera.updateProjectionMatrix();
      const right=new T.Vector3(0,1,0).cross(direction).normalize(),up=direction.clone().cross(right).normalize();
      const topReserve=window.innerWidth<760?(latest.current.focus?250:265):(latest.current.focus?180:235),bottomReserve=latest.current.focus?35:120;
      const tanV=Math.tan(camera.fov*Math.PI/360),widthFraction=Math.max(.7,1-100/host.clientWidth),heightFraction=Math.max(.35,1-(topReserve+bottomReserve)/host.clientHeight);
      camera.near=Math.max(.003,Math.min(.05,bounds.getSize(new T.Vector3()).length()/100));camera.updateProjectionMatrix();
      let distance=latest.current.focus==='cooling'&&latest.current.coolingView==='spring'?.025:.15;
      for(const x of [bounds.min.x,bounds.max.x])for(const y of [bounds.min.y,bounds.max.y])for(const z of [bounds.min.z,bounds.max.z]){
        const p=new T.Vector3(x,y,z).sub(center),depth=p.dot(direction);
        distance=Math.max(distance,Math.abs(p.dot(right))/(tanV*camera.aspect*widthFraction)+depth,Math.abs(p.dot(up))/(tanV*heightFraction)+depth);
      }
      distance*=1.06;const target=center.clone().addScaledVector(up,(topReserve-bottomReserve)/host.clientHeight*distance*tanV);
      transition={position:target.clone().addScaledVector(direction,distance),target};
    }
    async function exportModel(){
      const {exportGLB}=await import('@/lib/export-model');const data=await exportGLB(renderedRoot,exportMaterials);
      const blob=new Blob([data],{type:'model/gltf-binary'}),url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='MAZ543-reference-current-pose.glb';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
    }
    api.current={view,focus,exportModel,reset:()=>{t={...INITIAL_TELEMETRY};view('perspective');}};
    const ray=new T.Raycaster(),pointer=new T.Vector2();let down=[0,0];
    const pointerDown=(e:PointerEvent)=>{down=[e.clientX,e.clientY];};
    const pointerUp=(e:PointerEvent)=>{if(e.button!==0||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);
      const hit=ray.intersectObject(renderedRoot,true).find(h=>{let o:T.Object3D|null=h.object;while(o){if(!o.visible)return false;o=o.parent;}if(latest.current.mode==='section'&&h.point.z>0)return false;return true;});
      let o=hit?.object;while(o&&!o.userData.partId)o=o.parent||undefined;callbacks.current.onSelect(o?.userData.partId||'');};
    renderer.domElement.addEventListener('pointerdown',pointerDown);renderer.domElement.addEventListener('pointerup',pointerUp);
    const contextLost=(e:Event)=>{e.preventDefault();callbacks.current.onError('图形上下文已中断，请刷新页面恢复模型。');};renderer.domElement.addEventListener('webglcontextlost',contextLost);
    const target=new T.WebGLRenderTarget(1,1,{type:T.HalfFloatType,samples:2});const composer=new EffectComposer(renderer,target);composer.addPass(new RenderPass(scene,camera));
    const ao=new GTAOPass(scene,camera,1,1);ao.blendIntensity=.55;ao.updateGtaoMaterial({radius:.32,distanceExponent:1.5,thickness:1,scale:1,samples:8});composer.addPass(ao);composer.addPass(new OutputPass());
    const resize=()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h);composer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();if(latest.current.focus)focus(latest.current.focus);else frame(renderedRoot,camera.position.clone().sub(orbit.target).normalize());};
    const observer=new ResizeObserver(resize);observer.observe(host);resize();
    const gl=renderer.getContext() as WebGL2RenderingContext,debugRenderer=gl.getExtension('WEBGL_debug_renderer_info');
    const gpu=String(gl.getParameter(debugRenderer?.UNMASKED_RENDERER_WEBGL??gl.RENDERER));
    const gpuTimer=gl.getExtension('EXT_disjoint_timer_query_webgl2') as {TIME_ELAPSED_EXT:number;GPU_DISJOINT_EXT:number}|null;
    const pendingTimers:WebGLQuery[]=[];let gpuMs:number|undefined,timerFrame=0;
    let handle=0,last=performance.now(),lastReport=0,lastSelected='',lastFocus='',lastSuspensionWheel=-1,lastStartingComponent='',lastEngineInspection='',lastCoolingView='assembly',statsTime=last,statsFrames=0,stats:Telemetry['renderStats'];
    function animate(now:number){handle=requestAnimationFrame(animate);if(document.hidden){last=now;statsTime=now;statsFrames=0;return;}const dt=Math.min((now-last)/1000,.05);last=now;t=advance(t,latest.current,dt);model.update(latest.current,t);
      for(const {source,target} of bindings){target.position.copy(source.position);target.quaternion.copy(source.quaternion);target.scale.copy(source.scale);target.visible=source.visible;}
      if(transmissionRoot){
        for(const [name,pose] of Object.entries(planetaryPose(t.planetary.inputAngle,t.planetary.carrierAngle,latest.current.gear,Object.fromEntries(Object.entries(t.transmission.hydraulics.boosters).map(([name,b])=>[name,b.travel]))))){const joint=transmissionNodes.get(name);if(joint){joint.rotation.x=pose.rx;if(pose.p)joint.position.set(...pose.p);
          if(pose.springPack&&pose.springTravel!==undefined){const spring=transmissionNodes.get(`TX_${pose.springPack}_return_spring_${name.split('_').at(-1)}`);if(spring instanceof T.Mesh&&spring.morphTargetInfluences&&spring.morphTargetDictionary){const weights=transmissionSpringWeights(pose.springPack,pose.springTravel);spring.morphTargetInfluences[spring.morphTargetDictionary.Pitch]=weights[0];spring.morphTargetInfluences[spring.morphTargetDictionary.Radius]=weights[1];}}
        }}
        const inspect=latest.current.focus==='drive'&&latest.current.transmissionView!=='assembly';
        const view=latest.current.transmissionView,pack:ClutchName=latest.current.transmissionClutch;
        const boosterPack=pack;
        transmissionRoot.traverse(o=>{if(o instanceof T.Mesh)o.visible=latest.current.focus!=='drive'||(view==='gears'?!!o.userData.teeth:view==='booster'?o.name.startsWith(`TX_${boosterPack}_`)||(boosterPack==='direct'&&o.name.startsWith('TX_feed_'))||(boosterPack!=='first'&&o.name.startsWith('TX_case47_')&&(!o.name.endsWith('_oil_gallery')||o.name===`TX_case47_${boosterPack}_oil_gallery`)):view==='clutch'?o.name.startsWith(`TX_${pack}_`)&&(!latest.current.transmissionPlatesOnly||o.name.startsWith(`TX_${pack}_disc_`)):true);});
        const housing=transmissionNodes.get('TX_housing');if(housing)housing.visible=!inspect;
        for(const [child,visible] of driveVisibility)child.visible=inspect?child===transmissionRoot:visible;
        const driveViewKey=view==='clutch'||view==='booster'?`${view}-${pack}`:view;
        if(lastDriveView!==driveViewKey){lastDriveView=driveViewKey;if(latest.current.focus==='drive')needsFocus=true;}
      }
      // Accessory ratios are not integer multiples of a 720 degree cycle.
      // Keep the accumulated shaft angle; only the displayed crank angle wraps.
      for(const [name,pose] of Object.entries(d12Pose(t.starting.angle))){const joint=d12Nodes.get(name);if(joint){joint.position.set(...pose.p);joint.rotation.set(pose.rx,0,0);joint.scale.set(1,pose.sy??1,1);}}
      for(const [name,pose] of Object.entries(startingPose(t.starting))){const joint=startingNodes.get(name);if(joint){joint.position.set(...pose.p);joint.rotation.set(pose.rx,0,0);joint.scale.set(pose.sx??1,1,1);}}
      for(const [name,pose] of Object.entries(coolingPose(t.starting.cooling,t.starting.angle,latest.current.shutter))){const joint=coolingNodes.get(name);if(joint){joint.position.set(...pose.p);joint.rotation.set(pose.rx,pose.ry??0,0);joint.scale.set(pose.sx??1,1,1);}}
      for(let side=0;side<2;side++){
        const spring=coolingSprings[side];
        if(spring){
          const weights=releaseSpringWeights(t.starting.cooling.axialPosition[side]);
          spring.mesh.morphTargetInfluences![spring.pitch]=weights[0];
          spring.mesh.morphTargetInfluences![spring.radius]=weights[1];
        }
      }
      if(cardanRoot){
        cardanRoot.visible=latest.current.focus==='cooling'&&latest.current.coolingView==='cardan';
        if(cardanRoot.visible)for(const [name,pose] of Object.entries(cardanPose(t.starting.angle*COOLING.lowerTeeth[0]/COOLING.lowerTeeth[1],latest.current.cardanBend,latest.current.cardanExtension))){const joint=cardanNodes.get(name);if(joint){joint.position.set(...pose.p);joint.quaternion.set(...pose.q);}}
      }
      if(startingRoot){startingRoot.visible=(!latest.current.focus||['engine','starting'].includes(latest.current.focus))&&!(latest.current.focus==='engine'&&['camdrive','timing','waterpump'].includes(latest.current.engineView));}
      if(startEngine){const engine=renderedRoot.getObjectByName('engine');if(engine)startEngine.position.copy(engine.position);startEngine.visible=latest.current.startingComponent!=='preoil'||latest.current.focus!=='starting';}
      if(preoilRoot)preoilRoot.visible=latest.current.focus!=='engine'&&(latest.current.startingComponent!=='starter'||latest.current.focus!=='starting');
      const flywheelRing=startingNodes.get('C5_FLYWHEEL_RING');
      if(flywheelRing)flywheelRing.visible=!(latest.current.focus==='starting'&&latest.current.startingComponent==='starter'&&latest.current.startingView==='assembled');
      const suspension=suspensionPose(t.suspension.travel);
      for(const [name,pose] of Object.entries(suspension)){const joint=suspensionNodes.get(name);if(joint){joint.position.set(...pose.p);joint.rotation.set(pose.rx,0,0);}}
      wheelBindings.forEach(({carrier,brake,source},i)=>{const p=suspension[`S543_${i}_wheel`],side=i%2?1:-1;
        carrier.position.set(...p.p);carrier.position.z+=side*latest.current.explode/100*1.5;
        carrier.rotation.set(p.rx,source.rotation.y,0,'XYZ');
        if(brake){brake.position.copy(carrier.position).add(new T.Vector3(0,0,-side*.29).applyQuaternion(carrier.quaternion));brake.quaternion.copy(carrier.quaternion);}
      });
      for(const {mesh,base,normal,tangent} of torsionMeshes){
        // An isolated engine/cooling view hides the entire suspension parent.
        // Its dynamics still step above; recompute absolute tube deformation
        // when visible again instead of rewriting hidden vertices every frame.
        if(latest.current.focus&&latest.current.focus!=='suspension')continue;
        if(!mesh.visible||(latest.current.focus==='suspension'&&latest.current.suspensionWheel>=0&&latest.current.suspensionWheel!==mesh.userData.torsionStation))continue;
        const u=mesh.userData,angle=suspension[`S543_${u.torsionStation}_${u.torsionArm}`]?.rx??0,a=mesh.geometry.getAttribute('position'),n=mesh.geometry.getAttribute('normal');
        for(let i=0;i<a.count;i++){const k=i*3,f=(base[k]-u.torsionAnchorX)/(u.torsionDrivenX-u.torsionAnchorX),c=Math.cos(angle*f),s=Math.sin(angle*f),y=base[k+1]-u.torsionY,z=base[k+2]-u.torsionZ;
          a.setXYZ(i,base[k],u.torsionY+y*c-z*s,u.torsionZ+y*s+z*c);n.setXYZ(i,normal[k],normal[k+1]*c-normal[k+2]*s,normal[k+1]*s+normal[k+2]*c);
          if(tangent){const j=i*4,tx=tangent[j],rate=angle/(u.torsionDrivenX-u.torsionAnchorX),ty=tangent[j+1]*c-tangent[j+2]*s-rate*(y*s+z*c)*tx,tz=tangent[j+1]*s+tangent[j+2]*c+rate*(y*c-z*s)*tx,len=Math.hypot(tx,ty,tz);mesh.geometry.getAttribute('tangent').setXYZW(i,tx/len,ty/len,tz/len,tangent[j+3]);}
        }a.needsUpdate=true;n.needsUpdate=true;
        if(tangent)mesh.geometry.getAttribute('tangent').needsUpdate=true;
      }
      const isolated=!!latest.current.focus,cx=SUSPENSION.axles.reduce((a,b)=>a+b,0)/4;
      // Isolated mechanisms need a genuine underside view; the chassis floor
      // restriction otherwise clamps the impeller camera back to the horizon.
      orbit.maxPolarAngle=isolated?Math.PI-.04:Math.PI*.51;
      const camInspection=['cooling','drive'].includes(latest.current.focus)||latest.current.focus==='engine'&&['camdrive','timing','waterpump'].includes(latest.current.engineView);
      floor.visible=!camInspection;grid.visible=!camInspection;
      renderedRoot.position.y=isolated?0:t.suspension.heave-t.suspension.pitch*cx;
      renderedRoot.rotation.set(isolated?0:-t.suspension.roll,0,isolated?0:t.suspension.pitch);
      const onStand=!isolated&&(latest.current.terrain>0||t.suspension.travel.some(q=>Math.abs(q)>.001));
      floor.position.y=onStand?-.23:-.008;grid.position.y=floor.position.y+.001;
      testPads.forEach((pad,i)=>{pad.visible=onStand;pad.position.y=t.suspension.road[i]-.05;});
      const style=`${latest.current.coolingView}-${latest.current.coolingInternals}-${latest.current.waterCutaway}-${latest.current.startingView}-${latest.current.startingComponent}-${latest.current.mode}-${latest.current.wireframe}-${latest.current.engineView}-${latest.current.engineBank}-${latest.current.suspensionInternals}-${latest.current.suspensionWheel}-${latest.current.focus}`;
      if(style!==nativeStyle){nativeStyle=style;ao.updateGtaoMaterial({radius:camInspection?.015:.32,thickness:camInspection?.02:1});for(const o of nativeMeshes){const src=exportMaterials.get(o.name)!;let mat=src;if(latest.current.mode==='xray'&&nativeGhost.has(o))mat=ghost;
        if(d12Nodes.has(o.name)){
          const role=o.userData.d12Role,view=latest.current.engineView;
          o.visible=!(view==='valvetrain'&&role==='cover')&&!(view==='internals'&&['housing','timing-housing','cover','liner','pump-housing'].includes(role));
          if(view==='waterpump')o.visible=!!o.userData.waterPump&&role!=='water-pipe'&&(!latest.current.waterCutaway||o.userData.waterHalf!==1);
          if(view==='internals'&&o.userData.waterHalf===1)o.visible=false;
          if(view==='camdrive')o.visible=!!o.userData.camTrain&&(latest.current.engineBank==='both'||o.userData.camBank===latest.current.engineBank);
          if(view==='timing')o.visible=!!(o.userData.timingTrain||o.userData.camTrain)&&role!=='timing-housing';
          if(latest.current.mode==='xray'&&view==='assembled'&&['housing','cover','liner','pump-housing'].includes(role))mat=ghost;
        }
        if(startingNodes.has(o.name)){
          const view=latest.current.startingView,role=o.userData.startingRole,open=view!=='assembled'||latest.current.mode!=='solid';
          o.visible=!(view!=='assembled'&&role==='cover')&&(open||!['internal','envelope'].includes(role))&&!(view==='stator'&&role==='envelope');
          if(latest.current.mode==='xray'&&o.userData.startingRole==='cover')mat=ghost;
        }
        if(suspensionNodes.has(o.name)){
          const open=latest.current.suspensionInternals||latest.current.mode!=='solid',role=o.userData.s543Role;
          o.visible=!(latest.current.suspensionInternals&&role==='cover')&&!(!open&&['internal','torsion'].includes(role));
        }
        if(o.userData.coolingLegacyAux)o.visible=latest.current.focus!=='cooling';
        if(coolingNodes.has(o.name)){
          const role=o.userData.coolingRole;
          o.visible=!(latest.current.coolingInternals&&['housing','shroud','radiator','bearing-cover','clutch-cover'].includes(role));
          // These rolling elements, gears and windings sit behind opaque covers.
          // Keep their solved poses, but draw them only when those covers open
          // or the user requests x-ray/section inspection. External shafts and
          // mating flanges remain visible in the assembled view.
          const enclosed=/^COOL_(?:(?:lower|upper)_(?:ball_mesh_|ball_|cage_|bevel_|bearing_inner_|bearing_outer_)|needle_(?:inner_race_|\d)|coil_turn_|tank_partition_)/.test(o.name);
          if(enclosed&&!latest.current.coolingInternals&&latest.current.mode==='solid')o.visible=false;
          if(latest.current.focus==='cooling'&&latest.current.coolingView==='clutch'){
            let parent:T.Object3D|null=o;while(parent&&parent.name!=='COOL_fan_mount_0')parent=parent.parent;
            o.visible=o.visible&&!!parent&&!o.userData.upperGearbox&&!['fan-blade','fan-fastener','shroud'].includes(role);
          }
          if(latest.current.focus==='cooling'&&latest.current.coolingView==='lower')o.visible=o.visible&&!!o.userData.lowerDrive;
          if(latest.current.focus==='cooling'&&latest.current.coolingView==='upper')o.visible=o.visible&&!!o.userData.upperGearbox&&o.userData.upperSide===0&&role!=='support';
          if(latest.current.focus==='cooling'&&latest.current.coolingView==='cardan')o.visible=false;
          if(latest.current.focus==='cooling'&&latest.current.coolingView==='spring')o.visible=o.name==='COOL_release_spring_0';
          if(latest.current.mode==='xray'&&['housing','shroud','radiator','bearing-cover','clutch-cover'].includes(role))mat=ghost;
        }
        if(cardanNodes.has(o.name))o.visible=!(latest.current.coolingInternals&&['yoke','cover','seal','clip'].includes(o.userData.cardanRole));
        if(latest.current.mode==='section'){if(!clipMaterials.has(src)){const m=src.clone();m.clippingPlanes=[clip];m.clipShadows=true;m.side=T.DoubleSide;clipMaterials.set(src,m);}mat=clipMaterials.get(src)!;}
        o.material=mat;(mat as T.MeshStandardMaterial).wireframe=latest.current.wireframe;
      }
        // Closed opaque castings conceal these moving mechanisms. Cull their
        // draws while still solving the joints, and reveal them immediately in
        // cutaway or x-ray views. The exposed crankshaft/flywheel remains drawn.
        for(const [name,node] of d12Nodes){
          const bottom=/^D12_(?:piston_[LR]\d|master_rod_\d|slave_rod_\d)$/.test(name);
          const top=/^D12_(?:valve_[LR]\d_|spring_[LR]\d_|cam_[LR]_)/.test(name)&&!(node instanceof T.Mesh);
          const pump=/^D12_(?:injection_cam|pump_plunger_[LR]\d)$/.test(name);
          if(bottom||top||pump)node.visible=latest.current.mode!=='solid'||['internals','timing'].includes(latest.current.engineView)||(top&&['valvetrain','camdrive'].includes(latest.current.engineView));
        }
        for(const [name,node] of suspensionNodes){const match=/^S543_(\d)_/.exec(name);if(match&&node.parent?.name==='S543_SUSPENSION')node.visible=latest.current.focus!=='suspension'||latest.current.suspensionWheel<0||Number(match[1])===latest.current.suspensionWheel;}
      }
      if(lastSuspensionWheel!==latest.current.suspensionWheel){lastSuspensionWheel=latest.current.suspensionWheel;if(latest.current.focus==='suspension')focus('suspension');}
      const startingInspection=`${latest.current.startingComponent}-${latest.current.startingView}`;
      const engineInspection=`${latest.current.engineView}-${latest.current.engineBank}`;
      if(lastEngineInspection!==engineInspection){lastEngineInspection=engineInspection;if(latest.current.focus==='engine')needsFocus=true;}
      if(lastStartingComponent!==startingInspection){lastStartingComponent=startingInspection;if(latest.current.focus==='starting')needsFocus=true;}
      if(lastCoolingView!==latest.current.coolingView){lastCoolingView=latest.current.coolingView;if(latest.current.focus==='cooling')needsFocus=true;}
      if(lastFocus!==latest.current.focus){lastFocus=latest.current.focus;needsFocus=true;}
      if(needsFocus){needsFocus=false;if(latest.current.focus)focus(latest.current.focus);else frame(renderedRoot,camera.position.clone().sub(orbit.target).normalize());}
      for(const mat of new Set(exportMaterials.values())){if(mat.name==='Headlamp_prismatic_glass')(mat as T.MeshStandardMaterial).emissiveIntensity=latest.current.lights?2.5:.04;}
      grid.position.x=((t.distance%1)+1)%1;
      if(transition){camera.position.lerp(transition.position,.1);orbit.target.lerp(transition.target,.1);if(camera.position.distanceTo(transition.position)<.015)transition=null;}
      orbit.update();
      lastSelected=selection.current;const selectedPart=displayParts.find(p=>p.id===lastSelected);
      selector.visible=!!selectedPart&&!latest.current.focus;
      if(selector.visible&&selectedPart)selector.box.copy(visibleBounds(selectedPart.group));
      for(const p of displayParts){const el=labelNodes.get(p.id);if(!el)continue;if(!latest.current.labels||!p.group.visible){el.style.display='none';continue;}const pos=new T.Box3().setFromObject(p.group).getCenter(new T.Vector3());pos.y+=.3;pos.project(camera);el.style.display=pos.z<1&&Math.abs(pos.x)<.92&&Math.abs(pos.y)<.9?'block':'none';el.style.left=`${(pos.x*.5+.5)*host.clientWidth}px`;el.style.top=`${(-pos.y*.5+.5)*host.clientHeight}px`;}
      if(gpuTimer&&pendingTimers.length&&gl.getQueryParameter(pendingTimers[0],gl.QUERY_RESULT_AVAILABLE)){
        const q=pendingTimers.shift()!;if(!gl.getParameter(gpuTimer.GPU_DISJOINT_EXT))gpuMs=Number(gl.getQueryParameter(q,gl.QUERY_RESULT))/1e6;gl.deleteQuery(q);
      }
      const query=gpuTimer&&timerFrame++%30===0&&pendingTimers.length<3?gl.createQuery():null;
      if(query&&gpuTimer)gl.beginQuery(gpuTimer.TIME_ELAPSED_EXT,query);
      ao.enabled=latest.current.mode==='solid'&&!latest.current.wireframe&&renderInspection!=='no-ao';renderer.info.reset();composer.render();
      if(query&&gpuTimer){gl.endQuery(gpuTimer.TIME_ELAPSED_EXT);pendingTimers.push(query);}
      statsFrames++;if(now-statsTime>=1000){stats={fps:statsFrames*1000/(now-statsTime),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,gpu,gpuMs};statsFrames=0;statsTime=now;}
      if(now-lastReport>150){
        const pixelsPerMetre=host.clientHeight/(2*Math.tan(camera.fov*Math.PI/360)*camera.position.distanceTo(orbit.target));
        const metres=[.001,.002,.005,.01,.02,.05,.1,.2,.5,1,2,5,10,20].filter(m=>m*pixelsPerMetre<=95).at(-1)??.001;
        lastReport=now;callbacks.current.onTelemetry({...t,renderStats:stats,viewScale:{metres,pixels:metres*pixelsPerMetre}});
      }
    }
    handle=requestAnimationFrame(animate);
    return ()=>{disposed=true;cancelAnimationFrame(handle);pendingTimers.forEach(q=>gl.deleteQuery(q));observer.disconnect();orbit.dispose();draco.dispose();model.dispose();nativeMeshes.forEach(m=>m.geometry.dispose());new Set(exportMaterials.values()).forEach(m=>m.dispose());clipMaterials.forEach(m=>m.dispose());ghost.dispose();composer.dispose();ao.dispose();selector.geometry.dispose();(selector.material as T.Material).dispose();floor.geometry.dispose();floor.material.dispose();padGeometry.dispose();padMaterial.dispose();grid.geometry.dispose();(grid.material as T.Material).dispose();env.dispose();pmrem.dispose();renderer.dispose();renderer.domElement.remove();labelNodes.forEach(el=>el.remove());api.current=null;};
  },[api]);
  return <div className="three-surface" ref={container}/>;
}

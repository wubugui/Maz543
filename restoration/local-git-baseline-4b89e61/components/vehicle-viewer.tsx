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
    renderer.domElement.setAttribute('aria-label','MAZ-543 三维模型：拖动旋转，滚轮缩放，点击选择部件');
    const scene=new T.Scene();scene.background=new T.Color('#333b3a');scene.fog=new T.Fog('#333b3a',28,65);
    const camera=new T.PerspectiveCamera(35,1,.05,120);camera.position.set(-12,7.5,12);
    const orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(-.2,1.1,0);orbit.enableDamping=true;orbit.dampingFactor=.08;orbit.minDistance=1.2;orbit.maxDistance=28;orbit.maxPolarAngle=Math.PI*.51;orbit.update();
    const pmrem=new T.PMREMGenerator(renderer),room=new RoomEnvironment();const env=pmrem.fromScene(room,.05);scene.environment=env.texture;scene.environmentIntensity=.55;room.dispose();
    const ambient=new T.HemisphereLight('#dce5e8','#626357',1.1);scene.add(ambient);
    const key=new T.DirectionalLight('#fff8ea',2.6);key.position.set(-7,13,7);key.castShadow=true;key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-10;key.shadow.camera.right=10;key.shadow.camera.top=9;key.shadow.camera.bottom=-9;key.shadow.normalBias=.016;key.shadow.bias=-.00006;key.shadow.camera.far=40;scene.add(key);
    const rim=new T.DirectionalLight('#c8d9e3',1.9);rim.position.set(3,6,-9);scene.add(rim);
    const fill=new T.DirectionalLight('#ede6d6',.7);fill.position.set(-9,3,-3);scene.add(fill);
    const floor=new T.Mesh(new T.PlaneGeometry(160,160),new T.MeshStandardMaterial({color:'#4b5450',roughness:.93,metalness:.025}));floor.rotation.x=-Math.PI/2;floor.position.y=-.008;floor.receiveShadow=true;scene.add(floor);
    const grid=new T.GridHelper(80,80,'#68736d','#505b56');grid.position.y=-.007;(grid.material as T.Material).transparent=true;(grid.material as T.Material).opacity=.11;scene.add(grid);
    const model=createMAZ543();scene.add(model.root);
    let renderedRoot=model.root,displayParts=model.parts,exportMaterials=model.originalMaterials,disposed=false;
    const bindings:{source:T.Object3D;target:T.Object3D}[]=[];
    const ghost=new T.MeshStandardMaterial({color:'#a6bab1',transparent:true,opacity:.055,depthWrite:false,roughness:.6,side:T.DoubleSide});
    const clip=new T.Plane(new T.Vector3(0,0,-1),0),clipMaterials=new Map<T.Material,T.Material>();
    const nativeMeshes:T.Mesh[]=[],nativeGhost=new Set<T.Mesh>();let nativeStyle='';
    const draco=new DRACOLoader();draco.setDecoderPath('/draco/');draco.setWorkerLimit(2);const loader=new GLTFLoader();loader.setDRACOLoader(draco);
    loader.loadAsync('/models/maz543a-blender.glb?v=blender-final-4').then(gltf=>{
      if(disposed)return;
      renderedRoot=(gltf.scene.getObjectByName('MAZ543_REFERENCE_CHASSIS')||gltf.scene) as T.Group;
      scene.remove(model.root);scene.add(renderedRoot);exportMaterials=new Map();
      renderedRoot.traverse(o=>{const source=model.root.getObjectByName(o.name);if(source)bindings.push({source,target:o});if(o instanceof T.Mesh){o.castShadow=true;o.receiveShadow=true;nativeMeshes.push(o);exportMaterials.set(o.name,o.material as T.Material);
        if(o.userData.surface==='exterior'||model.ghostNames.has(o.name)||/BL_.*(?:Tyre|Rim|Hub|Wheel|Merged_wheels)/.test(o.name))nativeGhost.add(o);
        if((o.material as T.MeshStandardMaterial).map)(o.material as T.MeshStandardMaterial).map!.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
      }});
      displayParts=model.parts.map(p=>({...p,group:(renderedRoot.getObjectByName(p.id)||p.group) as T.Group}));
      const count=nativeMeshes.reduce((n,m)=>n+(m.userData.detail_meshes||1),0);callbacks.current.onError('');callbacks.current.onReady(displayParts,count);
    }).catch(()=>{if(!disposed)callbacks.current.onError('Blender 模型未能加载。请刷新重试；需要下载完整三维资产与贴图。');});
    let t={...INITIAL_TELEMETRY};model.update(latest.current,t);
    const selector=new T.BoxHelper(model.root,0xe5a369);(selector.material as T.LineBasicMaterial).transparent=true;(selector.material as T.LineBasicMaterial).opacity=.35;selector.visible=false;scene.add(selector);
    const labelNodes=new Map<string,HTMLButtonElement>();
    for(const p of model.parts){const el=document.createElement('button');el.className='model-label';el.textContent=p.name;el.onclick=()=>callbacks.current.onSelect(p.id);el.style.display='none';host.appendChild(el);labelNodes.set(p.id,el);}
    let transition:{position:T.Vector3;target:T.Vector3}|null=null;
    const views:Record<string,[number,number,number]>={perspective:[-12,7.5,12],front:[-17,3,0],side:[0,3,18],top:[0,19,.001],rear:[15,4,8],under:[-9,.35,10]};
    function view(name:string){transition={position:new T.Vector3(...(views[name]||views.perspective)),target:new T.Vector3(-.2,1.1,0)};}
    function focus(id:string){const part=displayParts.find(p=>p.id===id);if(!part){view('perspective');return;}const bounds=new T.Box3().setFromObject(part.group),center=bounds.getCenter(new T.Vector3()),size=bounds.getSize(new T.Vector3());const dist=Math.max(size.x,size.y,size.z)*1.6+1;const direction=camera.position.clone().sub(orbit.target).normalize();transition={position:center.clone().addScaledVector(direction,dist),target:center};}
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
    const resize=()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h);composer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};
    const observer=new ResizeObserver(resize);observer.observe(host);resize();
    let handle=0,last=performance.now(),lastReport=0,lastSelected='';
    function animate(now:number){handle=requestAnimationFrame(animate);if(document.hidden){last=now;return;}const dt=Math.min((now-last)/1000,.05);last=now;t=advance(t,latest.current,dt);model.update(latest.current,t);
      for(const {source,target} of bindings){target.position.copy(source.position);target.quaternion.copy(source.quaternion);target.scale.copy(source.scale);target.visible=source.visible;}
      const style=`${latest.current.mode}-${latest.current.wireframe}`;
      if(style!==nativeStyle){nativeStyle=style;for(const o of nativeMeshes){const src=exportMaterials.get(o.name)!;let mat=src;if(latest.current.mode==='xray'&&nativeGhost.has(o))mat=ghost;
        if(latest.current.mode==='section'){if(!clipMaterials.has(src)){const m=src.clone();m.clippingPlanes=[clip];m.clipShadows=true;m.side=T.DoubleSide;clipMaterials.set(src,m);}mat=clipMaterials.get(src)!;}
        o.material=mat;(mat as T.MeshStandardMaterial).wireframe=latest.current.wireframe;
      }}
      for(const mat of new Set(exportMaterials.values())){if(mat.name==='Headlamp_prismatic_glass')(mat as T.MeshStandardMaterial).emissiveIntensity=latest.current.lights?2.5:.04;}
      grid.position.x=((t.distance%1)+1)%1;
      if(transition){camera.position.lerp(transition.position,.1);orbit.target.lerp(transition.target,.1);if(camera.position.distanceTo(transition.position)<.015)transition=null;}
      orbit.update();
      if(selection.current!==lastSelected){lastSelected=selection.current;const p=displayParts.find(p=>p.id===lastSelected);if(p){selector.setFromObject(p.group);selector.visible=true;}else selector.visible=false;}
      if(selector.visible){const p=displayParts.find(p=>p.id===lastSelected);if(p)selector.setFromObject(p.group);}
      for(const p of displayParts){const el=labelNodes.get(p.id)!;if(!latest.current.labels||!p.group.visible){el.style.display='none';continue;}const pos=new T.Box3().setFromObject(p.group).getCenter(new T.Vector3());pos.y+=.3;pos.project(camera);el.style.display=pos.z<1&&Math.abs(pos.x)<.92&&Math.abs(pos.y)<.9?'block':'none';el.style.left=`${(pos.x*.5+.5)*host.clientWidth}px`;el.style.top=`${(-pos.y*.5+.5)*host.clientHeight}px`;}
      ao.enabled=latest.current.mode==='solid'&&!latest.current.wireframe;composer.render();if(now-lastReport>150){lastReport=now;callbacks.current.onTelemetry({...t});}
    }
    handle=requestAnimationFrame(animate);
    return ()=>{disposed=true;cancelAnimationFrame(handle);observer.disconnect();orbit.dispose();draco.dispose();model.dispose();nativeMeshes.forEach(m=>m.geometry.dispose());new Set(exportMaterials.values()).forEach(m=>m.dispose());clipMaterials.forEach(m=>m.dispose());ghost.dispose();composer.dispose();ao.dispose();selector.geometry.dispose();(selector.material as T.Material).dispose();floor.geometry.dispose();floor.material.dispose();grid.geometry.dispose();(grid.material as T.Material).dispose();env.dispose();pmrem.dispose();renderer.dispose();renderer.domElement.remove();labelNodes.forEach(el=>el.remove());api.current=null;};
  },[api]);
  return <div className="three-surface" ref={container}/>;
}

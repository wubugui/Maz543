import * as T from 'three';
import {SimplexNoise} from 'three/addons/math/SimplexNoise.js';
import type {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {createContextSourceOrder} from './contextSourceOrder';

/** Same r183 Simplex noise texture recipe, with an audit-only fixed random
 * source. Two independent contexts need identical AO input data to compare.
 * Ordinary rendering keeps the stock constructor and its random texture. */
export function installContextAuditNoise(ao:GTAOPass){
  let seed=0x543a2026;
  const simplex=new SimplexNoise({random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/0x100000000;}});
  const size=64,data=new Uint8Array(size*size*4);
  for(let i=0;i<size;i++)for(let j=0;j<size;j++){
    const offset=(i*size+j)*4;
    data[offset]=(simplex.noise(i,j)*.5+.5)*255;
    data[offset+1]=(simplex.noise(i+size,j)*.5+.5)*255;
    data[offset+2]=(simplex.noise(i,j+size)*.5+.5)*255;
    data[offset+3]=(simplex.noise(i+size,j+size)*.5+.5)*255;
  }
  const texture=new T.DataTexture(data,size,size,T.RGBAFormat,T.UnsignedByteType);
  texture.wrapS=T.RepeatWrapping;texture.wrapT=T.RepeatWrapping;texture.needsUpdate=true;
  ao.pdNoiseTexture.dispose();ao.pdNoiseTexture=texture;ao.pdMaterial.uniforms.tNoise.value=texture;
  return data;
}

const digest=async(data:Uint8Array)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data as Uint8Array<ArrayBuffer>)),v=>v.toString(16).padStart(2,'0')).join('');
const encode=(value:unknown)=>new TextEncoder().encode(JSON.stringify(value));

/** Finite readback and fingerprints; no frame data is put into conversation
 * history. Context IDs and material allocation IDs are deliberately excluded
 * from input fingerprints. Actual source draw order is hashed separately. */
export function createContextFrameAudit(renderer:T.WebGLRenderer,scene:T.Scene,camera:T.Camera,ao:GTAOPass,noise:Uint8Array,host:HTMLDivElement,document:Pick<Document,'createElement'>){
  const button=document.createElement('button'),sourceButton=document.createElement('button'),output=document.createElement('pre'),traceOutput=document.createElement('pre');
  traceOutput.dataset.contextFrameTrace='1';traceOutput.style.display='none';host.appendChild(traceOutput);
  button.textContent='核对当前渲染上下文';button.style.cssText='position:absolute;z-index:11;left:12px;top:145px;padding:7px;background:#263d32;color:white';
  sourceButton.textContent='核对固定源顺序';sourceButton.style.cssText='position:absolute;z-index:11;left:200px;top:145px;padding:7px;background:#263d32;color:white';host.appendChild(sourceButton);
  output.setAttribute('aria-label','跨上下文完整帧指纹');output.style.cssText='position:absolute;z-index:10;left:12px;top:185px;max-width:90%;max-height:45%;overflow:auto;background:#111e;color:#ddd;padding:12px;font-size:11px';
  output.textContent='等待完整模型；审计使用相同固定噪声输入，普通预览不变。';host.appendChild(button);host.appendChild(output);
  let armed=false,disposed=false,generation=0,sourceOrderRequested=false;
  button.onclick=()=>{armed=true;sourceOrderRequested=false;output.textContent='等待下一完整姿态并读取当前上下文。';};
  sourceButton.onclick=()=>{armed=true;sourceOrderRequested=true;output.textContent='等待下一完整姿态并核对固定源排序；仅此诊断帧。';};
  return {
    shouldCapture(loaded:boolean){return !disposed&&armed&&loaded;},
    capture(draw:()=>void,details:Record<string,unknown>){
      armed=false;const captureGeneration=++generation;
      const ids=new Map<T.Object3D,number>(),inputs:unknown[]=[],sourceOrder:unknown[]=[];
      scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
      scene.traverse(o=>{
        ids.set(o,ids.size);
        if(!(o instanceof T.Mesh))return;
        const materials=Array.isArray(o.material)?o.material:[o.material];
        sourceOrder.push({sceneId:ids.get(o),name:o.name,objectId:o.id,renderOrder:o.renderOrder,materials:materials.map(m=>({name:m.name,id:(m as T.Material&{id:number}).id}))});
        const attributes=o.geometry.attributes as Record<string,T.BufferAttribute|T.InterleavedBufferAttribute>;
        inputs.push({name:o.name,parent:o.parent?.name,visible:o.visible,layers:o.layers.mask,castShadow:o.castShadow,receiveShadow:o.receiveShadow,
          matrix:[...o.matrixWorld.elements],morph:[...(o.morphTargetInfluences??[])],
          attributes:Object.fromEntries(Object.entries(attributes).map(([key,a])=>[key,[a.count,a.itemSize,a.normalized,a.array.constructor.name]])),
          indices:o.geometry.index?.count??0,groups:o.geometry.groups,drawRange:o.geometry.drawRange,
          materials:materials.map(value=>{
            const m=value as T.MeshPhysicalMaterial;
            return {name:m.name,type:m.type,visible:m.visible,side:m.side,transparent:m.transparent,opacity:m.opacity,depthWrite:m.depthWrite,depthTest:m.depthTest,
              color:m.color?.toArray(),roughness:m.roughness,metalness:m.metalness,transmission:m.transmission,thickness:m.thickness,ior:m.ior,
              clipping:m.clippingPlanes?.map(p=>[...p.normal.toArray(),p.constant])};
          })});
      });
      const view={projection:[...camera.projectionMatrix.elements],world:[...camera.matrixWorld.elements],layers:camera.layers.mask};
      const sequence:unknown[]=[];const original=renderer.renderBufferDirect;
      renderer.renderBufferDirect=function(...args){
        const [passCamera,passScene,geometry,material,object,group]=args,target=renderer.getRenderTarget();
        sequence.push([ids.get(object)??-1,object.name,material.name,material.type,material.side,passCamera===camera?'main':'other',!!passScene?.overrideMaterial,
          target?.width??0,target?.height??0,target?.samples??0,geometry.index?.count??geometry.attributes.position?.count??0,group]);
        return original.apply(renderer,args);
      };
      const canonical=sourceOrderRequested?createContextSourceOrder(scene):null;
      if(canonical){renderer.setOpaqueSort(canonical.opaque);renderer.setTransparentSort(canonical.transparent);}
      try{draw();}finally{
        renderer.renderBufferDirect=original;
        // This inspection mode otherwise uses stock sorting, and is mutually
        // exclusive with the ordered batching experiment.
        if(canonical){renderer.setOpaqueSort(null!);renderer.setTransparentSort(null!);}
      }
      const gl=renderer.getContext(),width=gl.drawingBufferWidth,height=gl.drawingBufferHeight,pixels=new Uint8Array(width*height*4);
      gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);const readbackError=gl.getError();
      const report={...details,sorting:canonical?'source-scene-order':'stock-allocation-order',width,height,pixelRatio:renderer.getPixelRatio(),meshes:inputs.length,draws:renderer.info.render.calls,triangles:renderer.info.render.triangles,
        readbackError,view,ao:{enabled:ao.enabled,samples:ao.gtaoMaterial.defines.SAMPLES,blendIntensity:ao.blendIntensity},
        limits:'Exact RGBA fingerprint of this current context and pose, fixed audit-only stock-recipe AO noise. Input fingerprint covers transforms/material subset and geometry layouts, not all geometry bytes or every shader input. Asset/source checks and actual pixel equality remain separate requirements.'};
      output.textContent='正在计算已读取完整帧的 SHA-256。';
      void Promise.all([digest(pixels),digest(encode(inputs)),digest(encode(sequence)),digest(noise)]).then(([pixelSha256,sceneInputSha256,drawSequenceSha256,noiseSha256])=>{
        if(!disposed&&captureGeneration===generation){
          const result={...report,pixelSha256,sceneInputSha256,drawSequenceSha256,noiseSha256};
          // Finite diagnostic DOM artifact, read to a local file without adding
          // the full draw list to the visible overlay or conversation history.
          traceOutput.textContent=JSON.stringify({report:result,sourceOrder,sequence});
          output.textContent=JSON.stringify(result,null,2);
        }
      }).catch(error=>{if(!disposed&&captureGeneration===generation)output.textContent=JSON.stringify({error:String(error)});});
    },
    dispose(){disposed=true;generation++;button.onclick=null;sourceButton.onclick=null;button.remove();sourceButton.remove();output.remove();traceOutput.remove();},
  };
}

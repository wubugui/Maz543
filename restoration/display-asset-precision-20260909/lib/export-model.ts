import * as T from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import {useBinaryGltfBlob} from './binaryGltfBlob';
import {prepareExportTangents} from './exportTangents';

function prepareExport(root:T.Group,originalMaterials:Map<string,T.Material>,progress?:(stage:string)=>void){
  const scene=new T.Scene();scene.name='MAZ543_REFERENCE';const copy=root.clone(true);scene.add(copy);
  const materials=new Map<T.Material,T.Material>();
  const geometries=new Map<T.BufferGeometry,T.BufferGeometry>();let repaired=0,unresolved=0;
  copy.traverse(o=>{
    if(!(o instanceof T.Mesh))return;
    if(!geometries.has(o.geometry)){const prepared=prepareExportTangents(o.geometry);geometries.set(o.geometry,prepared.geometry);repaired+=prepared.audit.repaired;unresolved+=prepared.audit.unresolved;}
    o.geometry=geometries.get(o.geometry)!;
    const src=originalMaterials.get(o.name)||(o.material as T.Material);
    if(!materials.has(src)){const mat=(src as T.MeshStandardMaterial).clone();mat.clippingPlanes=null;mat.wireframe=false;if(mat.map instanceof T.DataTexture)mat.map=null;if(mat.bumpMap instanceof T.DataTexture)mat.bumpMap=null;if(mat.roughnessMap instanceof T.DataTexture)mat.roughnessMap=null;materials.set(src,mat);}
    o.material=materials.get(src)!;
  });
  progress?.(`export-tangents:repaired=${repaired}:unresolved=${unresolved}`);
  return {scene,dispose:()=>{materials.forEach(mat=>mat.dispose());geometries.forEach((copy,source)=>{if(copy!==source)copy.dispose();});}};
}

export async function exportGLB(root:T.Group, originalMaterials:Map<string,T.Material>, animations:T.AnimationClip[]=[],progress?:(stage:string)=>void) {
  progress?.('copy-model');const prepared=prepareExport(root,originalMaterials,progress),{scene}=prepared;
  const exporter=new GLTFExporter();
  if(progress)exporter.register(writer=>({beforeParse:()=>{progress('encode-geometry');},afterParse:()=>{
    const pending=(writer as unknown as {pending:Promise<unknown>[]}).pending;
    progress(`encode-images-and-binary:${pending.length}`);
    void Promise.allSettled(pending).then(results=>progress(`images-settled:${results.filter(result=>result.status==='fulfilled').length}/${results.length}`));
  }}));
  try{const data=await exporter.parseAsync(scene,{binary:true,onlyVisible:true,animations}) as ArrayBuffer;progress?.(`encoded:${data.byteLength}`);return data;}
  finally{prepared.dispose();}
}

export async function exportGLBBlob(root:T.Group,originalMaterials:Map<string,T.Material>,animations:T.AnimationClip[]=[],progress?:(stage:string)=>void){
  progress?.('copy-model');const prepared=prepareExport(root,originalMaterials,progress),exporter=new GLTFExporter();
  useBinaryGltfBlob(exporter,progress);
  try{
    // parse's public result type is ArrayBuffer; the instance-local finalizer
    // above deliberately returns the same GLB bytes as a Blob instead.
    const result=await exporter.parseAsync(prepared.scene,{binary:true,onlyVisible:true,animations}) as unknown as Blob;
    if(!(result instanceof Blob))throw new Error('GLB Blob 封装未生效');progress?.(`encoded:${result.size}`);return result;
  }finally{prepared.dispose();}
}

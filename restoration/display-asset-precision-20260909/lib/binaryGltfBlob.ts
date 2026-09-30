import type {GLTFExporter,GLTFExporterOptions} from 'three/addons/exporters/GLTFExporter.js';
import type {Object3D} from 'three';

/** Assemble the glTF 2.0 container without reading the complete binary payload
 * back into JavaScript twice. Every already-encoded byte is retained. */
export function assembleBinaryGltf(json:object,binaryParts:BlobPart[]):Blob{
  const binary=new Blob(binaryParts,{type:'application/octet-stream'});
  const jsonBytes=new TextEncoder().encode(JSON.stringify(json));
  const jsonPadding=(4-jsonBytes.length%4)%4,binaryPadding=(4-binary.size%4)%4;
  const jsonLength=jsonBytes.length+jsonPadding,binaryLength=binary.size+binaryPadding,total=12+8+jsonLength+8+binaryLength;
  if(total>0xffffffff)throw new Error('GLB 超出格式允许的 32 位长度；未截断任何模型数据');
  const header=new ArrayBuffer(12),jsonPrefix=new ArrayBuffer(8),binaryPrefix=new ArrayBuffer(8);
  const h=new DataView(header),j=new DataView(jsonPrefix),b=new DataView(binaryPrefix);
  h.setUint32(0,0x46546c67,true);h.setUint32(4,2,true);h.setUint32(8,total,true);
  j.setUint32(0,jsonLength,true);j.setUint32(4,0x4e4f534a,true);b.setUint32(0,binaryLength,true);b.setUint32(4,0x004e4942,true);
  return new Blob([header,jsonPrefix,jsonBytes,new Uint8Array(jsonPadding).fill(0x20),binaryPrefix,binary,new Uint8Array(binaryPadding)],{type:'model/gltf-binary'});
}

type BinaryWriter={
  options:GLTFExporterOptions;
  pending:Promise<unknown>[];
  buffers:BlobPart[];
  json:{buffers?:{byteLength:number}[];extensionsUsed?:string[];extensionsRequired?:string[]};
  extensionsUsed:Record<string,boolean>;extensionsRequired:Record<string,boolean>;
  processInputAsync:(input:Object3D|Object3D[])=>Promise<void>;
  writeAsync:(input:Object3D|Object3D[],onDone:(result:Blob)=>void,options?:GLTFExporterOptions)=>Promise<void>;
};

/** Instance-local finalization adapter for Three r183's exporter writer.
 * Its stock scene/accessor/material/image/morph/animation encoders and plugins
 * still run. Only the two whole-payload FileReader copies are replaced.
 * This internal writer contract must be rechecked when Three is upgraded. */
export function useBinaryGltfBlob(exporter:GLTFExporter,progress?:(stage:string)=>void){
  exporter.register(publicWriter=>{
    const writer=publicWriter as unknown as BinaryWriter;
    if(!Array.isArray(writer.buffers)||!Array.isArray(writer.pending)||typeof writer.processInputAsync!=='function'||typeof writer.writeAsync!=='function')throw new Error('GLTFExporter 写入接口已变化，无法保证无损封装');
    writer.writeAsync=async(input,onDone,options={})=>{
      writer.options={binary:true,trs:false,onlyVisible:true,maxTextureSize:Infinity,animations:[],includeCustomExtensions:false,...options};
      if(writer.options.animations!.length>0)writer.options.trs=true;
      progress?.('encode-geometry');await writer.processInputAsync(input);
      progress?.(`encode-images:${writer.pending.length}`);await Promise.all(writer.pending);
      const binary=new Blob(writer.buffers,{type:'application/octet-stream'}),json=writer.json;
      const used=Object.keys(writer.extensionsUsed),required=Object.keys(writer.extensionsRequired);
      if(used.length)json.extensionsUsed=used;if(required.length)json.extensionsRequired=required;
      if(json.buffers?.length)json.buffers[0].byteLength=binary.size;
      progress?.(`assemble-binary-blob:${binary.size}`);onDone(assembleBinaryGltf(json,[binary]));
    };
    return {};
  });
}

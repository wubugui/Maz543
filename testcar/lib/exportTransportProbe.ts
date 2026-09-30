/** Development-only capability probe for an export that stalls after geometry.
 * Uses a 1-pixel canvas and a 4-byte Blob; never touches vehicle geometry. */
export function probeWorkerExportTransport(report:(stage:string)=>void){
  const blob=new Blob([new Uint8Array([0,1,2,255])]);
  void blob.arrayBuffer().then(data=>report(`probe:blob-array-buffer:${data.byteLength}`),error=>report(`probe:blob-error:${error}`));
  const reader=new FileReader();
  reader.onloadend=()=>report(`probe:file-reader:${reader.result instanceof ArrayBuffer?reader.result.byteLength:reader.error?.message}`);
  reader.onerror=()=>report(`probe:file-reader-error:${reader.error?.message}`);reader.readAsArrayBuffer(blob);
  const canvas=new OffscreenCanvas(1,1),context=canvas.getContext('2d')!;context.fillStyle='#678123';context.fillRect(0,0,1,1);
  void canvas.convertToBlob({type:'image/png'}).then(data=>report(`probe:canvas-png:${data.size}`),error=>report(`probe:canvas-error:${error}`));
  void (async()=>{
    const T=await import('three'),{exportGLB,exportGLBBlob}=await import('./export-model');
    const bitmap=await createImageBitmap(canvas),texture=new T.Texture(bitmap);texture.needsUpdate=true;texture.flipY=false;
    const material=new T.MeshStandardMaterial({map:texture}),geometry=new T.BoxGeometry(.1,.2,.3),mesh=new T.Mesh(geometry,material),root=new T.Group();mesh.name='image-probe';root.add(mesh);
    try{const original=new Uint8Array(await exportGLB(root,new Map([[mesh.name,material]]))),candidate=new Uint8Array(await(await exportGLBBlob(root,new Map([[mesh.name,material]]))).arrayBuffer());
      const equal=original.length===candidate.length&&original.every((value,index)=>value===candidate[index]);report(`probe:textured-glb-byte-equality:${equal}:${candidate.length}`);
    }finally{geometry.dispose();material.dispose();texture.dispose();bitmap.close();}
  })().catch(error=>report(`probe:textured-glb-error:${error}`));
}

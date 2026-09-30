import * as T from 'three';

export type ExportTangentAudit={candidates:number;repaired:number;unresolved:number};
/** Repair quantized zero tangents only when the vertex cannot belong to any
 * surface triangle: every incident triangle has an exactly duplicated position
 * pair, also identical in every morph target. No epsilon/culling assumption.
 * The authoritative geometry is untouched; only an export wrapper and its
 * tangent attribute are allocated. All other attributes/indices are shared. */
export function prepareExportTangents(source:T.BufferGeometry):{geometry:T.BufferGeometry;audit:ExportTangentAudit}{
  const position=source.getAttribute('position'),normal=source.getAttribute('normal'),tangent=source.getAttribute('tangent');
  const audit:ExportTangentAudit={candidates:0,repaired:0,unresolved:0};
  if(!position||!normal||!tangent||tangent.itemSize!==4||normal.count!==position.count||tangent.count!==position.count)return {geometry:source,audit};
  const candidate=new Uint8Array(position.count);
  for(let i=0;i<tangent.count;i++)if(Math.hypot(tangent.getX(i),tangent.getY(i),tangent.getZ(i))<.01){candidate[i]=1;audit.candidates++;}
  if(!audit.candidates)return {geometry:source,audit};
  // Skinning can separate equal positions; unknown/non-triangle input is not
  // eligible. Quantized zero tangents came from float Draco attributes here.
  if(source.hasAttribute('skinIndex')||source.hasAttribute('skinWeight')||!(tangent instanceof T.BufferAttribute)||!(tangent.array instanceof Float32Array))return {geometry:source,audit:{...audit,unresolved:audit.candidates}};
  const index=source.getIndex(),count=index?.count??position.count;
  if(count%3)return {geometry:source,audit:{...audit,unresolved:audit.candidates}};
  const attributes=[position,...(source.morphAttributes.position??[])];
  if(attributes.some(attribute=>attribute.count!==position.count))return {geometry:source,audit:{...audit,unresolved:audit.candidates}};
  const equal=(a:number,b:number)=>attributes.every(attribute=>attribute.getX(a)===attribute.getX(b)&&attribute.getY(a)===attribute.getY(b)&&attribute.getZ(a)===attribute.getZ(b));
  const safe=candidate.slice();
  for(let i=0;i<count;i+=3){const a=index?index.getX(i):i,b=index?index.getX(i+1):i+1,c=index?index.getX(i+2):i+2;
    if(!(candidate[a]||candidate[b]||candidate[c]))continue;
    if(!(equal(a,b)||equal(b,c)||equal(c,a))){safe[a]=0;safe[b]=0;safe[c]=0;}
  }
  let replacement:T.BufferAttribute|undefined;
  const n=new T.Vector3(),axis=new T.Vector3(),direction=new T.Vector3();
  for(let i=0;i<safe.length;i++)if(safe[i]){
    n.fromBufferAttribute(normal,i);if(!Number.isFinite(n.lengthSq())||n.lengthSq()===0)continue;
    // A stable orthogonal unit frame for a triangle with no surface. Its UV
    // derivative is undefined; do not amplify the tiny Draco quantization noise.
    const x=Math.abs(n.x),y=Math.abs(n.y),z=Math.abs(n.z);axis.set(x<=y&&x<=z?1:0,y<x&&y<=z?1:0,z<x&&z<y?1:0);
    direction.crossVectors(n,axis).normalize();if(!replacement)replacement=tangent.clone();replacement.setXYZ(i,direction.x,direction.y,direction.z);audit.repaired++;
  }
  audit.unresolved=audit.candidates-audit.repaired;if(!replacement)return {geometry:source,audit};
  const geometry=new T.BufferGeometry();geometry.name=source.name;geometry.index=source.index;geometry.attributes={...source.attributes,tangent:replacement};
  geometry.morphAttributes={...source.morphAttributes};geometry.morphTargetsRelative=source.morphTargetsRelative;geometry.groups=source.groups.map(group=>({...group}));geometry.drawRange={...source.drawRange};geometry.boundingBox=source.boundingBox;geometry.boundingSphere=source.boundingSphere;geometry.userData={...source.userData};
  return {geometry,audit};
}

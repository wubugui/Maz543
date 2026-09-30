import * as T from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { SPECS, steeringAngles, pistonPosition, type Controls, type Telemetry } from './mechanics';

type V3 = [number, number, number];
export type PartInfo = { id: string; name: string; english: string; detail: string; motion: string; fidelity: string; color: string; group: T.Group };
type Link = { mesh: T.Mesh; start: V3; wheel: number; end: V3 };
export function createMAZ543() {
  const root = new T.Group(); root.name = 'MAZ543_REFERENCE_CHASSIS';
  root.userData = {units:'metres', accuracy:'Reference reconstruction; estimated geometry; not factory CAD', source:'https://djvu.online/file/zjMdLY3MFjmTL'};
  const parts: PartInfo[] = [], exterior: T.Object3D[] = [], shells: T.Mesh[] = [], rotors: {object:T.Object3D; axis:'x'|'y'|'z'; rate:number}[] = [];
  const wheels: {carrier:T.Group; spin:T.Group; x:number; side:number; hub:T.Group; brake:T.Group}[] = [];
  const doors: {group:T.Group; side:number}[] = [];
  const pistons: {piston:T.Group; rod:T.Mesh; bank:number; phase:number; x:number}[] = [];
  const valves: {mesh:T.Mesh; origin:T.Vector3; axis:T.Vector3; phase:number; exhaust:boolean}[] = [];
  const links: Link[] = []; const fans:T.Group[] = []; const steeringWheels:T.Group[] = [];
  const geometries = new Map<string,T.BufferGeometry>();
  const geom = (key:string, fn:()=>T.BufferGeometry) => {if(!geometries.has(key))geometries.set(key,fn());return geometries.get(key)!;};
  const material = (color:string, metalness=.2, roughness=.6) => new T.MeshStandardMaterial({color,metalness,roughness});
  const m = {
    olive:material('#596147',.25,.72), edge:material('#727a59',.3,.65), dark:material('#252c27',.5,.64),
    steel:material('#717b79',.82,.34), bright:material('#b0b4af',.8,.28), rubber:material('#242727',.02,.95),
    tread:material('#2b2e2c',.03,.94), engine:material('#597366',.5,.5), brass:material('#b49760',.72,.36),
    seat:material('#514138',.03,.9), red:material('#a3422f',.25,.6), black:material('#151b1c',.2,.66),
    glass:new T.MeshPhysicalMaterial({color:'#8faaa1',metalness:.15,roughness:.12,transparent:true,opacity:.48,side:T.DoubleSide,depthWrite:false}),
    lamp:new T.MeshStandardMaterial({color:'#f0e4b9',roughness:.28,metalness:.2,emissive:'#ffc677',emissiveIntensity:.08}),
  };
  const noise = new Uint8Array(64*64*4); let seed = 543;
  for(let i=0;i<noise.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const n=180+(seed%70);noise[i]=noise[i+1]=noise[i+2]=n;noise[i+3]=255;}
  const texture=new T.DataTexture(noise,64,64);texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.repeat.set(5,5);texture.needsUpdate=true;
  [m.olive,m.edge,m.rubber,m.tread].forEach(mat=>{mat.roughnessMap=texture;mat.bumpMap=texture;mat.bumpScale=.002;});
  function add(parent:T.Object3D, geometry:T.BufferGeometry, mat:T.Material, pos:V3=[0,0,0]) {
    const mesh=new T.Mesh(geometry,mat);mesh.position.set(...pos);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);return mesh;
  }
  function box(p:T.Object3D,size:V3,pos:V3,mat:T.Material=m.olive,rounded=0) {
    return add(p,geom(`b${size.join(',')},${rounded}`,()=>rounded?new RoundedBoxGeometry(...size,2,rounded):new T.BoxGeometry(...size)),mat,pos);
  }
  function cylinder(p:T.Object3D,r:number,len:number,pos:V3,mat:T.Material=m.steel,axis:'x'|'y'|'z'='y',r2=r,segments=24) {
    const mesh=add(p,geom(`c${r},${r2},${len},${segments}`,()=>new T.CylinderGeometry(r,r2,len,segments)),mat,pos);
    if(axis==='x')mesh.rotation.z=Math.PI/2; if(axis==='z')mesh.rotation.x=Math.PI/2;return mesh;
  }
  function align(mesh:T.Object3D,a:V3|T.Vector3,b:V3|T.Vector3) {
    const av=Array.isArray(a)?new T.Vector3(...a):a,bv=Array.isArray(b)?new T.Vector3(...b):b;
    mesh.position.copy(av).add(bv).multiplyScalar(.5);const delta=bv.clone().sub(av);mesh.scale.y=delta.length();mesh.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),delta.normalize());
  }
  function link(p:T.Object3D,a:V3,b:V3,r=.025,mat:T.Material=m.steel) {const mesh=cylinder(p,r,1,[0,0,0],mat);align(mesh,a,b);return mesh;}
  function tube(p:T.Object3D,pts:V3[],r:number,mat:T.Material=m.dark) {
    return add(p,new T.TubeGeometry(new T.CatmullRomCurve3(pts.map(a=>new T.Vector3(...a))),Math.max(8,pts.length*5),r,8,false),mat);
  }
  function torus(p:T.Object3D,r:number,t:number,pos:V3,mat:T.Material=m.rubber,axis:'x'|'y'|'z'='z') {
    const mesh=add(p,geom(`t${r},${t}`,()=>new T.TorusGeometry(r,t,8,48)),mat,pos);if(axis==='x')mesh.rotation.y=Math.PI/2;if(axis==='y')mesh.rotation.x=Math.PI/2;return mesh;
  }
  function panel(p:T.Object3D,pts:V3[],mat:T.Material) {
    const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(pts.flat(),3));geo.setIndex([0,1,2,0,2,3]);geo.computeVertexNormals();return add(p,geo,mat);
  }
  function part(id:string,name:string,english:string,detail:string,motion:string,fidelity:string,color:string) {
    const group=new T.Group();group.name=id;group.userData.partId=id;root.add(group);
    parts.push({id,name,english,detail,motion,fidelity,color,group});return group;
  }
  function boltRing(p:T.Object3D,count:number,r:number,pos:V3,axis:'x'|'y'|'z'='z',size=.023) {
    for(let i=0;i<count;i++){const a=i/count*Math.PI*2;const v:V3=axis==='z'?[pos[0]+Math.cos(a)*r,pos[1]+Math.sin(a)*r,pos[2]]:axis==='x'?[pos[0],pos[1]+Math.cos(a)*r,pos[2]+Math.sin(a)*r]:[pos[0]+Math.cos(a)*r,pos[1],pos[2]+Math.sin(a)*r];cylinder(p,size,.024,v,m.bright,axis,size,6);}
  }
  const frame=part('frame','车架与支承','FRAME','双纵梁、横梁及铆接支承。按总轴距配置，梁截面和连接细节为估算。','固定承载结构。','轴距有据 · 截面估算','#a6ad9f');
  for(const z of [-.66,.66]) {
    box(frame,[10.65,.32,.07],[0,1.12,z],m.dark);
    for(const y of [.945,1.295]) box(frame,[10.65,.035,.19],[0,y,z],m.dark);
    for(let x=-5;x<5.2;x+=.28)for(const y of [1.01,1.23]) cylinder(frame,.014,.018,[x,y,z+Math.sign(z)*.045],m.steel,'z',.014,6);
  }
  for(const x of [-4.85,-3.9,-2.8,-1.7,-.5,.7,1.8,3,4.3,5]) {box(frame,[.13,.26,1.4],[x,1.13,0],m.dark);for(const z of [-.61,.61])box(frame,[.22,.34,.11],[x,1.12,z],m.olive);}
  box(frame,[.2,.22,2.98],[-5.48,.94,0],m.olive,.025);
  for(const z of [-.95,.95]){torus(frame,.105,.025,[-5.61,.85,z],m.dark,'x');box(frame,[.08,.13,.2],[-5.51,.92,z],m.dark);}
  box(frame,[.18,.25,2.3],[5.32,1.1,0],m.olive);torus(frame,.115,.04,[5.48,1.08,0],m.steel,'x');
  const cab=part('cab','双驾驶室','TWIN CABINS','两侧独立玻璃钢驾驶室，每舱前后布置两座。窗框、门体、座椅和仪表为照片参考重建。','四扇门可开启；方向盘跟随双前轴转向。','布局有据 · 曲面估算','#b6c498');
  for(const s of [-1,1]) {
    const z=s*1.025,w=.86,outer=z+s*w/2,inner=z-s*w/2;
    const shell=new T.Group();cab.add(shell);exterior.push(shell);
    box(shell,[2.61,.09,w],[-4.08,1.42,z],m.olive,.035);
    box(shell,[2.43,.3,.045],[-4.10,1.62,inner],m.olive,.015);
    box(shell,[.065,1.17,w],[-2.805,2.02,z],m.olive,.02);
    box(shell,[2.16,.07,.97],[-3.87,2.635,z],m.olive,.035);
    box(shell,[.055,.74,w],[-5.32,1.86,z],m.olive,.018);
    const wind:V3[]=[[-5.335,2.13,z-w/2+.08],[-4.94,2.56,z-w/2+.08],[-4.94,2.56,z+w/2-.08],[-5.335,2.13,z+w/2-.08]];
    panel(shell,wind,m.glass);for(let i=0;i<4;i++)link(shell,wind[i],wind[(i+1)%4],.028,m.dark);
    for(const ez of [inner,outer]){link(shell,[-5.37,2.08,ez],[-4.95,2.64,ez],.048,m.olive);link(shell,[-4.95,2.61,ez],[-2.82,2.61,ez],.046,m.olive);}
    box(shell,[.16,.045,.94],[-4.94,2.67,z],m.olive,.016).rotation.z=-.08;
    link(shell,[-5.36,2.15,z-.22],[-5.16,2.35,z+.1],.012,m.black);link(shell,[-5.2,2.32,z-.03],[-5.04,2.48,z+.18],.016,m.black);
    box(shell,[.035,.08,.4],[-5.365,1.93,z],m.dark,.012);
    for(const zz of [-.25,.25]){cylinder(shell,.115,.08,[-5.38,1.69,z+zz],m.dark,'x');cylinder(shell,.089,.085,[-5.42,1.69,z+zz],m.lamp,'x');torus(shell,.108,.012,[-5.47,1.69,z+zz],m.olive,'x');}
    for(let k=0;k<4;k++)box(shell,[.022,.018,.32],[-5.36,1.86+k*.045,z],m.dark);
    cylinder(shell,.045,.04,[-5.39,2.035,z+s*.27],m.brass,'x');
    for(const [ix,start,end] of [[0,-4.91,-4.03],[1,-3.96,-3.01]]) {
      const dg=new T.Group();dg.position.set(start,1.47,outer+.025*s);cab.add(dg);doors.push({group:dg,side:s});exterior.push(dg);
      const length=end-start;box(dg,[length,.5,.052],[length/2,.27,0],m.olive,.024);
      const window:V3[]=[[.05,.52,0],[.23,.99,0],[length-.06,.99,0],[length-.06,.52,0]];if(ix===1)window[1]=[.05,.99,0];
      panel(dg,window,m.glass);for(let j=0;j<4;j++)link(dg,window[j],window[(j+1)%4],.034,m.olive);
      for(const y of [.13,.63])cylinder(dg,.032,.13,[.02,y,0],m.dark);
      box(dg,[.17,.026,.047],[length-.18,.47,s*.045],m.dark,.012);box(dg,[.04,.08,.022],[length-.18,.38,s*.05],m.steel,.006);
      box(dg,[length-.2,.31,.025],[length/2,.26,-s*.04],m.engine,.012);
      box(cab,[length-.08,.055,.21],[(start+end)/2,1.23,outer],m.dark);
      for(const xx of [start+.1,end-.1])link(cab,[xx,1.45,outer],[xx,1.23,outer],.025,m.steel);
    }
    link(shell,[-4.94,2.54,outer],[-5.03,2.43,outer+s*.24],.019,m.dark);link(shell,[-5.03,2.43,outer+s*.24],[-5.03,2.13,outer+s*.24],.019,m.dark);
    box(shell,[.045,.27,.17],[-5.04,2.31,outer+s*.24],m.dark,.022);box(shell,[.008,.23,.13],[-5.069,2.31,outer+s*.24],m.bright,.003);
    for(const x of [-4.45,-3.38]) {
      box(cab,[.46,.25,.46],[x,1.6,z],m.engine,.035);box(cab,[.51,.11,.52],[x,1.78,z],m.seat,.04);
      box(cab,[.1,.53,.51],[x+.22,2.035,z],m.seat,.035).rotation.z=.1;
      for(const zz of [-.19,.19])link(cab,[x,1.78,z+zz],[x+.24,2.28,z+zz],.017,m.steel);
    }
    box(cab,[.25,.26,.73],[-4.93,1.98,z],m.engine,.025).rotation.z=-.15;
    for(let i=0;i<7;i++){const dz=z-.27+(i%4)*.17,dy=2.04-Math.floor(i/4)*.12;cylinder(cab,i<2?.054:.036,.025,[-4.775,dy,dz],m.black,'x');torus(cab,i<2?.054:.036,.006,[-4.755,dy,dz],m.bright,'x');link(cab,[-4.738,dy,dz],[-4.738,dy+.025,dz+.015],.003,m.brass);}
    if(s===-1) {
      link(cab,[-4.65,1.47,z],[-4.65,2.11,z],.025,m.dark);
      const sw=new T.Group();sw.position.set(-4.62,2.13,z);sw.rotation.z=.3;cab.add(sw);steeringWheels.push(sw);
      torus(sw,.185,.013,[0,0,0],m.black,'y');for(let i=0;i<3;i++){const a=i/3*Math.PI*2;link(sw,[0,0,0],[.177*Math.cos(a),0,.177*Math.sin(a)],.009,m.steel);}cylinder(sw,.035,.035,[0,0,0],m.dark);
      for(const zz of [-.16,.12]){link(cab,[-4.85,1.48,z+zz],[-4.9,1.68,z+zz],.012,m.dark);box(cab,[.08,.028,.09],[-4.9,1.68,z+zz],m.rubber);}
      link(cab,[-4.16,1.5,z+.28],[-4.27,1.94,z+.28],.012,m.steel);cylinder(cab,.032,.045,[-4.27,1.94,z+.28],m.black);
    }
    cylinder(cab,.075,.48,[-2.94,1.96,z-.23*s],m.red);torus(cab,.075,.008,[-2.94,1.91,z-.23*s],m.dark,'y');
    tube(cab,[[-2.94,2.24,z-.23*s],[-3.06,2.28,z-.23*s],[-3.06,1.85,z-.23*s]],.013,m.rubber);
    if(s===-1){cylinder(shell,.03,.13,[-3.2,2.75,z],m.steel);cylinder(shell,.135,.17,[-3.2,2.855,z],m.dark,'x');cylinder(shell,.11,.013,[-3.295,2.855,z],m.lamp,'x');}
  }
  const body=part('body','外壳与附件','BODY & FITTINGS','动力舱罩、挡泥板、检修盖与后部工具箱。裸底盘，无任务上装。','透视及拆解可移开外壳检查内部。','照片参考 · 细节估算','#8f9c76');
  exterior.push(body);box(body,[1.84,.06,2.37],[-1.81,2.22,0],m.olive,.025);
  for(const s of [-1,1]){
    box(body,[1.84,.81,.065],[-1.81,1.8,s*1.19],m.olive,.015);
    for(let i=0;i<17;i++){box(body,[.024,.48,.018],[-2.6+i*.098,1.87,s*1.228],m.dark);box(body,[.022,.45,.034],[-2.58+i*.098,1.87,s*1.24],m.edge);}
    for(const x of SPECS.axles){
      box(body,[1.82,.065,.72],[x,1.685,s*1.2],m.olive,.025);box(body,[.055,.46,.66],[x+.89,1.43,s*1.2],m.rubber);
      for(const dx of [-.7,.7])link(body,[x+dx,1.26,s*.67],[x+dx,1.67,s*1.14],.027,m.dark);
    }
    box(body,[1.75,.28,.43],[.05,1.35,s*1.05],m.olive,.025);
    for(const xx of [-.63,.67])box(body,[.04,.055,.06],[xx,1.39,s*1.284],m.steel);
    box(body,[.77,.3,.83],[4.89,1.4,s*.91],m.olive,.025);for(const x of [4.63,5.12])cylinder(body,.019,.025,[x,1.4,s*1.338],m.steel,'z',.019,6);
    cylinder(body,.065,.04,[5.38,1.15,s*.94],m.red,'x');
  }
  for(const z of [-.7,.7]){box(body,[1.3,.025,.49],[-1.85,2.267,z],m.edge,.012);for(const x of [-2.34,-1.36])link(body,[x,2.29,z-.07],[x,2.29,z+.07],.016,m.dark);}
  const engine=part('engine','D12A · V12 柴油机','POWER UNIT','60° V12 结构参考。12 活塞、连杆、曲轴、气门、凸轮轴与进排气管；内部尺寸和相位为演示用重建。','曲柄连杆几何驱动活塞；慢动作便于观察。','缸数及布局有据 · 内部机构示意','#eab07d');
  engine.position.set(-2.05,1.32,0);
  shells.push(box(engine,[1.65,.26,.61],[0,-.03,0],m.engine,.075),box(engine,[1.7,.35,.72],[0,.24,0],m.engine,.05));
  for(const x of [-.88,.88]){cylinder(engine,.25,.07,[x,.21,0],m.engine,'x');boltRing(engine,12,.214,[x+(x>0?.04:-.04),.21,0],'x');}
  const crank=new T.Group();crank.position.y=.2;engine.add(crank);rotors.push({object:crank,axis:'x',rate:1});cylinder(crank,.038,1.83,[0,0,0],m.bright,'x');
  for(let i=0;i<6;i++) {
    const x=-.66+i*.264,phase=(i%3)*Math.PI*2/3;
    for(const dx of [-.064,.064]){const c=cylinder(crank,.093,.027,[x+dx,0,0],m.steel,'x');c.scale.y=1.4;}
    cylinder(crank,.034,.1,[x,.09*Math.cos(phase),.09*Math.sin(phase)],m.bright,'x');
    for(const bank of [-1,1]){
      const tilt=bank*Math.PI/6,axis=new T.Vector3(0,Math.cos(tilt),Math.sin(tilt)),base=new T.Vector3(x,.2,0);
      const liner=cylinder(engine,.086,.26,[x,.2+axis.y*.36,axis.z*.36],m.steel);liner.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),axis);shells.push(liner);
      const pg=new T.Group();engine.add(pg);pg.quaternion.copy(liner.quaternion);cylinder(pg,.074,.082,[0,0,0],m.bright);
      for(const y of [-.018,0,.018])torus(pg,.074,.0025,[0,y,0],m.dark,'y');
      const rod=cylinder(engine,.016,1,[0,0,0],m.brass);pistons.push({piston:pg,rod,bank,phase,x});
      const head=box(engine,[.237,.13,.23],[x,.2+axis.y*.57,axis.z*.57],m.engine,.022);head.quaternion.copy(liner.quaternion);shells.push(head);
      for(const exhaust of [false,true]){
        const origin=base.clone().addScaledVector(axis,.52);origin.x+=exhaust?.045:-.045;
        const v=cylinder(engine,.009,.12,[origin.x,origin.y,origin.z],m.bright);v.quaternion.copy(liner.quaternion);valves.push({mesh:v,origin,axis,phase,exhaust});cylinder(v,.027,.01,[0,-.06,0],m.steel);
      }
      tube(engine,[[x,.67,bank*.34],[x,.67,bank*.49],[x+.06,.57,bank*.57]],.03,m.dark);
      tube(engine,[[x,.75,bank*.23],[x,.84,bank*.15],[x,.79,bank*.04]],.023,m.engine);
    }
  }
  for(const s of [-1,1]){
    const cover=box(engine,[1.73,.115,.24],[0,.81,s*.36],m.engine,.03);cover.rotation.x=s*Math.PI/6;shells.push(cover);
    for(let i=0;i<10;i++)cylinder(engine,.013,.025,[-.77+i*.17,.871,s*.36],m.steel);
    cylinder(engine,.044,1.72,[0,.61,s*.57],m.dark,'x');
    const cam=new T.Group();cam.position.set(0,.72,s*.29);engine.add(cam);cylinder(cam,.018,1.7,[0,0,0],m.bright,'x');rotors.push({object:cam,axis:'x',rate:.5});
    for(let i=0;i<12;i++){const l=cylinder(cam,.027,.021,[-.78+i*.14,.01,0],m.steel,'x');l.scale.y=.7;}
    tube(engine,[[.7,.6,s*.57],[.92,.45,s*.58],[1.1,.25,s*.62],[1.12,.2,s*.89],[1.35,.2,s*.89]],.048,m.dark);
  }
  cylinder(engine,.135,.36,[-.2,.39,-.57],m.black,'x');cylinder(engine,.095,.27,[.32,.4,-.55],m.steel,'x');
  for(let i=0;i<6;i++)tube(engine,[[-.4+i*.13,.45,-.48],[-.4+i*.13,.87,-.18],[-.66+i*.264,.83,-.27]],.006,m.brass);
  cylinder(engine,.12,.3,[.65,.45,.51],m.engine);cylinder(engine,.07,.24,[.49,.19,.5],m.steel);
  const cooling=part('cooling','冷却与辅助系统','COOLING & AUXILIARIES','散热器、风扇、空气滤清器、蓄电池与辅助管路。','风扇跟随发动机转动；热交换与电气网络未求解。','位置和管路为示意','#84afb0');
  box(cooling,[.13,.91,1.03],[-.98,1.77,0],m.dark,.03);for(let i=0;i<30;i++)box(cooling,[.025,.81,.014],[-.897,1.78,-.47+i*.032],m.steel);
  const fan=new T.Group();fan.position.set(-1.13,1.77,0);cooling.add(fan);fans.push(fan);cylinder(fan,.09,.08,[0,0,0],m.dark,'x');
  for(let i=0;i<8;i++){const a=i*Math.PI/4;const blade=box(fan,[.025,.27,.12],[0,Math.cos(a)*.23,Math.sin(a)*.23],m.dark,.012);blade.rotation.x=a;blade.rotation.y=.22;}
  torus(cooling,.395,.024,[-1.13,1.77,0],m.dark,'x');
  for(const s of [-1,1]){tube(cooling,[[-1.02,2.12,s*.35],[-1.45,2.05,s*.46],[-1.7,1.95,s*.34]],.035,m.rubber);cylinder(cooling,.19,.4,[-2.91,2.03,s*.2],m.dark);torus(cooling,.19,.015,[-2.91,2.17,s*.2],m.steel,'y');box(cooling,[.53,.31,.35],[-.24,1.17,s*.91],m.black,.014);for(const x of [-.41,-.08])cylinder(cooling,.025,.025,[x,1.34,s*.91],m.brass);}
  const drive=part('drive','变速与分动机构','TRANSMISSION','液力变矩器、三速行星变速箱、两速分动箱及前后传动轴。齿轮以通用机构表示。','挡位决定车轮目标转速；空挡断开驱动。未求解液力流场与齿面接触。','拓扑有据 · 齿比与齿形示意','#cb9d61');
  shells.push(cylinder(drive,.3,.3,[-.97,1.12,0],m.engine,'x'),box(drive,[.9,.46,.52],[-.36,1.05,0],m.engine,.07),box(drive,[.49,.53,.69],[.46,1.03,0],m.engine,.045));
  function gear(p:T.Object3D,r:number,thick:number,pos:V3,axis:'x'|'z',count=24) {
    const g=new T.Group();g.position.set(...pos);p.add(g);cylinder(g,r,thick,[0,0,0],m.brass,axis);
    for(let i=0;i<count;i++){const a=i/count*Math.PI*2;const b=box(g,axis==='x'?[thick,.027,.027]:[.027,.027,thick],axis==='x'?[0,Math.cos(a)*r,Math.sin(a)*r]:[Math.cos(a)*r,Math.sin(a)*r,0],m.brass);if(axis==='x')b.rotation.x=a;else b.rotation.z=a;}
    return g;
  }
  const turbine=gear(drive,.25,.06,[-.99,1.12,0],'x',28);rotors.push({object:turbine,axis:'x',rate:1});
  for(const x of [-.66,-.33,0]){const g=new T.Group();g.position.set(x,1.05,0);drive.add(g);torus(g,.22,.02,[0,0,0],m.steel,'x');const sun=gear(g,.075,.07,[0,0,0],'x');rotors.push({object:sun,axis:'x',rate:1});for(let i=0;i<3;i++){const a=i*Math.PI*2/3;const small=gear(g,.065,.07,[.015,Math.cos(a)*.14,Math.sin(a)*.14],'x',12);rotors.push({object:small,axis:'x',rate:-.8});}rotors.push({object:g,axis:'x',rate:.4});}
  for(const y of [.85,1.15]){const g=gear(drive,.14,.05,[.46,y,0],'x',20);rotors.push({object:g,axis:'x',rate:y===.85?.3:-.3});}
  for(const [a,b] of [[SPECS.axles[0],SPECS.axles[1]],[SPECS.axles[1],.4],[.7,SPECS.axles[2]],[SPECS.axles[2],SPECS.axles[3]]]){
    cylinder(drive,.048,b-a,[a+(b-a)/2,.87,0],m.steel,'x');
    for(const x of [a+.06,b-.06]){const joint=new T.Group();joint.position.set(x,.87,0);drive.add(joint);cylinder(joint,.086,.08,[0,0,0],m.dark,'x');box(joint,[.13,.09,.05],[0,0,0],m.steel);rotors.push({object:joint,axis:'x',rate:0});}
  }
  for(const x of SPECS.axles){const housing=add(drive,new T.SphereGeometry(.23,24,16),m.engine,[x,.84,0]);housing.scale.set(1.1,1,1.35);shells.push(housing);const diff=gear(drive,.19,.05,[x,.84,0],'z');rotors.push({object:diff,axis:'z',rate:0});}
  const suspension=part('suspension','独立扭杆悬架','TORSION SUSPENSION','八轮独立悬架，纵向扭杆、上下叉形摆臂及液压减振器。','路面输入驱动轮端升降，摆臂、半轴和减振器端点同步更新。','机构类型有据 · 几何与刚度未标定','#98b6c7');
  const rolling=part('wheels','轮胎与轮边减速','WHEELS & HUBS','8 个越野胎纹轮胎、轮辋、轮毂和行星轮边传动。','前两轴按共同转向中心计算转角；车轮随车速滚动。','轮数与轮距有据 · 胎纹估算','#c5c6bd');
  const brakes=part('brakes','制动与气路','BRAKES & AIR','八轮鼓式制动、气罐、管路与轮端制动蹄。','制动输入使制动蹄张开并减速；气压和液压回路未求解。','系统类型有据 · 管路示意','#c18471');
  for(const s of [-1,1]){cylinder(brakes,.12,1.15,[.1,.85,s*.9],m.dark,'x');for(const xx of [-.3,.5])torus(brakes,.125,.014,[xx,.85,s*.9],m.steel,'x');tube(brakes,[[-4.6,1.24,s*.5],[-.2,1.24,s*.5],[3.9,1.24,s*.5]],.012,m.brass);}
  for(const [i,x] of SPECS.axles.entries())for(const s of [-1,1]){
    const index=wheels.length,z=s*SPECS.track/2;
    const carrier=new T.Group();carrier.position.set(x,.8,z);rolling.add(carrier);const spin=new T.Group();carrier.add(spin);
    const profile=[[.49,-.215],[.56,-.286],[.66,-.3],[.755,-.24],[.785,-.17],[.785,.17],[.755,.24],[.66,.3],[.56,.286],[.49,.215]].map(a=>new T.Vector2(a[0],a[1]));
    const tire=add(spin,geom('tire',()=>new T.LatheGeometry(profile,64)),m.rubber);tire.rotation.x=Math.PI/2;
    const treadGeo=geom('tread',()=>new RoundedBoxGeometry(.135,.065,.29,1,.012));
    const tread=new T.InstancedMesh(treadGeo,m.tread,96);tread.castShadow=true;tread.receiveShadow=true;const dummy=new T.Object3D();
    for(let j=0;j<48;j++)for(let k=0;k<2;k++){const a=j/48*Math.PI*2+(k?.024:0);dummy.position.set(Math.sin(a)*.777,Math.cos(a)*.777,(k?1:-1)*.132);dummy.rotation.set(0,0,-a);dummy.rotateY((k?1:-1)*.54);dummy.updateMatrix();tread.setMatrixAt(j*2+k,dummy.matrix);}spin.add(tread);
    for(const side of [-1,1]){torus(spin,.512,.021,[0,0,side*.225],m.rubber);torus(spin,.676,.006,[0,0,side*.279],m.tread);torus(spin,.712,.004,[0,0,side*.268],m.tread);}
    cylinder(spin,.497,.43,[0,0,0],m.olive,'z');torus(spin,.48,.026,[0,0,s*.24],m.edge);cylinder(spin,.376,.06,[0,0,s*.244],m.edge,'z');cylinder(spin,.235,.16,[0,0,s*.286],m.olive,'z');
    boltRing(spin,12,.31,[0,0,s*.281],'z',.026);boltRing(spin,16,.445,[0,0,s*.245],'z',.014);
    for(let j=0;j<8;j++){const a=j*Math.PI/4;cylinder(spin,.046,.01,[Math.cos(a)*.388,Math.sin(a)*.388,s*.269],m.dark,'z');}
    shells.push(cylinder(spin,.175,.025,[0,0,s*.38],m.olive,'z'));boltRing(spin,8,.144,[0,0,s*.4],'z',.012);
    const hub=new T.Group();carrier.add(hub);hub.position.z=s*.18;const sun=gear(hub,.065,.032,[0,0,s*.035],'z',14);rotors.push({object:sun,axis:'z',rate:0});
    for(let j=0;j<3;j++){const a=j*Math.PI*2/3;const g=gear(hub,.046,.03,[Math.cos(a)*.11,Math.sin(a)*.11,s*.035],'z',12);rotors.push({object:g,axis:'z',rate:0});}
    const brake=new T.Group();brake.position.set(x,.8,z-s*.29);brakes.add(brake);shells.push(cylinder(brake,.335,.13,[0,0,0],m.dark,'z'));
    for(const k of [-1,1]){const shoe=add(brake,new T.TorusGeometry(.287,.023,6,20,Math.PI*.74),m.red);shoe.rotation.z=k===1?-.37*Math.PI:.63*Math.PI;shoe.userData.shoe=k;}
    cylinder(brake,.044,.2,[0,.2,0],m.steel,'x');wheels.push({carrier,spin,x,side:s,hub,brake});
    for(const y of [.62,1.02])for(const dx of [-.24,.24]){const start:V3=[x+dx,y,s*.56],end:V3=[0,y-.8,-s*.14];const mesh=link(suspension,start,[x,y,z-s*.14],.036,m.dark);links.push({mesh,start,wheel:index,end});}
    const a:V3=[x-.26,1.33,s*.69],b:V3=[x,.64,z-s*.12];const damper=link(suspension,a,b,.057,m.olive);links.push({mesh:damper,start:a,wheel:index,end:[0,-.16,-s*.12]});
    const a2:V3=[x,.84,s*.18];const axle=link(suspension,a2,[x,.8,z],.038,m.steel);links.push({mesh:axle,start:a2,wheel:index,end:[0,0,0]});
    cylinder(suspension,.035,1.75,[x+(i%2===0?.72:-.72),.69,s*.53],m.brass,'x');
    if(i<2){const start:V3=[x-.3,.91,s*.55],end:V3=[-.16,.07,-s*.14];const steering=link(suspension,start,[x-.16,.87,z-s*.14],.022,m.brass);links.push({mesh:steering,start,wheel:index,end});}
    tube(brakes,[[x,1.24,s*.5],[x+.24,1.02,s*.72],[x+.13,.87,s*.91]],.014,m.dark);
  }
  const fuel=part('fuel','燃油系统','FUEL SYSTEM','侧置燃油箱、固定带、加注口与供油管。未重建油泵的全部内部零件。','固定组件，管路呈现系统布局。','布置参考 · 油箱外形估算','#92a17a');
  for(const s of [-1,1]){box(fuel,[1.67,.44,.54],[.06,.98,s*1.02],m.olive,.11);for(const x of [-.51,.6])box(fuel,[.045,.46,.56],[x,.98,s*1.02],m.dark,.02);cylinder(fuel,.065,.06,[.48,1.23,s*1.02],m.steel);tube(fuel,[[.48,1.2,s*1.02],[-.7,1.2,s*.72],[-2.0,1.69,s*.48]],.013,m.brass);}
  // Merge fixed sibling details while preserving the pivots of all moving parts.
  // Shells remain separate so x-ray rendering does not hide internal mechanisms.
  const moving=new Set<T.Object3D>([...rotors.map(r=>r.object),...valves.map(v=>v.mesh),...links.map(l=>l.mesh),...pistons.map(p=>p.rod)]);
  const shellObjects=new Set<T.Object3D>(shells);
  const holders:T.Object3D[]=[];root.traverse(o=>{if(o instanceof T.Group)holders.push(o);});
  for(const holder of holders){
    const batches=new Map<string,T.Mesh[]>();
    for(const o of holder.children){if(!(o instanceof T.Mesh)||o instanceof T.InstancedMesh||o.children.length||moving.has(o)||shellObjects.has(o)||o.userData.shoe||Array.isArray(o.material))continue;
      const key=o.material.uuid+!!o.geometry.index+Object.keys(o.geometry.attributes).sort().join(',');if(!batches.has(key))batches.set(key,[]);batches.get(key)!.push(o);
    }
    for(const meshes of batches.values()){if(meshes.length<3)continue;const copies=meshes.map(o=>{o.updateMatrix();return o.geometry.clone().applyMatrix4(o.matrix);});const merged=mergeGeometries(copies,false);copies.forEach(g=>g.dispose());if(!merged)continue;
      const mesh=add(holder,merged,meshes[0].material as T.Material);mesh.userData.fixedDetailCount=meshes.length;meshes.forEach(o=>holder.remove(o));
    }
  }
  root.updateMatrixWorld(true);
  const originalMaterials=new Map<string,T.Material>();
  for(const [key,mat] of Object.entries(m))mat.name=key;
  for(const p of parts){p.group.userData.base=p.group.position.toArray();let n=0,g=0;p.group.traverse(o=>{if(o instanceof T.Mesh){o.name=`${p.id}_${String(++n).padStart(4,'0')}`;originalMaterials.set(o.name,o.material as T.Material);}else if(o!==p.group&&!o.name){o.name=`${p.id}_pivot_${String(++g).padStart(3,'0')}`;}});}
  const exteriorMeshes=new Set<T.Mesh>();for(const o of exterior)o.traverse(x=>{if(x instanceof T.Mesh)exteriorMeshes.add(x);});
  const shellsSet=new Set(shells),xrayM=new T.MeshStandardMaterial({color:'#8eb7b8',transparent:true,opacity:.06,depthWrite:false,metalness:.1,roughness:.5,side:T.DoubleSide});
  const cutPlane=new T.Plane(new T.Vector3(0,0,-1),0),variants=new Map<T.Material,T.Material>();let lastStyle='';
  let previousWheel=0;const wheelPhases=Array(8).fill(0);
  function update(c:Controls,t:Telemetry) {
    const angles=steeringAngles(c.steering),amount=c.explode/100;
    wheels.forEach((w,i)=>{
      const travel=c.terrain/100*.18*Math.sin(t.time*1.7+w.x*.95+(w.side>0?1.4:0));
      const armHorizontal=SPECS.track/2-.70;
      const lateral=.70+Math.sqrt(Math.max(0,armHorizontal*armHorizontal-travel*travel));
      w.carrier.position.set(w.x,.8+travel,w.side*(lateral+amount*1.5));w.carrier.rotation.y=i<4?-angles[i]:0;
      const pivot=(SPECS.axles[2]+SPECS.axles[3])/2,turnRadius=Math.abs(c.steering)>.001?(pivot-SPECS.axles[0])/Math.tan(c.steering*Math.PI/180):Infinity;
      const pathRatio=Number.isFinite(turnRadius)?(i<4?Math.hypot(pivot-w.x,turnRadius-w.side*SPECS.track/2):Math.abs(turnRadius-w.side*SPECS.track/2))/Math.abs(turnRadius):1;
      if(t.time===0)wheelPhases[i]=0;else wheelPhases[i]+=(t.wheel-previousWheel)*pathRatio;
      w.spin.rotation.z=wheelPhases[i];
      w.brake.position.y=.8+travel;w.brake.rotation.y=w.carrier.rotation.y;w.brake.children.forEach(o=>{if(o.userData.shoe)o.position.x=o.userData.shoe*c.brake*.00016;});w.hub.rotation.z=t.wheel;
    });
    previousWheel=t.wheel;
    for(const l of links){const w=wheels[l.wheel];const end=new T.Vector3(...l.end).applyAxisAngle(new T.Vector3(0,1,0),w.carrier.rotation.y).add(w.carrier.position);align(l.mesh,l.start,end);}
    for(const r of rotors)r.object.rotation[r.axis]=r.rate===0?t.wheel*4:t.crank*r.rate;
    for(const f of fans)f.rotation.x=t.crank*1.4;
    for(const p of pistons){const tilt=p.bank*Math.PI/6,theta=t.crank+p.phase;const axis=new T.Vector3(0,Math.cos(tilt),Math.sin(tilt)),base=new T.Vector3(p.x,.2,0);
      p.piston.position.copy(base).addScaledVector(axis,pistonPosition(theta-tilt));const pin=base.clone().add(new T.Vector3(0,.09*Math.cos(theta),.09*Math.sin(theta)));align(p.rod,pin,p.piston.position);
    }
    for(const v of valves){const phase=((t.crank+v.phase+(v.exhaust?Math.PI:0))%(Math.PI*4)+Math.PI*4)%(Math.PI*4);const lift=phase>Math.PI&&phase<2*Math.PI?Math.sin(phase-Math.PI)*.022:0;v.mesh.position.copy(v.origin).addScaledVector(v.axis,-lift);}
    for(const d of doors)d.group.rotation.y=-d.side*c.doors/100*Math.PI*.55;
    for(const sw of steeringWheels)sw.rotation.y=-c.steering*Math.PI/180*12;m.lamp.emissiveIntensity=c.lights?2:.08;
    for(const p of parts){const base=p.group.userData.base as number[];let dy=0,dz=0;if(p.id==='cab')dy=amount*2.4;if(p.id==='body')dy=amount*3.4;if(p.id==='engine')dy=amount*1.8;if(p.id==='cooling'){dy=amount*1.7;dz=amount*1.5;}if(p.id==='fuel')dz=amount*1.5;if(p.id==='brakes')dy=amount*-.25;p.group.position.set(base[0],base[1]+dy,base[2]+dz);p.group.visible=!c.focus||c.focus===p.id;}
    const style=`${c.mode}-${c.wireframe}`;
    if(style!==lastStyle){lastStyle=style;root.traverse(o=>{if(!(o instanceof T.Mesh)||!originalMaterials.has(o.name))return;const orig=originalMaterials.get(o.name)!;let mat=orig;
      if(c.mode==='xray'&&(exteriorMeshes.has(o)||shellsSet.has(o)))mat=xrayM;
      if(c.mode==='section'){if(!variants.has(orig)){const v=orig.clone();v.clippingPlanes=[cutPlane];v.clipShadows=true;v.side=T.DoubleSide;variants.set(orig,v);}mat=variants.get(orig)!;}
      o.material=mat;if('wireframe' in mat)(mat as T.MeshStandardMaterial).wireframe=c.wireframe;
    });}
    root.updateMatrixWorld(true);
  }
  function dispose(){const mats=new Set<T.Material>(originalMaterials.values()),geos=new Set<T.BufferGeometry>(geometries.values());root.traverse(o=>{if(o instanceof T.Mesh){geos.add(o.geometry);if(Array.isArray(o.material))o.material.forEach(mat=>mats.add(mat));else mats.add(o.material);}});geos.forEach(g=>g.dispose());mats.forEach(mat=>mat.dispose());variants.forEach(mat=>mat.dispose());texture.dispose();}
  const ghostNames=new Set([...exteriorMeshes,...shellsSet].map(o=>o.name));
  return {root,parts,update,dispose,wheels,pistons,doors,originalMaterials,ghostNames};
}

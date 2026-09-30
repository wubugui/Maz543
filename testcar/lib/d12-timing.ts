// MAZ-543 1973 fig.7 tooth counts. All shaft coordinates and modules are fits.
// Ideal rigid gear constraints; backlash, elastic torsion and loads remain open.
export type V3=[number,number,number];
export type TimingShaft={node:string;origin:V3;axis:V3;existing:boolean;rate:number};
export type TimingGear={shaft:string;teeth:number;kind:'bevel'|'spur';profile:string;member:'A'|'B';origin:V3;axis:V3;phase:number;module:number;bore:number};
export const dot=(a:V3,b:V3)=>a.reduce((s,v,i)=>s+v*b[i],0);
const sub=(a:V3,b:V3):V3=>a.map((v,i)=>v-b[i]) as V3;
const scale=(a:V3,s:number):V3=>a.map(v=>v*s) as V3;
const add=(a:V3,b:V3):V3=>a.map((v,i)=>v+b[i]) as V3;
const norm=(a:V3):V3=>scale(a,1/Math.hypot(...a));
export const cross=(a:V3,b:V3):V3=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export function timingBasis(axis:V3):[V3,V3,V3]{
  const x=norm(axis),ref:V3=Math.abs(x[0])>.9?[0,1,0]:[1,0,0];
  const y=norm(sub(ref,scale(x,dot(ref,x))));return [x,y,cross(x,y)];
}
const phi=(axis:V3,toward:V3)=>{const [,y,z]=timingBasis(axis);return Math.atan2(dot(toward,z),dot(toward,y));};

export function createTimingLayout(camY:number,offset:number,beta:number,crankY:number){
  const x=-.665,c=Math.cos(beta),s=Math.sin(beta),X:V3=[1,0,0],Y:V3=[0,1,0],down:V3=[0,-1,0];
  const crank:V3=[x,crankY,0],upperCam:V3=[x,crankY+offset/s,0],injection:V3=[x,.59,0];
  const gen:V3=[x,.166,-.343],genAxis=norm(sub(gen,crank));
  const low:V3=[x,-.085,0],oilIdler=add(low,[.0531,0,.0708]);
  const oilOutput=add(oilIdler,[.084*Math.cos(.35),0,.084*Math.sin(.35)]);
  const fuelSpur=add(low,[0,0,-.069]),fuelApex:V3=[x,-.155,-.069];
  const shafts:Record<string,TimingShaft>={};
  const shaft=(id:string,node:string,origin:V3,axis:V3,existing=false)=>{shafts[id]={node,origin,axis: norm(axis),existing,rate:NaN};};
  shaft('crank','D12_crankshaft',[0,crankY,0],X,true);shafts.crank.rate=1;
  shaft('upper','D12_timing_upper',crank,Y);
  shaft('lower','D12_timing_lower',crank,down);
  shaft('generator_takeoff','D12_timing_generator_takeoff',crank,genAxis);
  shaft('generator','D12_timing_generator',gen,X);
  shaft('injection','D12_injection_cam',[0,.59,0],X,true);
  shaft('oil_idler','D12_timing_oil_idler',oilIdler,down);
  shaft('oil_pump','D12_timing_oil_pump',oilOutput,down);
  shaft('fuel_takeoff','D12_timing_fuel_takeoff',fuelSpur,down);
  shaft('fuel_feed','D12_timing_fuel_feed',fuelApex,X);
  for(const [bank,sign] of [['L',-1],['R',1]] as const){
    const z=-sign*offset;
    shaft('inclined_'+bank,'D12_timing_inclined_'+bank,upperCam,[0,c,sign*s]);
    shaft('intake_'+bank,'D12_cam_'+bank+'_intake',[0,crankY+camY*c-z*sign*s,camY*sign*s+z*c],X,true);
    shaft('exhaust_'+bank,'D12_cam_'+bank+'_exhaust',[0,crankY+camY*c+z*sign*s,camY*sign*s-z*c],X,true);
  }
  const gears:Record<string,TimingGear>={};const edges:{a:string;b:string;ratio:number}[]=[];
  const bevel=(id:string,sh:string,teeth:number,profile:string,member:'A'|'B',origin:V3,axis:V3,module:number,bore:number)=>{gears[id]={shaft:sh,teeth,kind:'bevel',profile,member,origin,axis,phase:NaN,module,bore};};
  const spur=(id:string,sh:string,teeth:number,origin:V3,module:number,bore:number)=>{gears[id]={shaft:sh,teeth,kind:'spur',profile:'accessory',member:'A',origin,axis:shafts[sh].axis,phase:NaN,module,bore};};
  const drive=(a:string,b:string)=>{
    const A=gears[a],B=gears[b],sa=shafts[A.shaft],sb=shafts[B.shaft];
    const ratio=-dot(A.axis,sa.axis)/dot(B.axis,sb.axis)*A.teeth/B.teeth;
    if(!Number.isFinite(A.phase))A.phase=0;
    const pa=phi(A.axis,A.kind==='bevel'?B.axis:sub(B.origin,A.origin));
    const pb=phi(B.axis,B.kind==='bevel'?A.axis:sub(A.origin,B.origin));
    B.phase=pb+(A.teeth*(pa-A.phase)-Math.PI)/B.teeth;
    const rate=sa.rate*ratio;
    if(Number.isFinite(sb.rate)&&Math.abs(sb.rate-rate)>1e-10)throw Error('Inconsistent timing loop '+b);
    sb.rate=rate;edges.push({a,b,ratio});
  };
  bevel('crank27','crank',27,'crank','A',crank,X,.004,.031);
  for(const [id,axis] of [['upper',Y],['lower',down],['generator_takeoff',genAxis]] as [string,V3][]){
    bevel(id+'18',id,18,'crank','B',crank,axis,.004,.010);drive('crank27',id+'18');
  }
  bevel('upper12','upper',12,'cam_lower','A',upperCam,Y,.0025,.008);
  for(const bank of ['L','R']){
    const inclined=shafts['inclined_'+bank],cam=shafts['intake_'+bank],apex:V3=[x,cam.origin[1],cam.origin[2]];
    bevel('inclined18_'+bank,'inclined_'+bank,18,'cam_lower','B',upperCam,inclined.axis,.0025,.008);
    drive('upper12','inclined18_'+bank);
    bevel('inclined12_'+bank,'inclined_'+bank,12,'cam_upper','A',apex,scale(inclined.axis,-1),.003,.0075);
    bevel('cam24_'+bank,'intake_'+bank,24,'cam_upper','B',apex,X,.003,.0212);
    drive('inclined12_'+bank,'cam24_'+bank);
    spur('intake22_'+bank,'intake_'+bank,22,[-.629,cam.origin[1],cam.origin[2]],2*offset/22,.020);
    spur('exhaust22_'+bank,'exhaust_'+bank,22,[-.629,...shafts['exhaust_'+bank].origin.slice(1)] as V3,2*offset/22,.020);
    drive('intake22_'+bank,'exhaust22_'+bank);
  }
  bevel('injection12','upper',12,'injection','A',injection,down,.0026,.008);
  bevel('injection36','injection',36,'injection','B',injection,X,.0026,.012);drive('injection12','injection36');
  bevel('generator21','generator_takeoff',21,'generator','A',gen,scale(genAxis,-1),.0028,.008);
  bevel('generator18','generator',18,'generator','B',gen,X,.0028,.008);drive('generator21','generator18');
  spur('lower23','lower',23,low,.003,.010);
  spur('oil36','oil_idler',36,oilIdler,.003,.010);drive('lower23','oil36');
  spur('oil20','oil_pump',20,oilOutput,.003,.009);drive('oil36','oil20');
  spur('fuel23','fuel_takeoff',23,fuelSpur,.003,.008);drive('lower23','fuel23');
  bevel('fuel11','fuel_takeoff',11,'fuel_feed','A',fuelApex,Y,.0025,.006);
  bevel('fuel21','fuel_feed',21,'fuel_feed','B',fuelApex,X,.0025,.007);drive('fuel11','fuel21');
  return {shafts,gears,edges,crank,upperCam,injection,generator:gen,lower:low,fuelApex};
}

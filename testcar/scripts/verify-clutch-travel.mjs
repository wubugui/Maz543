import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {CLUTCH_PACKS,CLUTCH_CONTACT as C,clutchContactTravel,clutchPlateShift} from '../work/transmission/transmission.mjs';
let states=0;
// Independent axial interval construction verifies unilateral contact over the
// entire stroke, not just the final selected pose or copied shift expressions.
for(const [name,p] of Object.entries(CLUTCH_PACKS)){
  const pitch=C.plateThickness+C.plateGap,start=p.direction===1?p.start:p.start-(p.count-1)*pitch;
  for(let i=0;i<=1000;i++){
    const travel=clutchContactTravel(name)*i/1000;
    const centers=Array.from({length:p.count},(_,j)=>start+j*pitch+clutchPlateShift(name,j,travel));
    for(let j=1;j<centers.length;j++)assert.ok(centers[j]-centers[j-1]>=C.plateThickness-1e-12);
    const piston=p.start-p.direction*.005+p.direction*travel;
    const gap=p.direction===1?centers[0]-C.plateThickness/2-(piston+.002):piston-.002-(centers.at(-1)+C.plateThickness/2);
    assert.ok(gap>=-1e-12);
    assert.ok(Math.abs((p.direction===1?centers.at(-1):centers[0])-(p.direction===1?start+(p.count-1)*pitch:start))<1e-12);
    if(i===1000){assert.ok(Math.abs(gap)<1e-12);for(let j=1;j<centers.length;j++)assert.ok(Math.abs(centers[j]-centers[j-1]-C.plateThickness)<1e-12);}
    states++;
  }
}
const result={states,errors:0,limits:'Unilateral axial geometry only; no force or hydraulic response.'};
await fs.writeFile('outputs/clutch-travel-verification.json',JSON.stringify(result,null,2));console.log(result);

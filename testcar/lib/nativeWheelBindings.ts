import type {Object3D} from 'three';

/** Stable identities from the retained eight-station authoring hierarchy.
 * These describe the legacy assets, not the unexported native-joint candidate.
 */
export const LEGACY_WHEEL_STATIONS=Object.freeze(([
  [0,'wheels_pivot_001','wheels_pivot_002','brakes_pivot_001'],
  [1,'wheels_pivot_008','wheels_pivot_009','brakes_pivot_002'],
  [2,'wheels_pivot_015','wheels_pivot_016','brakes_pivot_003'],
  [3,'wheels_pivot_022','wheels_pivot_023','brakes_pivot_004'],
  [4,'wheels_pivot_029','wheels_pivot_030','brakes_pivot_005'],
  [5,'wheels_pivot_036','wheels_pivot_037','brakes_pivot_006'],
  [6,'wheels_pivot_043','wheels_pivot_044','brakes_pivot_007'],
  [7,'wheels_pivot_050','wheels_pivot_051','brakes_pivot_008'],
] as const).map(([station,carrier,spin,brake])=>Object.freeze({station,carrier,spin,brake})));

type SourceWheel={carrier:Object3D;spin:Object3D;brake:Object3D;side:number};
export type LegacyWheelBinding=Readonly<{
  station:number;carrier:Object3D;spin:Object3D;brake:Object3D;source:Object3D;
}>;

/** Validate the complete group before changing the native scene. Never compact
 * missing stations or apply legacy local poses to a different parent chain.
 */
export function bindLegacyWheelStations(root:Object3D,sources:readonly SourceWheel[]):readonly LegacyWheelBinding[]{
  const fail=(message:string):never=>{throw new Error(`Native wheel binding: ${message}`);};
  if(sources.length!==8)fail(`expected 8 source stations, got ${sources.length}`);
  const required=new Set(['wheels','brakes',...LEGACY_WHEEL_STATIONS.flatMap(s=>[s.carrier,s.spin,s.brake])]);
  const targets=new Map<string,Object3D>();
  root.traverse(object=>{
    if(!required.has(object.name))return;
    if(targets.has(object.name))fail(`duplicate target ${object.name}`);
    targets.set(object.name,object);
  });
  const target=(name:string)=>targets.get(name)??fail(`missing target ${name}`);
  const wheels=target('wheels'),brakes=target('brakes');
  const sourceByCarrier=new Map<string,SourceWheel>();
  for(const source of sources){
    if(sourceByCarrier.has(source.carrier.name))fail(`duplicate source ${source.carrier.name}`);
    sourceByCarrier.set(source.carrier.name,source);
  }
  return Object.freeze(LEGACY_WHEEL_STATIONS.map(identity=>{
    const {station}=identity,source=sourceByCarrier.get(identity.carrier)??fail(`missing source ${identity.carrier}`);
    if(source.spin.name!==identity.spin||source.brake.name!==identity.brake||source.side!==(station%2?1:-1))
      fail(`source identity mismatch at station ${station}`);
    if(source.carrier.parent?.name!=='wheels'||source.brake.parent?.name!=='brakes'||source.spin.parent!==source.carrier)
      fail(`unsupported source parent chain at station ${station}`);
    const carrier=target(identity.carrier),spin=target(identity.spin),brake=target(identity.brake);
    if(carrier.parent!==wheels||brake.parent!==brakes||spin.parent!==carrier)
      fail(`unsupported target parent chain at station ${station}`);
    return Object.freeze({station,carrier,spin,brake,source:source.carrier});
  }));
}

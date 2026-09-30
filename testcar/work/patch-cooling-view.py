from pathlib import Path
p=Path('components/vehicle-viewer.tsx');s=p.read_text(encoding='utf-8')
s=s.replace('cooling.glb?v=cooling-2','cooling.glb?v=lower-1').replace('latest.current.coolingClutch','latest.current.coolingView').replace('lastCoolingClutch=false','lastCoolingView=\'assembly\'').replace('lastCoolingClutch','lastCoolingView')
s=s.replace("id==='cooling'&&latest.current.coolingView)","id==='cooling'&&latest.current.coolingView==='clutch')")
s=s.replace("latest.current.focus==='cooling'&&latest.current.coolingView){","latest.current.focus==='cooling'&&latest.current.coolingView==='clutch'){")
s=s.replace("    function focus(id:string){", "    function focus(id:string){\n      if(id==='cooling'&&latest.current.coolingView==='lower'){const lower=coolingNodes.get('COOL_lower_drive');if(lower){frame(lower,new T.Vector3(-1,.5,.9).normalize());return;}}")
s=s.replace("          if(latest.current.mode==='xray'&&['housing','shroud'", "          if(latest.current.focus==='cooling'&&latest.current.coolingView==='lower')o.visible=o.visible&&!!o.userData.lowerDrive;\n          if(latest.current.mode==='xray'&&['housing','shroud'")
s=s.replace('下传动箱、万向轴及完整管路仍待细化。','下传动箱按实物照和目录重建；上齿轮箱、万向轴及完整管路仍待细化。')
p.write_text(s,encoding='utf-8')

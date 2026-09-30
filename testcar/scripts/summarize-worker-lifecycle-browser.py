from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'outputs/worker-lifecycle'
failed=(folder/'worker-failed-ax.txt').read_text(encoding='utf8');recovered=(folder/'worker-recovery-ax.txt').read_text(encoding='utf8');door=(folder/'recovered-door-ax.txt').read_text(encoding='utf8')
assert 'button (disabled) 导出 GLB' in failed
assert '开发检查触发的显示故障' in failed and 'button 重新加载' in failed
assert 'image MAZ-543 三维模型' not in failed
assert 'container 独立机械计算' not in failed and 'text 画面已缓存' not in failed
assert recovered.count('image MAZ-543 三维模型')==1
assert '8,868 个几何实例' in recovered and 'text 画面已缓存' in recovered
assert 'container 独立机械计算 240 Hz · 待推进 0.000 s' in recovered
assert 'button (disabled) 导出 GLB' not in recovered
assert '开发检查触发的显示故障' not in recovered
assert 'checkbox 右舱前门 关闭 99°, Value: 1' in door
assert 'text 画面已缓存' in door
report={'passed':True,'browser':'IAB, existing tab 3, localhost:3000','scenario':'Full model ready, click development fault inside actual render worker, click existing reload control, same-page component recreated, open right front door','failed':{'canvasAbsent':True,'exportDisabled':True,'staleSimulationAndRenderStatsRemoved':True,'reloadAvailable':True},'recovered':{'viewportImageCount':1,'geometryInstances':8868,'cachedIdle':True,'mechanicalHz':240,'backlogSeconds':0,'rightFrontDoorDegrees':99},'limits':'Actual UI fault injection and recovery, not a GPU driver crash, hardware memory measurement, many-cycle leak soak, or dynamic FPS benchmark. The full physical/product acceptance gates remain open.'}
(folder/'browser-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))

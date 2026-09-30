"""Archive the bounded camera-pass diagnostic stage without overwriting history."""
from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[1]
destination = root.parent / 'restoration' / 'occlusion-transmission-profile-20260909'
assert destination.resolve().is_relative_to(root.parent.resolve())
if destination.exists():
    raise SystemExit('Archive already exists; refusing to overwrite it')

guides = ['AGENT_START_HERE.md', 'NEXT_AGENT_PROMPT.md',
          'docs/CONTINUATION_20260908.md', 'docs/ACCEPTANCE.md']
for relative in guides:
    path = root / relative
    content = path.read_text(encoding='utf-8')
    doc = ('docs/' if '/' not in relative else '') + 'OCCLUSION_AND_TRANSMISSION_PROFILE_20260909.md'
    notice = ('**最新：[实际遮挡与透射绘制诊断](' + doc + ') 已核实玻璃透射预绘制与主颜色各处理 '
              '2315 次不透明绘制、约 539 万三角形，实际采样分别为 4 / 2。零样本记录不等于跨帧可隐藏；'
              '初次混合通道口径已更正。未启用遮挡剔除或缓冲复用，类型检查与构建通过，动态整车仍慢。'
              '完整 goal ACTIVE、16 项 OPEN，继续保精度优化和机械实现。**')
    if notice not in content:
        title, rest = content.split('\n', 1)
        path.write_text(title + '\n\n' + notice + '\n\n此前阶段：\n' + rest, encoding='utf-8')

files = guides + ['lib/occlusionProfile.ts', 'lib/vehicleViewport.ts',
    'scripts/verify-occlusion-profile.mjs', 'scripts/summarize-occlusion-profile.py',
    'scripts/archive-occlusion-profile-stage.py',
    'docs/OCCLUSION_AND_TRANSMISSION_PROFILE_20260909.md']
for directory in ['outputs/occlusion-profile', 'work/occlusion-profile']:
    files.extend(p.relative_to(root).as_posix() for p in (root / directory).rglob('*') if p.is_file())
assert (root / 'outputs/occlusion-profile/final-normal-ax.txt').is_file()
manifest = []
for relative in sorted(set(files)):
    source = (root / relative).resolve()
    assert source.is_relative_to(root.resolve()) and source.is_file()
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
    manifest.append({'path': relative, 'bytes': source.stat().st_size, 'sha256': digest})
report = {'files': len(manifest), 'bytes': sum(row['bytes'] for row in manifest),
          'goal': 'ACTIVE', 'wholeVehicleGates': '16 OPEN', 'manifest': manifest}
(destination / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'archive': str(destination), 'files': report['files'], 'bytes': report['bytes'],
                  'sha256Verified': True}, ensure_ascii=False))

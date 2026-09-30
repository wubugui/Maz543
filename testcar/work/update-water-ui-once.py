from pathlib import Path
p=Path('components/workshop.tsx');s=p.read_text(encoding='utf-8')
old='靠近轴封与弹簧<span>11—16</span></button>'
new=old+'''<button className="engine-pause" onClick={()=>api.current?.focus('water-impeller')}>查看叶轮底部<span>六片叶片</span></button><button className="engine-pause" onClick={()=>api.current?.focus('engine')}>查看整泵<span>装配位置</span></button>'''
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')

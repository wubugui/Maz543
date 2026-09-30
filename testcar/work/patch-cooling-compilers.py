from pathlib import Path
for name in ['verify-model.mjs','prepare-blender.mjs','bake-animation.mjs']:
    p=Path('scripts')/name;s=p.read_text(encoding='utf-8')
    s=s.replace("['starting','suspension'","['cooling','starting','suspension'").replace("['d12-timing','d12','starting'","['cooling','d12-timing','d12','starting'")
    s=s.replace('js=js.replace(','''js=js.replace("from './cooling'","from './cooling.mjs'").replace(''')
    s=s.replace('code=code.replace(','''code=code.replace("from './cooling'","from './cooling.mjs'").replace(''')
    p.write_text(s,encoding='utf-8')

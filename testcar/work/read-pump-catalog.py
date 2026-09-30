from pathlib import Path
from bs4 import BeautifulSoup
p=BeautifulSoup(Path('work/reference-docs/cooling-oil-pump-catalog.html').read_text(encoding='utf-8'),'html.parser')
for tr in p.select('tr'):
 t=tr.get_text(' ',strip=True)
 if '543-' in t or '535' in t or 'bearing' in t:print(t[:400])

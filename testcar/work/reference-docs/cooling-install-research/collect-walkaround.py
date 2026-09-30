"""Read exact PrimePortal links from archived gallery HTML, preserve source records."""
from pathlib import Path
import concurrent.futures, hashlib, html, json, re, urllib.request
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ARCHIVE = OUT.parents[3] / 'external' / 'maz543-references' / 'suspension'

def urls(text):
    return [html.unescape(x) for x in re.findall(r'(?:src|href)=[\"\']([^\"\']+)', text, re.I)]

def fetch(url):
    with urllib.request.urlopen(url, timeout=25) as response:
        return response.read()

pages = list(ARCHIVE.glob('primeportal*.html'))
texts = [p.read_text(errors='replace') for p in pages]
thumbs = sorted(set(u for t in texts for u in urls(t) if '/thumbnails/maz-543_scud_b_tel_' in u))
full = {re.search(r'_(\d+)_of_',u).group(1): u for t in texts for u in urls(t) if '/images/maz-543_scud_b_tel_' in u}
(OUT / 'thumbnails').mkdir(exist_ok=True)

def one(url):
    n = re.search(r'_(\d+)_of_',url).group(1)
    p = OUT / 'thumbnails' / f'{n}.jpg'
    record = {'number': n, 'thumbnailUrl': url, 'originalUrl': full.get(n), 'local': str(p.relative_to(OUT))}
    try:
        if not p.exists():
            data = fetch(url)
            if not data.startswith(b'\xff\xd8'):
                raise ValueError('Not JPEG')
            p.write_bytes(data)
        with Image.open(p) as im:
            im.verify()
        record['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception as exc:
        record['error'] = str(exc)
    return record

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    records = sorted(pool.map(one, thumbs), key=lambda x:x['number'])
(OUT / 'primeportal-source-index.json').write_text(json.dumps({'gallery':'http://www.primeportal.net/artillery/tim_roberts/maz-543_scud_b_tel/index.php', 'variant':'MAZ-543 SCUD-B TEL; exact 543A identity not established', 'records':records}, indent=2), encoding='utf-8')
valid = [r for r in records if 'error' not in r]
for offset in range(0, len(valid), 36):
    sheet = Image.new('RGB', (1200, 900), '#222222')
    draw = ImageDraw.Draw(sheet)
    for i,r in enumerate(valid[offset:offset+36]):
        im=Image.open(OUT/r['local']).convert('RGB'); im.thumbnail((196,125))
        x=(i%6)*200; y=(i//6)*150
        sheet.paste(im,(x+(200-im.width)//2,y))
        draw.text((x+5,y+128),r['number']+' / 192',fill='white')
    sheet.save(OUT / f'contact-{offset//36+1}.jpg',quality=94)
print(json.dumps({'requested':len(records),'downloaded':len(valid),'errors':[r for r in records if 'error' in r]}))

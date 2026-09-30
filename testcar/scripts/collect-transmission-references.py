"""Cache the observed 1973 manual links, retaining source and content hashes."""
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import hashlib, json, re
from urllib.parse import urlparse

OUT = Path(__file__).resolve().parents[1] / 'work/reference-docs/transmission'
BASE = 'https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/'
LINKS = ['009.htm', '010.htm', '011.htm', '053.htm', '000/0672.jpg', '000/3024.jpg', '000/3031.jpg']
LINKS += ['000/0708.jpg', '000/0714.jpg', '000/0721.jpg', '000/0728.jpg', '000/0735.jpg']
LINKS += ['012.htm','000/0749.jpg','000/0756.jpg','000/0771.jpg','000/0806.jpg','000/0812.jpg','000/0819.jpg','000/0826.jpg','000/0827.jpg','000/0840.jpg']
LINKS += ['000/0687.jpg']
OUT.mkdir(parents=True, exist_ok=True)
INDEX = OUT / 'source-index.json'
OLD = {row['url']: row for row in json.loads(INDEX.read_text(encoding='utf-8'))} if INDEX.exists() else {}

def fetch(relative):
    url = BASE + relative
    target = OUT / relative.replace('/', '-')
    try:
        previous = OLD.get(url, {})
        if target.exists() and previous.get('sha256') == hashlib.sha256(target.read_bytes()).hexdigest():
            return previous
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=35) as response:
            data = response.read()
            content_type = response.headers.get('Content-Type')
        # The public host sometimes asks a normal browser to set bpc and follow
        # an HTTP URL. Honor only this narrowly parsed same-host response; never
        # execute downloaded JavaScript or accept another destination host.
        if len(data) < 1024:
            challenge = data.decode('utf-8', errors='replace')
            cookie = re.search(r'document.cookie="(bpc=[a-f0-9]+);', challenge)
            redirect = re.search(r'document.location.href="([^"]+)"', challenge)
            if cookie and redirect and urlparse(redirect[1]).hostname == 'sinref.ru':
                request = Request(redirect[1], headers={'User-Agent':'Mozilla/5.0', 'Cookie':cookie[1]})
                with urlopen(request, timeout=35) as response:
                    data = response.read()
                    content_type = response.headers.get('Content-Type')
        if target.suffix == '.jpg':
            from io import BytesIO
            with Image.open(BytesIO(data)) as image:
                image.verify()
            with Image.open(BytesIO(data)) as image:
                size = list(image.size)
        else:
            if len(data) < 1024:
                raise ValueError('Short response is a cookie/redirect page, not manual content')
            size = None
        target.write_bytes(data)
        return dict(url=url, file=str(target), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), contentType=content_type, size=size)
    except Exception as error:
        return dict(url=url, error=str(error))

with ThreadPoolExecutor(max_workers=3) as pool:
    result = list(pool.map(fetch, LINKS))
(OUT / 'source-index.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))

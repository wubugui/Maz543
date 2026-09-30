"""Lossless compatibility copies of previously downloaded catalog GIF sheets."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1] / 'work/reference-docs'
for name in ['543-lower-exploded', '543-upper-exploded', '543-oil-pump-exploded',
             '543-fan-install', '543-cardan-exploded']:
    with Image.open(root / (name + '.gif')) as source:
        source.convert('RGBA').save(root / (name + '.png'))
print('Prepared 5 unchanged catalog image copies for Blender')

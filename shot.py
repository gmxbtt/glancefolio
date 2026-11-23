#!/usr/bin/env python3
"""Fetch a simulator screenshot and composite it onto black.

The glasses screenshot API returns RGBA where ALPHA carries brightness
(Day 1 finding); a raw view looks washed out. Composite onto black first.
Usage: shot.py <url> <out.png>  (url = .../api/screenshot/glasses or webview)
"""
import sys
import urllib.request
from PIL import Image

url, out = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(url, timeout=30) as resp:
    data = resp.read()
with open('/tmp/shot-raw.png', 'wb') as f:
    f.write(data)
img = Image.open('/tmp/shot-raw.png')
if img.mode == 'RGBA':
    bg = Image.new('RGBA', img.size, (0, 0, 0, 255))
    img = Image.alpha_composite(bg, img).convert('RGB')
else:
    img = img.convert('RGB')
img.save(out)
print(f'{out}: {img.size[0]}x{img.size[1]}')

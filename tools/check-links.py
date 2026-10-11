#!/usr/bin/env python3
"""Check that every relative link, image, script and stylesheet in the site exists.

    python3 -I tools/check-links.py        (run from the repository root)
"""
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATTR = re.compile(r'''(?:href|src|data-src|poster)\s*=\s*["']([^"']+)["']|srcset\s*=\s*["']([^"']+)["']''')
bad, checked = {}, 0
for page in ROOT.rglob('*.html'):
    if '.git' in page.parts:
        continue
    text = page.read_text(encoding='utf-8')
    for m in ATTR.finditer(text):
        urls = [m.group(1)] if m.group(1) else [c.strip().split()[0] for c in m.group(2).split(',') if c.strip()]
        for u in urls:
            if re.match(r'^(?:[a-z]+:|//|#)', u, re.I) or not u:
                continue
            path = urllib.parse.unquote(urllib.parse.urlparse(u).path)
            target = (page.parent / path).resolve()
            checked += 1
            if target.is_dir():
                target = target / 'index.html'
            if not target.exists() or ROOT not in target.parents and target != ROOT:
                bad.setdefault(u, set()).add(str(page.relative_to(ROOT)))
print(f'{checked} relative references checked, {len(bad)} broken')
for u, pages in sorted(bad.items()):
    print(' ', u, '<-', sorted(pages)[:2])
sys.exit(1 if bad else 0)

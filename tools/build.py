#!/usr/bin/env python3
"""One-time migration tool: turns the crawled WordPress site into the static site.

The published site does NOT need this (no build step on GitHub Pages). It is kept
so the conversion can be re-run from a fresh crawl.

    python3 -I tools/build.py <crawl-dir> <cache-dir>

<crawl-dir>  wget mirror of https://fryohanna.net/ (the fryohanna.net/ folder)
<cache-dir>  where files fetched from other hosts (Photon CDN, Google Photos,
             jQuery CDN) are cached between runs
"""
import hashlib
import json
import posixpath
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parent.parent
CRAWL = Path(sys.argv[1])
CACHE = Path(sys.argv[2])
CACHE.mkdir(parents=True, exist_ok=True)
HOST = 'fryohanna.net'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/130.0 Safari/537.36')
MAX_FILE = 50_000_000
LOG = {'unknown_links': {}, 'external_media': {}, 'removed': {}, 'fetch_failed': [],
       'big_files': []}

# Scripts the static site keeps (local copies). Everything else is dropped:
# analytics (gtag, Jetpack stats), OneSignal push, emoji, Polylang cookie, the
# debloat delay loader, speculation rules, Yoast JSON-LD.
KEEP_SCRIPTS = {
    'jquery-core-js': 'vendor/jquery.min.js',
    'jquery-migrate-js': 'vendor/jquery-migrate.min.js',
    'twentytwenty-js-js': 'theme.js',
    'pb-accordion-blocks-frontend-script-js': 'accordion.js',
    'yith-infinitescroll-js': 'infinite-scroll.js',
    'yith-infs-js': 'infinite-scroll-init.js',
    'automatic-youtube-gallery-public-js': 'youtube-gallery.js',
    'automatic-youtube-gallery-theme-classic-js': 'youtube-gallery-classic.js',
    'adb6b2c1e33052ebac488921fbc88b1b': 'vendor/owl.carousel.min.js',   # tribute sliders
    'e55b5359526dbe376a7a4858df720e98': 'slider-init.js',              # (debloat named it .css)
}
# Also dropped on purpose: 393b23078ffefcb92689e19bf23aa35c = WP YouTube Lyte (site.js
# replaces it); Photonic (its Google Photos galleries are already empty on the old site).
KEEP_INLINE = ('yith-infs-js-extra', 'automatic-youtube-gallery-public-js-extra')
DROP_STYLES = ('wp-emoji-styles-inline-css', 'jetpack-stats-inline-css')


# ---------------------------------------------------------------- pages
def key_from_file(p):
    rel = p.relative_to(CRAWL).as_posix()
    if rel == 'index.html':
        return ''
    if rel.endswith('/index.html'):
        return rel[:-len('/index.html')]
    if rel.endswith('.html'):                      # wget -E: "/en" saved as en.html
        return rel[:-5]
    return None


PAGES = {}
for p in sorted(CRAWL.rglob('*.html')):
    rel = p.relative_to(CRAWL).as_posix()
    if rel.startswith('wp-content/') or '?' in rel:
        continue
    k = key_from_file(p)
    if k is None or k in PAGES:
        continue
    PAGES[k] = p


def depth(key):
    return len(key.split('/')) if key else 0


def rel_to(from_key, target):
    """relative URL from page from_key to a site path (no leading slash)."""
    r = '../' * depth(from_key) + target
    return urllib.parse.quote(r, safe="/.#?=&%-_~") or './'


def page_href(from_key, to_key, frag=''):
    t = (to_key + '/') if to_key else ''
    r = rel_to(from_key, t) if t else ('../' * depth(from_key) or './')
    return r + frag


# ---------------------------------------------------------------- assets
def fetch(url):
    """download url into the cache, return the cached path or None."""
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    dst = CACHE / h
    if dst.exists():
        return dst
    if url in FAILED:
        return None
    print('fetch', url[:120], file=sys.stderr, flush=True)
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            dst.write_bytes(data)
            return dst
        except Exception as e:  # noqa: BLE001 (logged, page keeps the remote URL)
            err = str(e)
            time.sleep(1 + attempt)
    LOG['fetch_failed'].append(f'{url} ({err})')
    FAILED.add(url)
    return None


FAILED = set()


ASSETS = {}   # site path -> source file


def add_asset(site_path, src):
    if src is None:
        return False
    size = src.stat().st_size
    if size > MAX_FILE:
        LOG['big_files'].append(f'{site_path} {size}')
        return False
    ASSETS[site_path] = src
    return True


def ext_of(url, default='.jpg'):
    e = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return e if e in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg') else default


def localize(url):
    """absolute asset URL -> site path (no leading slash), or None to keep it remote."""
    u = urllib.parse.urlparse(url.strip())
    host = u.netloc.lower()
    path = posixpath.normpath(urllib.parse.unquote(u.path)) if u.path else ''
    if host in ('i0.wp.com', 'i1.wp.com', 'i2.wp.com', 'i3.wp.com') and path.startswith('/' + HOST + '/'):
        path = path[len(HOST) + 1:]
        host = HOST
    if host in (HOST, 'www.' + HOST):
        if 'lyteCache.php' in path:
            return None
        site = path.lstrip('/')
        if not site.startswith('wp-content/') or not Path(site).suffix:
            return None
        local = CRAWL / site
        src = local if local.is_file() else fetch(f'https://{HOST}/{urllib.parse.quote(site)}')
        return site if add_asset(site, src) else None
    if host == 'c0.wp.com':
        site = 'assets/js/vendor/' + Path(path).name
        return site if add_asset(site, fetch(url)) else None
    if host.endswith('googleusercontent.com') or host.endswith('fbcdn.net') or host == 'wp.fifu.app':
        h = hashlib.sha1(url.encode()).hexdigest()[:12]
        site = f'wp-content/uploads/external/{h}{ext_of(url)}'
        ok = add_asset(site, fetch(url))
        LOG['external_media'][url[:90]] = site if ok else 'FAILED'
        return site if ok else None
    return None


def lyte_thumb(url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    return q.get('origThumbUrl', [url])[0]


def fix_srcset(val, key):
    """keep the srcset, with local candidates only."""
    out = []
    for part in val.split(','):
        bits = part.strip().split()
        if not bits:
            continue
        loc = localize(bits[0])
        if loc:
            out.append(' '.join([rel_to(key, loc)] + bits[1:]))
    return ', '.join(out)


VOID_TAG = re.compile(r'<(link|meta|img|input|br|source|hr)\b((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)\s*/?\s*>', re.I)
INLINE_URL = re.compile(r'https://fryohanna\.net/wp-content/[^"\\]+')
CSS_URL = re.compile(r'url\((["\']?)(https?://[^"\')]+)\1\)')


def fix_css(text, key):
    def sub(m):
        loc = localize(m.group(2))
        return f'url({m.group(1)}{rel_to(key, loc) if loc else m.group(2)}{m.group(1)})'
    return CSS_URL.sub(sub, text)


# ---------------------------------------------------------------- links
def fix_href(href, key):
    u = urllib.parse.urlparse(href)
    if u.netloc.lower() not in (HOST, 'www.' + HOST):
        return href
    path = urllib.parse.unquote(u.path).strip('/')
    if path.startswith('wp-content/'):
        loc = localize(href)
        return rel_to(key, loc) if loc else href
    frag = ('#' + u.fragment) if u.fragment else ''
    if u.query:
        m = re.match(r'p=(\d+)', u.query)
        if m and path == '':
            LOG['unknown_links'].setdefault(href, set()).add(key)
            return href
    if path in PAGES:
        return page_href(key, path, frag)
    LOG['unknown_links'].setdefault(href, set()).add(key or '/')
    return href


# ---------------------------------------------------------------- page clean-up
def drop(el, why):
    LOG['removed'][why] = LOG['removed'].get(why, 0) + 1
    el.decompose()


def convert(key, src):
    # html.parser sometimes nests what follows a <link>/<meta> inside it (seen on these
    # pages); writing every void tag as <x ... /> first avoids that.
    raw = VOID_TAG.sub(lambda m: f'<{m.group(1)}{m.group(2)} />', src.read_text(encoding='utf-8'))
    soup = BeautifulSoup(raw, 'html.parser')
    html_el = soup.find('html')
    if html_el and 'no-js' in (html_el.get('class') or []):
        html_el['class'] = ['js' if c == 'no-js' else c for c in html_el['class']]

    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    # scripts
    for s in soup.find_all('script'):
        if getattr(s, 'decomposed', False):
            continue
        sid = s.get('id', '')
        if sid in KEEP_SCRIPTS:
            srcurl = s.get('src') or s.get('data-src') or ''
            loc = localize(srcurl) if 'c0.wp.com' in srcurl else None
            name = KEEP_SCRIPTS[sid]
            if not loc:
                site = 'assets/js/' + name
                f = CRAWL / urllib.parse.unquote(urllib.parse.urlparse(srcurl).path).lstrip('/')
                add_asset(site, f if f.is_file() else fetch(srcurl))
                loc = site
            new = soup.new_tag('script', src=rel_to(key, loc))
            new['defer'] = ''
            new['id'] = sid
            s.replace_with(new)
        elif sid in KEEP_INLINE:
            s.string = INLINE_URL.sub(lambda m: rel_to(key, localize(m.group()) or '') if localize(m.group())
                                      else m.group(), s.string or '')
        else:
            drop(s, 'script: ' + (sid or (s.get('type') or 'inline')))

    # head links
    for ln in soup.find_all('link'):
        if getattr(ln, 'decomposed', False):
            continue
        rel = ' '.join(ln.get('rel') or [])
        if rel in ('icon', 'apple-touch-icon', 'stylesheet'):
            loc = localize(ln.get('href', ''))
            if loc:
                ln['href'] = rel_to(key, loc)
            elif rel != 'stylesheet':
                drop(ln, 'link icon (remote)')
        elif rel == 'alternate' and ln.get('hreflang'):
            ln['href'] = fix_href(ln['href'], key)
        else:
            drop(ln, 'link ' + rel)
    for m in soup.find_all('meta', attrs={'name': ['generator', 'msapplication-TileImage']}):
        drop(m, 'meta generator')

    # styles
    for st in soup.find_all('style'):
        if getattr(st, 'decomposed', False):
            continue
        if st.get('id') in DROP_STYLES:
            drop(st, 'style ' + st['id'])
        else:
            st.string = fix_css(st.string or '', key)

    # junk elements
    for sel in ('#wpstats', '.onesignal-customlink-container', '#respond', '.comments-wrapper',
                '#wpadminbar', 'noscript'):
        for el in soup.select(sel):
            if getattr(el, 'decomposed', False):
                continue
            drop(el, 'element ' + sel)

    # lyte: point the thumbnails at YouTube directly; site.js makes them playable
    for el in soup.select('[data-src*="lyteCache.php"]'):
        el['data-src'] = lyte_thumb(el['data-src'])
    for m in soup.select('meta[itemprop=thumbnailUrl]'):
        m['content'] = lyte_thumb(m['content'])

    # images and media
    for el in soup.find_all(['img', 'source', 'video', 'audio', 'iframe']):
        if getattr(el, 'decomposed', False):
            continue
        for attr in ('src', 'data-src', 'poster'):
            v = el.get(attr)
            if v and v.startswith('http'):
                if 'lyteCache.php' in v:
                    el[attr] = lyte_thumb(v)
                    continue
                loc = localize(v)
                if loc:
                    el[attr] = rel_to(key, loc)
        if el.get('srcset'):
            fixed = fix_srcset(el['srcset'], key)
            if fixed:
                el['srcset'] = fixed
            else:
                del el['srcset']
                el.attrs.pop('sizes', None)
        el.attrs.pop('data-recalc-dims', None)
    for el in soup.find_all(style=True):
        el['style'] = fix_css(el['style'], key)

    # links
    for a in soup.find_all('a', href=True):
        a['href'] = fix_href(a['href'], key)
    for f in soup.find_all('form'):
        drop(f, 'form (posted to WordPress)')

    # our helper (lyte players)
    body = soup.find('body')
    for js in ('assets/js/config.js', 'assets/js/site.js'):
        s = soup.new_tag('script', src=rel_to(key, js))
        s['defer'] = ''
        body.append(s)
    head = soup.find('head')
    ln = soup.new_tag('link', rel='stylesheet', href=rel_to(key, 'assets/css/site.css'))
    head.append(ln)

    out = (ROOT / key / 'index.html') if key else (ROOT / 'index.html')
    out.parent.mkdir(parents=True, exist_ok=True)
    text = str(soup)
    out.write_text(text if text.lstrip().lower().startswith('<!doctype') else '<!DOCTYPE html>\n' + text,
                   encoding='utf-8')


def shortlinks():
    """?p=<id> links (WordPress shortlinks, shared on Facebook etc.) -> page path."""
    out = {}
    for f in CRAWL.glob('index.html[?]p=*.html'):
        pid = re.search(r'p=(\d+)', f.name).group(1)
        m = re.search(r'<link rel="canonical" href="([^"]+)"', f.read_text(encoding='utf-8'))
        if m:
            path = urllib.parse.unquote(urllib.parse.urlparse(m.group(1)).path).strip('/')
            if path in PAGES:
                out[pid] = path + '/' if path else ''
    (ROOT / 'assets' / 'shortlinks.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=0, sort_keys=True), encoding='utf-8')
    return len(out)


def main():
    for key, src in PAGES.items():
        convert(key, src)
    LOG['shortlinks'] = shortlinks()
    for site, src in ASSETS.items():
        dst = ROOT / site
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    report = {
        'pages': len(PAGES),
        'shortlinks': LOG['shortlinks'],
        'assets': len(ASSETS),
        'removed': LOG['removed'],
        'external_media': LOG['external_media'],
        'fetch_failed': LOG['fetch_failed'],
        'big_files': LOG['big_files'],
        'unknown_links': {k: sorted(v)[:3] for k, v in sorted(LOG['unknown_links'].items())},
    }
    (ROOT / 'tools' / 'build-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: (v if isinstance(v, int) else len(v)) for k, v in report.items()}))


if __name__ == '__main__':
    main()

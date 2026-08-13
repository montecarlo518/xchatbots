#!/usr/bin/env python3
"""Collect site + blog URLs and submit them to IndexNow (Bing/Yandex/DDG/Yahoo/Ecosia)."""
import json, re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from xml.etree import ElementTree as ET

HOST = "x-chatbots.com"
KEY  = "f059b8a52d94b862515b2e034433aa8e"
KEYLOC = f"https://{HOST}/{KEY}.txt"
UA = {"User-Agent": "xchatbots-indexnow/1.0"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

urls = set()

def parse_sitemap(url, depth=0):
    if depth > 3:
        return
    try:
        xml = get(url)
    except Exception as e:
        print("skip sitemap", url, e); return
    xml = re.sub(r'xmlns="[^"]+"', '', xml)
    try:
        root = ET.fromstring(xml)
    except Exception as e:
        print("parse err", url, e); return
    for loc in root.iter("loc"):
        u = (loc.text or "").strip()
        if not u:
            continue
        if u.endswith(".xml"):
            parse_sitemap(u, depth + 1)
        else:
            urls.add(u)

parse_sitemap(f"https://{HOST}/sitemap.xml")

# Blog is a separate Notion-powered service (not in sitemaps) -> scrape /blog
try:
    html = get(f"https://{HOST}/blog")
    for slug in re.findall(r'href="(?:https://x-chatbots\.com)?(/blog/[a-z0-9\-]+)"', html):
        urls.add(f"https://{HOST}{slug}")
except Exception as e:
    print("blog scrape failed", e)

urls = sorted(u for u in urls if u.startswith("http"))
print("collected", len(urls), "urls")

# Never submit dead URLs -- IndexNow penalises hosts that repeatedly submit
# non-200s, and a stale sitemap once fed ~75 404s into every run.
def alive(u):
    try:
        req = urllib.request.Request(u, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            return u if r.status == 200 else None
    except Exception:
        return None

with ThreadPoolExecutor(max_workers=8) as pool:
    checked = list(pool.map(alive, urls))

dead = [u for u, ok in zip(urls, checked) if ok is None]
urls = [u for u in checked if u]
if dead:
    print(f"skipping {len(dead)} non-200 urls:")
    for u in dead:
        print("  ", u)
print("submitting", len(urls), "urls")

if not urls:
    print("no urls; nothing to submit"); sys.exit(0)

payload = {"host": HOST, "key": KEY, "keyLocation": KEYLOC, "urlList": urls[:10000]}
data = json.dumps(payload).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=data,
      headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("IndexNow response:", r.status)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", "ignore")
    print("IndexNow HTTP", e.code, body)
    if e.code not in (200, 202):
        sys.exit(1)

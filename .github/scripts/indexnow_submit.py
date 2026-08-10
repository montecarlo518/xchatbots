#!/usr/bin/env python3
"""Collect site + blog URLs and submit them to IndexNow (Bing/Yandex/DDG/Yahoo/Ecosia)."""
import json, re, sys, urllib.request, urllib.error
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

parse_sitemap(f"https://{HOST}/sitemap-index.xml")

# Blog is a separate Notion-powered service (not in sitemaps) -> scrape /blog
try:
    html = get(f"https://{HOST}/blog")
    for slug in re.findall(r'href="(?:https://x-chatbots\.com)?(/blog/[a-z0-9\-]+)"', html):
        urls.add(f"https://{HOST}{slug}")
except Exception as e:
    print("blog scrape failed", e)

urls = sorted(u for u in urls if u.startswith("http"))
print("collected", len(urls), "urls")
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

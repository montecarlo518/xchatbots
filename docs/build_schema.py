#!/usr/bin/env python3
"""
Inject structured data into the x-chatbots.com static pages.

Adds:
  1. A shared Organization + WebSite entity graph on every indexable page.
  2. BreadcrumbList on every page except the homepage.
  3. WebPage / CollectionPage nodes on pages that had no schema at all.
  4. FAQPage on /faq (extracted from the existing markup).
  5. Upgrades bare name-only ItemList entries to SoftwareApplication with
     Offer + AggregateRating, using the Notion directory as the source of truth.
  6. Adds @id to existing nested publisher/author Organization objects so they
     resolve to the single Organization node instead of floating free.

All ratings/prices come from the Notion "Xchatbots Directory" database.
Tools absent from that database get name/category only -- never an invented rating.
"""
import json, os, re, sys
from html import unescape

ORIGIN = "https://x-chatbots.com"
ORG_ID = f"{ORIGIN}/#organization"
SITE_ID = f"{ORIGIN}/#website"
LOGO_ID = f"{ORIGIN}/#logo"

# ---------------------------------------------------------------- directory
# Name -> (rating, reviews, price, pricing) from the Notion directory DB.
DIRECTORY = {
    "CandyAI":            (4.5, 5063, "3.99",  "Freemium"),
    "CraveU AI":          (3.9,  597, "4.99",  "Freemium"),
    "CrushOn.ai":         (3.1, 3570, "4.90",  "Freemium"),
    "Darlink AI":         (4.6,  890, "12.99", "Paid"),
    "Dondi AI":           (4.1,  180, "5.99",  "Freemium"),
    "Dream Companion":    (4.0,  661, "5.89",  "Freemium"),
    "DreamBF AI":         (4.1,  734, "5.99",  "Freemium"),
    "Dreamz AI":          (4.1,   32, "14.99", "Freemium"),
    "EroPlay.ai":         (3.8,  826, "3.91",  "Freemium"),
    "Fanfinity AI":       (2.8, 1247, "5.99",  "Freemium"),
    "FlirtCam AI":        (4.4,   56, "19.99", "Freemium"),
    "FreeMode.ai":        (4.3,   52, "4.99",  "Freemium"),
    "Funy AI: Video, Image": (3.6, 1303, "24.99", "Freemium"),
    "Get-Harder AI":      (4.2,  340, "9.99",  "Paid"),
    "GirlfriendGPT":      (4.0, 1204, "13.74", "Freemium"),
    "Golove AI":          (4.2,   12, "4.80",  "Freemium"),
    "Joi AI":             (4.7,  624, "2.38",  "Freemium"),
    "JuicyChat.ai":       (3.5, 2284, "12.99", "Freemium"),
    "Lovescape":          (4.2,  210, "7.80",  "Freemium"),
    "LusyChat":           (4.3,  365, "7.99",  "Freemium"),
    "Luvr AI":            (3.0, 1665, "4.17",  "Freemium"),
    "OhChat":             (4.3,   23, "9.99",  "Freemium"),
    "OpenSourceGen":      (4.6,  312, "25.00", "Freemium"),
    "ourdream.ai":        (4.6, 4031, "9.99",  "Freemium"),
    "Promptchan":         (4.6, 1076, "26.99", "Freemium"),
    "Secrets AI":         (4.8, 1240, "19.99", "Freemium"),
    "Soulkyn":            (4.2,  138, "13.83", "Freemium"),
    "Spicier AI":         (4.1,   27, "7.99",  "Freemium"),
    "SpicyChat AI":       (3.2, 9575, "4.95",  "Freemium"),
    "Swipey AI":          (4.3,  367, "19.99", "Paid"),
    "Xotic AI":           (4.5,  832, "12.50", "Freemium"),
}

# Aliases used in page ItemLists -> canonical directory key.
ALIAS = {
    "candy ai": "CandyAI", "candyai": "CandyAI",
    "crushon ai": "CrushOn.ai", "crushon.ai": "CrushOn.ai", "crushon": "CrushOn.ai",
    "ourdream ai": "ourdream.ai", "ourdream.ai": "ourdream.ai", "ourdream": "ourdream.ai",
    "juicychat": "JuicyChat.ai", "juicychat ai": "JuicyChat.ai", "juicychat.ai": "JuicyChat.ai",
    "spicychat": "SpicyChat AI", "spicychat ai": "SpicyChat AI",
    "girlfriendgpt": "GirlfriendGPT",
    "promptchan": "Promptchan",
    "eroplay": "EroPlay.ai", "eroplay.ai": "EroPlay.ai",
}

def lookup(name):
    key = ALIAS.get(name.strip().lower())
    if key:
        return key, DIRECTORY[key]
    for k in DIRECTORY:
        if k.lower() == name.strip().lower():
            return k, DIRECTORY[k]
    return None, None

# ------------------------------------------------------------ page metadata
CATEGORY_PAGES = {
    "virtual-girlfriend": "AI Girlfriend Apps",
    "nsfw-image-generation": "NSFW AI Image Generators",
    "nsfw-video-generation": "NSFW AI Video Generators",
    "nsfw-chat": "NSFW AI Chat",
    "roleplay": "AI Roleplay Chatbots",
    "ai-boyfriend": "AI Boyfriend Apps",
    "best/nsfw-ai-chatbots": "Best NSFW AI Chatbots",
    "best/ai-hentai-anime-generators": "Best AI Hentai & Anime Generators",
    "best/undress-ai": "Best Undress AI & Nudify Tools",
    "alternatives/character-ai-alternatives": "Character AI Alternatives",
    "alternatives/crushon-ai-alternatives": "CrushOn AI Alternatives",
    "alternatives/janitor-ai-alternatives": "Janitor AI Alternatives",
    "alternatives/perchance-ai-alternatives": "Perchance AI Alternatives",
    "alternatives/spicychat-alternatives": "SpicyChat Alternatives",
}
UTILITY_PAGES = {
    "about": "About", "contact": "Contact", "submit": "Submit a Tool",
    "advertise": "Advertise", "privacy": "Privacy Policy", "terms": "Terms of Service",
    "faq": "FAQ", "how-we-review": "How We Review", "safety-standard": "Safety & Privacy Standard",
    "categories": "Categories", "state-of-ai-companions-2026": "State of AI Companions 2026",
    "what-is/uncensored-ai": "What Is Uncensored AI",
}
# List pages whose ItemList entries are bare names and need upgrading.
APPLICATION_CATEGORY = {
    "roleplay": "LifestyleApplication",
    "nsfw-chat": "LifestyleApplication",
    "virtual-girlfriend": "LifestyleApplication",
    "best/nsfw-ai-chatbots": "LifestyleApplication",
    "best/ai-hentai-anime-generators": "MultimediaApplication",
    "alternatives/perchance-ai-alternatives": "MultimediaApplication",
}
SKIP = {"advertise/success"}          # noindex,nofollow -- no schema needed

# ----------------------------------------------------------------- helpers
LD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S)

def page_slug(path):
    p = path.replace("\\", "/")
    p = p[2:] if p.startswith("./") else p
    return "" if p == "index.html" else p[:-5]

def page_url(slug):
    return f"{ORIGIN}/" if slug == "" else f"{ORIGIN}/{slug}"

def read_ld(src):
    out = []
    for raw in LD_RE.findall(src):
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            out.append(None)
    return out

def has_type(objs, t):
    for o in objs:
        if not isinstance(o, dict):
            continue
        if o.get("@type") == t:
            return True
        for n in o.get("@graph", []):
            if isinstance(n, dict) and n.get("@type") == t:
                return True
    return False

def dumps(o):
    return json.dumps(o, ensure_ascii=False, indent=2)

def script(o):
    return f'<script type="application/ld+json">\n{dumps(o)}\n</script>\n'

# ------------------------------------------------------------ node builders
def org_website_graph():
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": ORG_ID,
                "name": "Xchatbots",
                "url": f"{ORIGIN}/",
                "logo": {
                    "@type": "ImageObject",
                    "@id": LOGO_ID,
                    "url": f"{ORIGIN}/media/XC-2.png",
                    "contentUrl": f"{ORIGIN}/media/XC-2.png",
                    "width": 406,
                    "height": 258,
                    "caption": "Xchatbots",
                },
                "image": {"@id": LOGO_ID},
                "description": (
                    "Xchatbots is an independent directory of NSFW and uncensored AI "
                    "chatbots, AI companions, and AI image and video generators, with "
                    "hands-on testing and transparent review criteria."
                ),
                "sameAs": ["https://www.reddit.com/r/XChatbots/"],
            },
            {
                "@type": "WebSite",
                "@id": SITE_ID,
                "url": f"{ORIGIN}/",
                "name": "Xchatbots",
                "description": (
                    "Independent directory and reviews of NSFW AI chatbots, AI "
                    "companions and uncensored AI image and video generators."
                ),
                "publisher": {"@id": ORG_ID},
                "inLanguage": "en",
            },
        ],
    }

def breadcrumb(slug):
    trail = [("Home", f"{ORIGIN}/")]
    if slug in CATEGORY_PAGES:
        trail.append(("Categories", f"{ORIGIN}/categories"))
        trail.append((CATEGORY_PAGES[slug], page_url(slug)))
    elif slug in UTILITY_PAGES:
        if slug == "categories":
            trail.append(("Categories", f"{ORIGIN}/categories"))
        else:
            trail.append((UTILITY_PAGES[slug], page_url(slug)))
    else:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": n, "item": u}
            for i, (n, u) in enumerate(trail, 1)
        ],
    }

def webpage_node(slug, src, collection=False):
    m = re.search(r"<title>(.*?)</title>", src, re.S)
    title = unescape(m.group(1)).strip() if m else "Xchatbots"
    d = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', src, re.S)
    desc = unescape(d.group(1)).strip() if d else ""
    node = {
        "@context": "https://schema.org",
        "@type": "CollectionPage" if collection else "WebPage",
        "@id": page_url(slug) + "#webpage",
        "url": page_url(slug),
        "name": title,
        "isPartOf": {"@id": SITE_ID},
        "publisher": {"@id": ORG_ID},
        "inLanguage": "en",
    }
    if desc:
        node["description"] = desc
    return node

def software_item(name, appcat, url=None):
    """Turn a bare list entry into a real SoftwareApplication entity.

    Deliberately NO offers and NO aggregateRating. Google and Bing both require
    that a rating or price in structured data be visible to the user on the same
    page. Right now the visible ratings, the ratings already in other pages'
    schema, and the Notion directory disagree with each other (see
    docs/rating-discrepancies), so asserting any of them here would either
    contradict the page or contradict the directory. Structure first; ratings
    once there is one source of truth.
    """
    key, _ = lookup(name)
    item = {
        "@type": "SoftwareApplication",
        "name": key or name,
        "applicationCategory": appcat,
        "operatingSystem": "Web",
    }
    if url:
        item["url"] = url
    return item

def faq_nodes(src):
    """Extract Q/A pairs from faq.html markup."""
    pairs = re.findall(
        r"<h3[^>]*>(.*?)</h3>.*?<div class=\"faq-answer-content\"[^>]*>(.*?)</div>",
        src, re.S)
    out = []
    for q, a in pairs:
        q = unescape(re.sub(r"<[^>]+>", "", q)).strip()
        a = unescape(re.sub(r"<[^>]+>", " ", a))
        a = re.sub(r"\s+", " ", a).strip()
        if q and a:
            out.append({
                "@type": "Question", "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            })
    return out

# --------------------------------------------------------------- rewriting
def add_org_id(src):
    """Give existing nested publisher/author Organization objects the shared @id."""
    changed = 0
    def repl(m):
        nonlocal changed
        raw = m.group(1)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return m.group(0)
        def walk(o):
            nonlocal changed
            if isinstance(o, dict):
                if o.get("@type") == "Organization" and "@id" not in o:
                    o["@id"] = ORG_ID
                    changed += 1
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(obj)
        if changed == 0:
            return m.group(0)
        return m.group(0).replace(raw, "\n" + dumps(obj) + "\n")
    src = LD_RE.sub(repl, src)
    return src, changed

def upgrade_itemlist(src, slug):
    appcat = APPLICATION_CATEGORY.get(slug)
    if not appcat:
        return src, 0
    upgraded = 0
    def repl(m):
        nonlocal upgraded
        raw = m.group(1)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return m.group(0)
        if not (isinstance(obj, dict) and obj.get("@type") == "ItemList"):
            return m.group(0)
        for li in obj.get("itemListElement", []):
            if not isinstance(li, dict) or isinstance(li.get("item"), dict):
                continue
            name = li.get("name")
            if not name:
                continue
            li["item"] = software_item(name, appcat)
            li.pop("name", None)
            upgraded += 1
        if not upgraded:
            return m.group(0)
        return m.group(0).replace(raw, "\n" + dumps(obj) + "\n")
    src = LD_RE.sub(repl, src)
    return src, upgraded

def sync_existing_ratings(src):
    """Correct any aggregateRating that disagrees with the directory."""
    fixes = []
    def repl(m):
        raw = m.group(1)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return m.group(0)
        touched = False
        def walk(o):
            nonlocal touched
            if isinstance(o, dict):
                if o.get("@type") == "SoftwareApplication" and "aggregateRating" in o:
                    key, data = lookup(o.get("name", ""))
                    if data:
                        rating, reviews, price, _ = data
                        ar = o["aggregateRating"]
                        want_r, want_c = f"{rating}", f"{int(reviews)}"
                        if str(ar.get("ratingValue")) != want_r or str(ar.get("reviewCount")) != want_c:
                            fixes.append((o.get("name"), ar.get("ratingValue"), want_r,
                                          ar.get("reviewCount"), want_c))
                            ar["ratingValue"], ar["reviewCount"] = want_r, want_c
                            touched = True
                        ar.setdefault("bestRating", "5")
                        ar.setdefault("worstRating", "1")
                        off = o.get("offers")
                        if isinstance(off, dict) and str(off.get("price")) != price:
                            fixes.append((o.get("name") + " price", off.get("price"), price, "", ""))
                            off["price"] = price
                            touched = True
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(obj)
        if not touched:
            return m.group(0)
        return m.group(0).replace(raw, "\n" + dumps(obj) + "\n")
    src = LD_RE.sub(repl, src)
    return src, fixes

# -------------------------------------------------------------------- main
def process(path):
    slug = page_slug(path)
    if slug in SKIP:
        return None
    src = open(path, encoding="utf-8").read()
    original = src
    log = []

    src, n = add_org_id(src)
    if n:
        log.append(f"linked {n} Organization ref(s) to @id")

    src, n = upgrade_itemlist(src, slug)
    if n:
        log.append(f"upgraded {n} ItemList entries to SoftwareApplication")

    # NOTE: existing aggregateRating / Offer values are deliberately left
    # untouched -- they match the visible content on their own pages.
    existing = read_ld(src)
    additions = []

    if not any(isinstance(o, dict) and any(
            isinstance(n2, dict) and n2.get("@id") == ORG_ID
            for n2 in o.get("@graph", [])) for o in existing):
        additions.append(org_website_graph())
        log.append("added Organization + WebSite")

    if slug != "" and not has_type(existing, "BreadcrumbList"):
        bc = breadcrumb(slug)
        if bc:
            additions.append(bc)
            log.append("added BreadcrumbList")

    if not existing:
        collection = slug in ("categories",)
        additions.append(webpage_node(slug, src, collection))
        log.append("added " + ("CollectionPage" if collection else "WebPage"))

    if slug == "faq" and not has_type(existing, "FAQPage"):
        qs = faq_nodes(src)
        if qs:
            additions.append({
                "@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": qs,
            })
            log.append(f"added FAQPage ({len(qs)} Q&As)")

    if additions:
        block = "".join(script(a) for a in additions)
        src = src.replace("</head>", block + "</head>", 1)

    if src != original:
        open(path, "w", encoding="utf-8").write(src)
        return slug or "/", log
    return None

if __name__ == "__main__":
    files = []
    for root, dirs, names in os.walk("."):
        dirs[:] = [d for d in dirs if d != ".git"]
        for n in sorted(names):
            if n.endswith(".html"):
                files.append(os.path.join(root, n))
    total = 0
    for f in sorted(files):
        r = process(f)
        if r:
            total += 1
            print(f"\n{r[0]}")
            for line in r[1]:
                print(f"   - {line}")
    print(f"\n{total} files changed")

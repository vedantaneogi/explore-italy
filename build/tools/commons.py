#!/usr/bin/env python3
"""Find and verify Wikimedia Commons photos for the site.

  python3 build/tools/commons.py search "Val d'Orcia cypress" [--n 8] [--any]
  python3 build/tools/commons.py article "Val d'Orcia" [--n 8] [--any]   # photos used on an English Wikipedia article
  python3 build/tools/commons.py file "File:Some photo.jpg"

(commons.wikimedia.org is unreachable from this machine, so search goes through
api.wikimedia.org and metadata through en.wikipedia.org; both resolve Commons files.)

Prints JSON. Each result has an `image` object ready to paste into data files:
  {"url": <1280px thumb>, "alt": "", "credit": "Artist, LICENSE, via Wikimedia Commons", "page": <file page>}
By default keeps only landscape JPEGs >= 1600px wide. --any drops the shape/size filter.
"""
import hashlib, html, json, os, random, re, subprocess, sys, time, urllib.parse

UA = "ExploreItalyStaticSite/1.0 (educational travel guide build script)"
WP = "https://en.wikipedia.org/w/api.php"
SEARCH = "https://api.wikimedia.org/core/v1/commons/search/page"

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")

def get(url, params):
    """GET JSON with an on-disk cache and backoff (Wikimedia rate-limits bursts with HTTP 429)."""
    full = url + "?" + urllib.parse.urlencode(params)
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, hashlib.sha1(full.encode()).hexdigest() + ".json")
    if os.path.exists(cf):
        with open(cf) as fh:
            return json.load(fh)
    delay = 3
    for attempt in range(8):
        # curl, not urllib: this Python build lacks a CA bundle
        out = subprocess.run(["curl", "-sS", "-m", "40", "-A", UA, full], capture_output=True, text=True).stdout
        try:
            data = json.loads(out)
        except ValueError:
            time.sleep(delay + random.random() * 2)
            delay = min(delay * 2, 60)
            continue
        with open(cf, "w") as fh:
            json.dump(data, fh)
        return data
    sys.exit("Wikimedia API kept refusing (rate limit). Wait a minute and retry.")

def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(re.sub(r"\s+", " ", s)).strip()

PROPS = {"prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "1280",
         "iiextmetadatafilter": "Artist|LicenseShortName|ImageDescription",
         "format": "json", "formatversion": "2"}

def to_image(p):
    ii = (p.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata") if isinstance(ii.get("extmetadata"), dict) else {}
    artist = clean(meta.get("Artist", {}).get("value", "")) or "Unknown author"
    if len(artist) > 60: artist = artist[:57] + "..."
    lic = clean(meta.get("LicenseShortName", {}).get("value", ""))
    credit = ", ".join(x for x in [artist, lic, "via Wikimedia Commons"] if x)
    url = (ii.get("thumburl") or ii.get("url") or "").split("?")[0]
    url = url.replace("https://thumb.wikimedia.org/", "https://upload.wikimedia.org/")
    return {"title": p["title"], "width": ii.get("width", 0), "height": ii.get("height", 0),
            "mime": ii.get("mime"),
            "description": clean(meta.get("ImageDescription", {}).get("value", ""))[:160],
            "image": {"url": url, "alt": "", "credit": credit,
                      "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_"))}}

def keep(im, any_shape):
    if im["mime"] != "image/jpeg": return False
    return any_shape or (im["width"] >= 1600 and im["width"] > im["height"] * 1.15)

def info(titles):
    out = {}
    for i in range(0, len(titles), 40):
        d = get(WP, {"action": "query", "titles": "|".join(titles[i:i+40]), **PROPS})
        for p in d["query"]["pages"]:
            if "imageinfo" in p: out[p["title"]] = to_image(p)
    return [out[t] for t in titles if t in out]

def search(q, n=8, any_shape=False):
    d = get(SEARCH, {"q": q + " filetype:bitmap", "limit": "40"})
    titles = [p["title"] for p in d.get("pages", []) if p["title"].startswith("File:")]
    return [im for im in info(titles) if keep(im, any_shape)][:n]

def article(title, n=8, any_shape=False):
    d = get(WP, {"action": "query", "generator": "images", "titles": title, "gimlimit": "100", "redirects": "1", **PROPS})
    ims = [to_image(p) for p in d.get("query", {}).get("pages", []) if "imageinfo" in p]
    return [im for im in ims if keep(im, any_shape)][:n]

def file(title):
    if not title.startswith("File:"): title = "File:" + title
    r = info([title])
    return r[0] if r else {"error": "not found", "title": title}

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    n = int(a[a.index("--n") + 1]) if "--n" in a else 8
    if a[0] == "search": res = search(a[1], n, "--any" in a)
    elif a[0] == "article": res = article(a[1], n, "--any" in a)
    elif a[0] == "file": res = file(a[1])
    else: sys.exit(__doc__)
    print(json.dumps(res, indent=1, ensure_ascii=False))

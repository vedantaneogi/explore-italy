#!/usr/bin/env python3
"""Build the Explore Italy static site from the JSON in build/data.

    python3 build/build.py

Writes plain HTML pages into the project root. Every link is relative, so the
site works opened straight from disk or served from any static host.
"""
import glob, html, json, os, re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "build", "data")

AREAS = [
    ("north", "The North", "Alps, lakes, lagoon cities and the richest kitchens in the country."),
    ("central", "The Centre", "Hill towns, Renaissance cities, Rome, and the green Apennine spine."),
    ("south", "The South", "Volcanoes, baroque towns, two seas and the deepest roots of Italian food."),
    ("islands", "The Islands", "Sicily and Sardinia: whole worlds of their own, each with its own sea."),
]
REGION_ORDER = ["valle-daosta", "piedmont", "liguria", "lombardy", "trentino-alto-adige", "veneto",
                "friuli-venezia-giulia", "emilia-romagna", "tuscany", "umbria", "marche", "lazio",
                "abruzzo", "molise", "campania", "puglia", "basilicata", "calabria", "sicily", "sardinia"]
SECTIONS = {
    "experiences": ("Experiences", "Art, history, music, theatre, festivals and landscapes.",
                    ["heritage", "history", "music-dance", "theatre", "festivals", "nature"]),
    "taste": ("Taste", "Regional food, wine, cheese and coffee, and where to find them.",
              ["food", "wine", "cheese", "coffee"]),
    "discover": ("Discover", "Hidden places, day trips, historic tables and local stays.",
                 ["hidden-gems", "day-trips", "legacy-restaurants", "stay-local"]),
    "plan": ("Plan", "Entry rules, transport, seasons and the links you'll need to book.",
             ["plan-essentials", "plan-getting-around", "plan-when-to-go", "plan-booking-links"]),
}
SECTION_ORDER = ["experiences", "taste", "discover", "plan"]
ITIN_ORDER = ["classic-italy-10-days", "tuscany-umbria-slow-8-days", "amalfi-naples-7-days",
              "puglia-matera-9-days", "sicily-grand-loop-12-days", "dolomites-lakes-9-days",
              "food-valley-7-days", "hidden-italy-14-days"]
FLAVOUR_GROUPS = [("Plates", ["dish", "bread"]), ("Cheese", ["cheese"]), ("Cured meats", ["cured meat"]),
                  ("Wine", ["wine"]), ("Coffee & spirits", ["coffee", "spirit"]),
                  ("Oil", ["olive oil"]), ("Sweets", ["sweet"])]

# ---------------------------------------------------------------- data

def tidy(node):
    """Drop image placeholders that aren't real image objects (e.g. while content is being written)."""
    if isinstance(node, dict):
        return {k: (None if k in ("image", "hero_image") and not isinstance(v, dict) else tidy(v)) for k, v in node.items()}
    if isinstance(node, list):
        return [tidy(x) for x in node]
    return node

def load(pattern):
    out = {}
    for f in sorted(glob.glob(os.path.join(DATA, pattern))):
        with open(f, encoding="utf-8") as fh:
            d = tidy(json.load(fh))
        out[d.get("slug") or os.path.splitext(os.path.basename(f))[0]] = d
    return out

REGIONS = load("regions/*.json")
PAGES = load("pages/*.json")
ITINS = load("itineraries/*.json")

def ordered(keys, pool):
    seen = [k for k in keys if k in pool]
    return seen + sorted(k for k in pool if k not in seen)

REGION_SLUGS = ordered(REGION_ORDER, REGIONS)
ITIN_SLUGS = ordered(ITIN_ORDER, ITINS)

def page_slug(p):
    return re.sub(r"^plan-", "", p["slug"])

def section_pages(sec):
    keys = SECTIONS[sec][2]
    pool = {k: v for k, v in PAGES.items() if v.get("section") == sec}
    return [pool[k] for k in ordered(keys, pool)]

# ---------------------------------------------------------------- helpers

E = lambda s: html.escape(str(s or ""), quote=True)
CREDITS = {}

def slugify(s):
    s = re.sub(r"[^\w\s-]", "", str(s).lower().replace("'", ""))
    return re.sub(r"[\s_]+", "-", s).strip("-")[:60]

def para(text):
    return "".join(f"<p>{E(p)}</p>" for p in ([text] if isinstance(text, str) else (text or [])) if p)

def img(im, eager=False, sizes="(max-width: 700px) 100vw, 33vw"):
    if not isinstance(im, dict) or not im.get("url", "").startswith("http"):
        return ""
    CREDITS.setdefault(im["url"], im)
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img src="{E(im["url"])}" alt="{E(im.get("alt"))}" {load} decoding="async" '
            f'sizes="{sizes}" title="{E(im.get("credit"))}">')

def fit(n):
    """Four columns instead of three when three would leave a lone orphan on the last row."""
    return ' data-cols="4"' if n > 1 and n % 3 == 1 else ""

def ext(url, label, cls="ext"):
    if not url:
        return ""
    return f'<a class="{cls}" href="{E(url)}" target="_blank" rel="noopener">{E(label)}</a>'

class Page:
    def __init__(self, path):
        self.path = path
        self.depth = path.count("/")

    def u(self, target):
        return "../" * self.depth + target

def region_url(slug):
    return f"regions/{slug}.html"

def gpage_url(p):
    return f'{p["section"]}/{page_slug(p)}.html'

def itin_url(slug):
    return f"itineraries/{slug}.html"

def area_label(a):
    return {k: n for k, n, _ in AREAS}.get(a, "")

# ---------------------------------------------------------------- layout

def nav(pg, current):
    def cur(k):
        return ' aria-current="true"' if current == k else ""
    cols = []
    for key, label, _ in AREAS:
        items = "".join(f'<li><a href="{pg.u(region_url(s))}">{E(REGIONS[s]["name"])}</a></li>'
                        for s in REGION_SLUGS if REGIONS[s].get("area") == key)
        cols.append(f'<div><h4><span class="dot {key}"></span>{label}</h4><ul>{items}</ul></div>')
    out = [f'<li><a href="{pg.u("regions/index.html")}"{cur("regions")}>Regions</a>'
           f'<div class="drop drop-regions">{"".join(cols)}'
           f'<a class="all" href="{pg.u("regions/index.html")}">All 20 regions</a></div></li>']
    for sec in SECTION_ORDER[:3]:
        out.append(section_drop(pg, sec, cur(sec)))
    its = "".join(f'<li><a href="{pg.u(itin_url(s))}">{E(ITINS[s]["title"])}</a></li>' for s in ITIN_SLUGS)
    out.append(f'<li><a href="{pg.u("itineraries/index.html")}"{cur("itineraries")}>Itineraries</a>'
               f'<div class="drop"><ul>{its}</ul><a class="all" href="{pg.u("itineraries/index.html")}">All itineraries</a></div></li>')
    out.append(section_drop(pg, "plan", cur("plan")))
    return "".join(out)

def section_drop(pg, sec, cur):
    label = SECTIONS[sec][0]
    items = "".join(f'<li><a href="{pg.u(gpage_url(p))}">{E(p["title"])}</a></li>' for p in section_pages(sec))
    return (f'<li><a href="{pg.u(sec + "/index.html")}"{cur}>{label}</a>'
            f'<div class="drop"><ul>{items}</ul><a class="all" href="{pg.u(sec + "/index.html")}">All of {label.lower()}</a></div></li>')

def mobile_nav(pg):
    blocks = []
    regs = "".join(f'<li><a href="{pg.u(region_url(s))}">{E(REGIONS[s]["name"])}</a></li>' for s in REGION_SLUGS)
    blocks.append(f'<section><h4><a href="{pg.u("regions/index.html")}">Regions</a></h4><ul>{regs}</ul></section>')
    for sec in SECTION_ORDER[:3]:
        blocks.append(mobile_block(pg, sec))
    its = "".join(f'<li><a href="{pg.u(itin_url(s))}">{E(ITINS[s]["title"])}</a></li>' for s in ITIN_SLUGS)
    blocks.append(f'<section><h4><a href="{pg.u("itineraries/index.html")}">Itineraries</a></h4><ul>{its}</ul></section>')
    blocks.append(mobile_block(pg, "plan"))
    return f'<details class="mnav"><summary>Menu</summary><nav class="mnav-panel" aria-label="Site">{"".join(blocks)}</nav></details>'

def mobile_block(pg, sec):
    items = "".join(f'<li><a href="{pg.u(gpage_url(p))}">{E(p["title"])}</a></li>' for p in section_pages(sec))
    return f'<section><h4><a href="{pg.u(sec + "/index.html")}">{SECTIONS[sec][0]}</a></h4><ul>{items}</ul></section>'

def footer(pg):
    def col(title, links):
        lis = "".join(f'<li><a href="{pg.u(h)}">{E(t)}</a></li>' for t, h in links)
        return f"<div><h4>{title}</h4><ul>{lis}</ul></div>"
    regions = [(REGIONS[s]["name"], region_url(s)) for s in REGION_SLUGS]
    half = (len(regions) + 1) // 2
    exp = [(p["title"], gpage_url(p)) for p in section_pages("experiences") + section_pages("taste")]
    disc = [(p["title"], gpage_url(p)) for p in section_pages("discover")] + [("Itineraries", "itineraries/index.html")] + \
           [(p["title"], gpage_url(p)) for p in section_pages("plan")]
    return f"""<footer class="site-foot"><div class="stars" aria-hidden="true"></div><div class="wrap">
<div class="foot-top">
  <div><a class="brand" href="{pg.u("index.html")}"><b>Explore Italy</b><span>twenty regions, one long table</span></a>
  <p style="max-width:36ch;margin-top:18px">An independent guide to planning a trip through Italy, region by region. We don't sell anything: every booking link goes straight to the official source or the operator.</p></div>
  {col("Regions", regions[:half])}{col("&nbsp;", regions[half:])}{col("Experiences & taste", exp)}{col("Discover & plan", disc)}
</div>
<div class="foot-note"><span>Photographs from Wikimedia Commons contributors, used under their licences. <a href="{pg.u("credits.html")}">Photo credits</a> &nbsp; <a href="{pg.u("sitemap.html")}">Site map</a></span>
<span>Information checked {date.today():%B %Y}. Always confirm opening times and rules with the official source before you travel.</span></div>
</div></footer>"""

def layout(pg, title, desc, current, body):
    full = "Explore Italy" if title == "Explore Italy" else f"{title} | Explore Italy"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full)}</title>
<meta name="description" content="{E(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..700;1,6..96,400..700&family=Instrument+Sans:wght@400..700&display=swap">
<link rel="stylesheet" href="{pg.u("assets/css/style.css")}">
<link rel="icon" href="{pg.u("assets/favicon.svg")}" type="image/svg+xml">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="{pg.u("index.html")}"><b>Explore Italy</b><span>Italia</span></a>
<nav aria-label="Main"><ul class="nav">{nav(pg, current)}</ul></nav>
{mobile_nav(pg)}
</div></header>
<main id="main">
{body}
</main>
{footer(pg)}
</body>
</html>
"""

def hero(im, h1, standfirst="", kicker="", short=True, place=""):
    credit = ""
    if im:
        credit = (f'<p class="placard">{f"<strong>{E(place)}</strong>" if place else ""}'
                  f'Photo: {ext(im.get("page"), im.get("credit", "Wikimedia Commons"), "")}</p>')
    return f"""<section class="hero{" hero-short" if short else ""}">
{img(im, eager=True, sizes="100vw")}
<div class="wrap">{f'<p class="kicker">{kicker}</p>' if kicker else ""}<h1>{E(h1)}</h1>{f'<p class="standfirst">{E(standfirst)}</p>' if standfirst else ""}</div>
{credit}
</section>"""

def crumbs(pg, trail):
    lis = "".join(f'<li><a href="{pg.u(h)}">{E(t)}</a></li>' if h else f'<li aria-current="page">{E(t)}</li>' for t, h in trail)
    return f'<nav class="crumbs wrap" aria-label="Breadcrumb"><ol>{lis}</ol></nav>'

def section_head(h2, lead="", more=None, sid=""):
    m = f'<a class="more" href="{more[1]}">{E(more[0])}</a>' if more else ""
    right = f"<div>{f'<p>{E(lead)}</p>' if lead else ''}{m}</div>" if (lead or m) else "<div></div>"
    return f'<div class="section-head"{f" id={chr(34)}{sid}{chr(34)}" if sid else ""}><h2>{E(h2)}</h2>{right}</div>'

def pager(pg, prev, nxt):
    if not prev and not nxt:
        return ""
    a = f'<a href="{pg.u(prev[1])}"><span>Previous</span><b>{E(prev[0])}</b></a>' if prev else "<span></span>"
    b = f'<a class="next" href="{pg.u(nxt[1])}"><span>Next</span><b>{E(nxt[0])}</b></a>' if nxt else "<span></span>"
    return f'<nav class="wrap pager" aria-label="More pages">{a}{b}</nav>'

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)
    BUILT.append(path)

BUILT = []

# ---------------------------------------------------------------- item renderers

def item_links(pg, it):
    links = []
    if it.get("region") in REGIONS:
        links.append(f'<a href="{pg.u(region_url(it["region"]))}">{E(REGIONS[it["region"]]["name"])} guide</a>')
    if it.get("url"):
        links.append(ext(it["url"], it.get("url_label") or "Official site"))
    return links

def render_items(pg, layout_name, items, arch=False):
    if layout_name == "rows":
        rows = []
        for it in items:
            links = item_links(pg, it)
            rows.append(f"""<article class="row" id="{slugify(it.get("title"))}">
<figure>{img(it.get("image"), sizes="(max-width: 760px) 100vw, 45vw")}</figure>
<div><h3>{E(it.get("title"))}</h3>{f'<p class="sub">{E(it["subtitle"])}</p>' if it.get("subtitle") else ""}
{f'<p class="meta">{E(it["meta"])}</p>' if it.get("meta") else ""}<div class="desc">{para(it.get("desc"))}</div>
{f'<p class="links">{"".join(links)}</p>' if links else ""}</div></article>""")
        return f'<div class="rows">{"".join(rows)}</div>'
    if layout_name == "timeline":
        rows = []
        for it in items:
            links = item_links(pg, it)
            rows.append(f"""<article id="{slugify(it.get("title"))}"><p class="when">{E(it.get("meta"))}</p>
<div class="what"><h3>{E(it.get("title"))}</h3>{f'<p class="sub" style="color:var(--ink-3);margin-bottom:6px">{E(it["subtitle"])}</p>' if it.get("subtitle") else ""}
<p class="desc">{E(it.get("desc"))}</p>{f'<p class="links">{" &nbsp; ".join(links)}</p>' if links else ""}</div></article>""")
        return f'<div class="timeline">{"".join(rows)}</div>'
    if layout_name == "list" or not any(it.get("image") for it in items):
        rows = []
        for it in items:
            links = item_links(pg, it)
            rows.append(f"""<article id="{slugify(it.get("title"))}"><div><h3>{E(it.get("title"))}</h3>
{f'<p class="sub">{E(it["subtitle"])}</p>' if it.get("subtitle") else ""}{f'<p class="since">{E(it["meta"])}</p>' if it.get("meta") else ""}</div>
<div><p class="desc">{E(it.get("desc"))}</p>{f'<p class="links">{"".join(links)}</p>' if links else ""}</div></article>""")
        return f'<div class="ledger">{"".join(rows)}</div>'
    cards = []
    for it in items:
        links = item_links(pg, it)
        cards.append(f"""<article class="card" id="{slugify(it.get("title"))}">
<figure>{img(it.get("image"))}</figure>
<h3>{E(it.get("title"))}</h3>{f'<p class="sub">{E(it["subtitle"])}</p>' if it.get("subtitle") else ""}
{f'<p class="meta">{E(it["meta"])}</p>' if it.get("meta") else ""}<p class="desc">{E(it.get("desc"))}</p>
{f'<p class="links">{"".join(links)}</p>' if links else ""}</article>""")
    return f'<div class="cards{" arch" if arch else ""}"{fit(len(cards))}>{"".join(cards)}</div>'

def tips_block(tips, title="Good to know"):
    if not tips:
        return ""
    lis = "".join(f"<li>{E(t)}</li>" for t in tips)
    return f'<section class="section wrap"><div class="tips"><h2>{title}</h2><ul>{lis}</ul></div></section>'

def links_block(links, title="Useful links", lead="Official sources and trusted operators. Links open in a new tab."):
    if not links:
        return ""
    a = "".join(f'<a href="{E(l.get("url"))}" target="_blank" rel="noopener"><b>{E(l.get("label"))}</b><span>{E(l.get("desc"))}</span></a>'
                for l in links if l.get("url"))
    return f'<section class="section wrap">{section_head(title, lead)}<div class="linklist">{a}</div></section>'

# ---------------------------------------------------------------- cross references

def mentions(slug):
    """Items across generic pages tagged with this region."""
    out = []
    for p in PAGES.values():
        for s in p.get("sections", []):
            for it in s.get("items", []):
                if it.get("region") == slug:
                    out.append((p, it))
    return out

# ---------------------------------------------------------------- pages

def build_region(slug, i):
    r = REGIONS[slug]
    pg = Page(region_url(slug))
    area = r.get("area", "")
    kicker = (f'<span class="dot {area}"></span><a href="{pg.u("regions/index.html")}#{area}">{area_label(area)}</a>'
              + (f' &nbsp;/&nbsp; {E(r["italian_name"])}' if r.get("italian_name", r["name"]) != r["name"] else ""))
    out = [hero(r.get("hero_image"), r["name"], r.get("tagline"), kicker, short=False,
                place=(r.get("hero_image") or {}).get("alt", ""))]
    out.append(crumbs(pg, [("Home", "index.html"), ("Regions", "regions/index.html"), (r["name"], None)]))

    tabs = [("overview", "Overview"), ("places", "Places"), ("things-to-do", "Things to do"),
            ("flavours", "Flavours"), ("legacy-tables", "Legacy tables"), ("stay", "Stay local"),
            ("day-trips", "Day trips"), ("hidden-gems", "Hidden gems"), ("festivals", "Festivals"),
            ("culture", "Culture")]
    present = {"overview": True, "places": r.get("places"), "things-to-do": r.get("things_to_do"),
               "flavours": r.get("flavours"), "legacy-tables": r.get("legacy_restaurants"),
               "stay": r.get("stay_local"), "day-trips": r.get("day_trips"), "hidden-gems": r.get("hidden_gems"),
               "festivals": r.get("festivals"), "culture": r.get("culture")}
    tabs = [t for t in tabs if present.get(t[0])]

    facts = [("Capital", r.get("capital")), ("Best time to go", r.get("best_time")),
             ("Getting there and around", r.get("getting_there"))]
    dl = "".join(f"<div><dt>{k}</dt><dd>{E(v)}</dd></div>" for k, v in facts if v)
    tags = "".join(f"<li>{E(t)}</li>" for t in r.get("known_for", []))
    official = f'<div><dt>Official tourism site</dt><dd class="official">{ext(r["official_site"], r["official_site"].split("//")[-1].strip("/"))}</dd></div>' if r.get("official_site") else ""
    out.append(f"""<section class="wrap region-intro" id="overview">
<div class="body">{para(r.get("intro"))}{f'<ul class="tags" aria-label="Known for">{tags}</ul>' if tags else ""}</div>
<dl class="facts">{dl}{official}</dl></section>""")
    out.append('<nav class="subnav" aria-label="On this page"><div class="wrap"><ul>' +
               "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in tabs) + "</ul></div></nav>")

    if r.get("places"):
        items = [{"title": p["name"], "desc": p.get("desc"), "image": p.get("image")} for p in r["places"]]
        out.append(f'<section class="section wrap" id="places">{section_head("Places to know", "Where to spend your days in " + r["name"] + ", from the big names to the towns locals choose for a Sunday.")}{render_items(pg, "cards", items, arch=True)}</section>')
    if r.get("things_to_do"):
        arts = "".join(f'<article><h3>{E(t["title"])}</h3><p>{E(t.get("desc"))}</p></article>' for t in r["things_to_do"])
        out.append(f'<section class="section wrap" id="things-to-do">{section_head("Things to do", "Experiences that only make sense here.")}<div class="todo"{fit(len(r["things_to_do"]))}>{arts}</div></section>')
    if r.get("flavours"):
        groups = []
        fl = r["flavours"]
        used = set()
        for label, types in FLAVOUR_GROUPS:
            its = [f for f in fl if (f.get("type") or "").lower() in types]
            used.update(id(f) for f in its)
            if its:
                groups.append((label, its))
        rest = [f for f in fl if id(f) not in used]
        if rest:
            groups.append(("Also on the table", rest))
        g = "".join(f'<div class="menu-group"><h3>{E(l)}</h3>' +
                    "".join(f'<div class="menu-item"><b>{E(f["name"])}</b><span>{E(f.get("desc"))}</span></div>' for f in its) +
                    "</div>" for l, its in groups)
        out.append(f'<section class="section wrap" id="flavours"><div class="menu-card">{section_head("What to eat and drink", "The flavours of " + r["name"] + ", as you would order them at the counter or the table.")}<div class="menu-groups">{g}</div></div></section>')
    if r.get("legacy_restaurants"):
        items = [{"title": x["name"], "subtitle": x.get("city"), "meta": f'Since {x["since"]}' if x.get("since") else "",
                  "desc": x.get("desc"), "url": x.get("url"), "url_label": "Website"} for x in r["legacy_restaurants"]]
        out.append(f'<section class="section wrap" id="legacy-tables">{section_head("Legacy tables", "Historic restaurants, cafés and bakeries that have been feeding locals for generations.", ("More legacy tables across Italy", pg.u("discover/legacy-restaurants.html")))}{render_items(pg, "list", items)}</section>')
    if r.get("stay_local"):
        def stay(s):
            link = f'<p class="meta">{ext(s["url"], "See options")}</p>' if s.get("url") else ""
            return f'<article><h3>{E(s["title"])}</h3><p>{E(s.get("desc"))}</p>{link}</article>'
        arts = "".join(stay(s) for s in r["stay_local"])
        out.append(f'<section class="section wrap" id="stay">{section_head("Stay like a local", "Farm stays, village houses and family homes where you live alongside the people who belong here.", ("How local stays work", pg.u("discover/stay-local.html")))}<div class="todo"{fit(len(r["things_to_do"]))}>{arts}</div></section>')
    if r.get("day_trips"):
        arts = "".join(f'<article><h3>{E(d.get("from"))} to {E(d.get("to"))}</h3><p>{E(d.get("desc"))}</p><p class="meta">{E(d.get("how"))}</p></article>'
                       for d in r["day_trips"])
        out.append(f'<section class="section wrap" id="day-trips">{section_head("Day trips", "Out in the morning, back for dinner.", ("Day trips from every major city", pg.u("discover/day-trips.html")))}<div class="todo"{fit(len(r["things_to_do"]))}>{arts}</div></section>')
    if r.get("hidden_gems"):
        items = [{"title": h["name"], "desc": h.get("desc"), "image": h.get("image")} for h in r["hidden_gems"]]
        out.append(f'<section class="section wrap" id="hidden-gems">{section_head("Hidden gems", "Lesser-known corners that reward the detour.", ("Hidden gems across Italy", pg.u("discover/hidden-gems.html")))}{render_items(pg, "cards", items)}</section>')
    if r.get("festivals"):
        items = [{"title": f["name"], "subtitle": f.get("where"), "meta": f.get("when"), "desc": f.get("desc"),
                  "url": f.get("url"), "url_label": "Event info"} for f in r["festivals"]]
        out.append(f'<section class="section wrap" id="festivals">{section_head("Festivals", "When to time your visit.", ("The festival calendar", pg.u("experiences/festivals.html")))}{render_items(pg, "list", items)}</section>')
    if r.get("culture"):
        out.append(f"""<section class="section wrap" id="culture"><div class="split">
<figure>{img((r.get("places") or [{}])[-1].get("image") if r.get("places") else None, sizes="(max-width:860px) 100vw, 45vw")}</figure>
<div><h2>Music, craft and custom</h2><p>{E(r["culture"])}</p>
<p><a class="btn" href="{pg.u("experiences/music-dance.html")}">Music and dance across Italy</a></p></div></div></section>""")

    trips = [s for s in ITIN_SLUGS if slug in ITINS[s].get("regions", [])]
    refs = mentions(slug)
    if trips or refs:
        tr = "".join(itin_card(pg, s) for s in trips)
        rf = "".join(f'<a href="{pg.u(gpage_url(p))}#{slugify(it.get("title"))}"><b>{E(it.get("title"))}</b><span>{E(p["title"])}</span></a>'
                     for p, it in refs[:18])
        block = '<section class="section wrap">' + section_head("Plan " + r["name"] + " into your trip", "Itineraries that pass through, and more from this region across the guide.")
        if tr:
            block += f'<div class="trips">{tr}</div>'
        if rf:
            block += f'<div class="linklist linklist-int" style="margin-top:48px">{rf}</div>'
        out.append(block + "</section>")

    prev = REGION_SLUGS[i - 1] if i > 0 else None
    nxt = REGION_SLUGS[i + 1] if i + 1 < len(REGION_SLUGS) else None
    out.append(pager(pg, prev and (REGIONS[prev]["name"], region_url(prev)), nxt and (REGIONS[nxt]["name"], region_url(nxt))))
    write(pg.path, layout(pg, r["name"], r.get("tagline", ""), "regions", "\n".join(out)))

def region_tile(pg, s):
    r = REGIONS[s]
    it = f'<span class="it">{E(r["italian_name"])}</span>' if r.get("italian_name") and r["italian_name"] != r["name"] else ""
    return (f'<a class="tile" href="{pg.u(region_url(s))}"><figure>{img(r.get("hero_image"), sizes="(max-width:700px) 50vw, 20vw")}</figure>'
            f'<h3>{E(r["name"])}</h3>{it}<p>{E(r.get("tagline"))}</p></a>')

def build_regions_index():
    pg = Page("regions/index.html")
    first = PAGES.get("nature") or {}
    out = [hero(first.get("hero_image"), "Twenty regions", "Each with its own dialect, kitchen, saints, festivals and landscapes. Choose one, or string a few together.", short=True,
                place=(first.get("hero_image") or {}).get("alt", ""))]
    out.append(crumbs(pg, [("Home", "index.html"), ("Regions", None)]))
    for key, label, blurb in AREAS:
        slugs = [s for s in REGION_SLUGS if REGIONS[s].get("area") == key]
        if not slugs:
            continue
        tiles = "".join(region_tile(pg, s) for s in slugs)
        out.append(f'<section class="area {key} wrap" id="{key}"><div class="area-head"><h2>{label}</h2><p>{blurb}</p></div><div class="region-tiles">{tiles}</div></section>')
    write(pg.path, layout(pg, "Regions of Italy", "Guides to all twenty regions of Italy.", "regions", "\n".join(out)))

def build_generic(p, sec_pages, i):
    pg = Page(gpage_url(p))
    sec = p["section"]
    out = [hero(p.get("hero_image"), p.get("headline") or p["title"], p.get("tagline"),
                f'<a href="{pg.u(sec + "/index.html")}">{SECTIONS[sec][0]}</a> &nbsp;/&nbsp; {E(p["title"])}',
                place=(p.get("hero_image") or {}).get("alt", ""))]
    out.append(crumbs(pg, [("Home", "index.html"), (SECTIONS[sec][0], sec + "/index.html"), (p["title"], None)]))
    secs = p.get("sections", [])
    intro = p.get("intro") or []
    intro = intro if isinstance(intro, list) else [intro]
    toc = "".join(f'<li><a href="#{slugify(s["heading"])}">{E(s["heading"])}</a></li>' for s in secs)
    out.append(f'<section class="wrap lede"><nav class="toc" aria-label="In this guide"><h2>In this guide</h2><ol>{toc}</ol></nav><div class="body">{para(intro)}</div></section>')
    for s in secs:
        out.append(f'<section class="section wrap" id="{slugify(s["heading"])}">{section_head(s["heading"], s.get("intro", ""))}'
                   f'{render_items(pg, s.get("layout", "cards"), s.get("items", []))}</section>')
    out.append(tips_block(p.get("tips")))
    out.append(links_block(p.get("links")))
    prev = sec_pages[i - 1] if i > 0 else None
    nxt = sec_pages[i + 1] if i + 1 < len(sec_pages) else None
    out.append(pager(pg, prev and (prev["title"], gpage_url(prev)), nxt and (nxt["title"], gpage_url(nxt))))
    write(pg.path, layout(pg, p["title"], p.get("tagline", ""), sec, "\n".join(out)))

def build_section_index(sec):
    pages = section_pages(sec)
    if not pages:
        return
    pg = Page(f"{sec}/index.html")
    label, blurb, _ = SECTIONS[sec]
    lead = pages[0]
    out = [hero(lead.get("hero_image"), label, blurb, short=True, place=(lead.get("hero_image") or {}).get("alt", ""))]
    out.append(crumbs(pg, [("Home", "index.html"), (label, None)]))
    cards = "".join(f"""<article class="card"><figure>{img(p.get("hero_image"))}</figure>
<h3><a href="{pg.u(gpage_url(p))}">{E(p["title"])}</a></h3><p class="desc">{E(p.get("tagline"))}</p>
<p class="links"><a href="{pg.u(gpage_url(p))}">Read the {E(p["title"].lower())} guide</a></p></article>""" for p in pages)
    out.append(f'<section class="section wrap"><div class="index-grid">{cards}</div></section>')
    if sec == "discover":
        out.append(f'<section class="section wrap">{section_head("Itineraries", "Ready-made routes, day by day.", ("All itineraries", pg.u("itineraries/index.html")))}<div class="trips">{"".join(itin_card(pg, s) for s in ITIN_SLUGS[:3])}</div></section>')
    write(pg.path, layout(pg, label, blurb, sec, "\n".join(out)))

def itin_card(pg, s):
    t = ITINS[s]
    return (f'<a class="trip" href="{pg.u(itin_url(s))}"><figure>{img(t.get("hero_image"))}</figure>'
            f'<span class="days">{E(t.get("days"))} days, {E(str(t.get("style", "")).lower())}</span>'
            f'<h3>{E(t["title"])}</h3><p>{E(t.get("tagline"))}</p>'
            f'<p class="route">{E(" to ".join(t.get("route", [])[:1] + t.get("route", [])[-1:]) if len(t.get("route", [])) > 1 else "")}</p></a>')

def build_itin(s, i):
    t = ITINS[s]
    pg = Page(itin_url(s))
    out = [hero(t.get("hero_image"), t.get("headline") or t["title"], t.get("tagline"),
                f'<a href="{pg.u("itineraries/index.html")}">Itineraries</a> &nbsp;/&nbsp; {E(t.get("days"))} days',
                place=(t.get("hero_image") or {}).get("alt", ""))]
    out.append(crumbs(pg, [("Home", "index.html"), ("Itineraries", "itineraries/index.html"), (t["title"], None)]))
    facts = [("Length", f'{t.get("days")} days'), ("Best season", t.get("best_season")),
             ("Getting around", t.get("getting_around")), ("Budget", t.get("budget_note"))]
    dl = "".join(f"<div><dt>{k}</dt><dd>{E(v)}</dd></div>" for k, v in facts if v)
    route = "".join(f"<li>{E(x)}</li>" for x in t.get("route", []))
    out.append(f"""<section class="wrap lede"><p class="lead-quote">{E(t.get("title"))}</p><div class="body">{para(t.get("summary"))}</div></section>
<section class="wrap"><ol class="line" aria-label="Route">{route}</ol><dl class="trip-facts">{dl}</dl></section>""")
    days = []
    for d in t.get("days_plan", []):
        hl = "".join(f"<li>{E(h)}</li>" for h in d.get("highlights", []))
        aside = "".join(f"<dt>{k}</dt><dd>{E(v)}</dd>" for k, v in (("Eat", d.get("eat")), ("Stay", d.get("stay"))) if v)
        label = "Days" if "-" in str(d.get("day")) or "–" in str(d.get("day")) else "Day"
        days.append(f"""<article><p class="dno">{label}<b>{E(d.get("day"))}</b></p>
<div><h3>{E(d.get("title"))}</h3><p class="base">Base: {E(d.get("base"))}</p><div class="desc">{para(d.get("desc"))}</div>{f"<ul>{hl}</ul>" if hl else ""}</div>
{f"<aside><dl>{aside}</dl></aside>" if aside else "<span></span>"}</article>""")
    out.append(f'<section class="section wrap">{section_head("Day by day", "Swap days around freely; the order follows the most efficient route.")}<div class="days-plan">{"".join(days)}</div></section>')
    out.append(tips_block(t.get("tips"), "Before you go"))
    out.append(links_block(t.get("book"), "Book ahead", "Tickets and transport to reserve before you travel, on official sites."))
    regs = [r for r in t.get("regions", []) if r in REGIONS]
    if regs:
        out.append(f'<section class="section wrap">{section_head("Regions on this route")}<div class="region-tiles">{"".join(region_tile(pg, r) for r in regs)}</div></section>')
    prev = ITIN_SLUGS[i - 1] if i > 0 else None
    nxt = ITIN_SLUGS[i + 1] if i + 1 < len(ITIN_SLUGS) else None
    out.append(pager(pg, prev and (ITINS[prev]["title"], itin_url(prev)), nxt and (ITINS[nxt]["title"], itin_url(nxt))))
    write(pg.path, layout(pg, t["title"], t.get("tagline", ""), "itineraries", "\n".join(out)))

def build_itin_index():
    pg = Page("itineraries/index.html")
    first = ITINS[ITIN_SLUGS[0]] if ITIN_SLUGS else {}
    out = [hero(first.get("hero_image"), "Itineraries", "Day-by-day routes with real trains, real tables and the tickets worth booking ahead. Follow one exactly or borrow the best days.",
                place=(first.get("hero_image") or {}).get("alt", ""))]
    out.append(crumbs(pg, [("Home", "index.html"), ("Itineraries", None)]))
    out.append(f'<section class="section wrap"><div class="trips">{"".join(itin_card(pg, s) for s in ITIN_SLUGS)}</div></section>')
    dt = PAGES.get("day-trips")
    if dt:
        out.append(f'<section class="section wrap"><div class="split"><figure>{img(dt.get("hero_image"))}</figure><div><h2>Short on time?</h2><p>{E(dt.get("tagline"))}</p><p><a class="btn" href="{pg.u(gpage_url(dt))}">See day trips</a></p></div></div></section>')
    write(pg.path, layout(pg, "Itineraries", "Day-by-day Italy itineraries.", "itineraries", "\n".join(out)))

def build_home():
    pg = Page("index.html")
    with open(os.path.join(DATA, "site.json"), encoding="utf-8") as fh:
        hero_src = json.load(fh).get("home_hero")
    out = [hero(hero_src, "Twenty regions, one long table", "Plan a trip through Italy's art, food, music and landscapes, region by region, the way Italians travel it themselves.",
                short=False, place=(hero_src or {}).get("alt", ""))]
    out.append("""<section class="wrap lede"><p class="lead-quote">Italy isn't one country to tick off. It's twenty, each with its own dialect, its own bread and its own idea of the perfect evening.</p>
<div class="body"><p>Start with a region and you'll find the towns worth your days, what to order, the family tables that have been open for a century and the festivals worth timing a trip around. Follow an itinerary if you want the route worked out, or wander through the experiences, from opera houses to cheese dairies.</p>
<p>Everything here is information, not a sales pitch. Where you need to book a train, a museum slot or a farm stay, we link straight to the official source.</p></div></section>""")

    feat = [s for s in ["piedmont", "veneto", "tuscany", "lazio", "campania", "puglia", "sicily", "sardinia"] if s in REGIONS]
    out.append(f'<section class="section wrap">{section_head("Start with a region", "From the Alps of Valle d’Aosta to the islands off Sicily. Pick a region to see where to go, what to eat and where to sleep.", ("All twenty regions", pg.u("regions/index.html")))}'
               f'<div class="region-tiles">{"".join(region_tile(pg, s) for s in feat)}</div></section>')

    ways = [("heritage", "w7"), ("history", "w5"), ("music-dance", "w4"), ("theatre", "w4"), ("festivals", "w4"),
            ("nature", "w8"), ("food", "w4")]
    tiles = ""
    for slug, w in ways:
        p = PAGES.get(slug)
        if p:
            tiles += f'<a class="way {w}" href="{pg.u(gpage_url(p))}">{img(p.get("hero_image"), sizes="(max-width:900px) 100vw, 50vw")}<div><h3>{E(p["title"])}</h3><p>{E(p.get("tagline"))}</p></div></a>'
    out.append(f'<section class="section wrap">{section_head("Ways into Italy", "Culture, history, music, theatre and landscape. Choose the thread you want to follow.", ("All experiences", pg.u("experiences/index.html")))}<div class="ways">{tiles}</div></section>')

    if ITIN_SLUGS:
        out.append(f'<section class="band"><div class="stars" aria-hidden="true"></div><div class="wrap">{section_head("Ready-made routes", "From a first trip through Rome, Florence and Venice to two slow weeks in the regions most visitors miss.", ("All itineraries", pg.u("itineraries/index.html")))}'
                   f'<div class="trips">{"".join(itin_card(pg, s) for s in ITIN_SLUGS[:6])}</div></div></section>')

    taste = section_pages("taste")
    legacy = PAGES.get("legacy-restaurants")
    if taste:
        lis = "".join(f'<li><a href="{pg.u(gpage_url(p))}">{E(p["title"])}<span>{E(p.get("headline"))}</span></a></li>' for p in taste + ([legacy] if legacy else []))
        im = (PAGES.get("cheese") or taste[0]).get("hero_image")
        out.append(f'<section class="section wrap"><div class="split"><figure>{img(im, sizes="(max-width:860px) 100vw, 45vw")}</figure><div><h2>Eat and drink like you live here</h2>'
                   f'<p>Every region has its own pasta, cheese, wine and coffee ritual. Learn what to order, where it\'s made and which tables have been serving it longest.</p><ul>{lis}</ul></div></div></section>')

    gems = PAGES.get("hidden-gems")
    if gems:
        items = [it for s in gems.get("sections", []) for it in s.get("items", []) if it.get("image")][:6]
        out.append(f'<section class="section wrap">{section_head("Hidden gems", "Villages, islands and quiet cities that most visitors drive past.", ("See all hidden gems", pg.u(gpage_url(gems))))}{render_items(pg, "cards", items)}</section>')

    stay = PAGES.get("stay-local")
    if stay:
        lis = "".join(f'<li><a href="{pg.u(gpage_url(stay))}#{slugify(it["title"])}">{E(it["title"])}<span>{E(it.get("subtitle") or "")}</span></a></li>'
                      for it in [it for s in stay.get("sections", [])[:1] for it in s.get("items", [])][:5])
        out.append(f'<section class="section wrap"><div class="split"><div><h2>Stay with the people who live here</h2><p>{E(stay.get("tagline"))}</p><ul>{lis}</ul>'
                   f'<a class="btn" href="{pg.u(gpage_url(stay))}">How to stay like a local</a></div><figure>{img(stay.get("hero_image"), sizes="(max-width:860px) 100vw, 45vw")}</figure></div></section>')

    fest = PAGES.get("festivals")
    if fest:
        cal = next((s for s in fest.get("sections", []) if s.get("layout") == "list"), None)
        if cal:
            out.append(f'<section class="section wrap">{section_head("The year in festivals", "Palios, processions, harvests and music nights. Time your trip around one.", ("Full festival calendar", pg.u(gpage_url(fest))))}{render_items(pg, "list", cal["items"][:6])}</section>')

    plan = section_pages("plan")
    if plan:
        a = "".join(f'<a href="{pg.u(gpage_url(p))}"><b>{E(p["title"])}</b><span>{E(p.get("tagline"))}</span></a>' for p in plan)
        out.append(f'<section class="section wrap">{section_head("Plan the practical part", "Visas, trains, ferries, seasons and the official booking links, in one place.")}<div class="linklist linklist-int">{a}</div></section>')
    write(pg.path, layout(pg, "Explore Italy", "Plan a trip to Italy region by region: culture, food, wine, festivals, hidden gems, itineraries and local stays.", "home", "\n".join(out)))

def build_credits():
    pg = Page("credits.html")
    ps = "".join(f'<p>{ext(im.get("page"), (im.get("alt") or "Photo"), "")}: {E(im.get("credit"))}</p>'
                 for im in sorted(CREDITS.values(), key=lambda x: (x.get("alt") or "").lower()))
    body = (crumbs(pg, [("Home", "index.html"), ("Photo credits", None)]) +
            f'<section class="section wrap">{section_head("Photo credits", "Every photograph on this site comes from Wikimedia Commons and is used under the licence chosen by its author. Select a title to see the original file and its full licence.")}<div class="credits">{ps}</div></section>')
    write(pg.path, layout(pg, "Photo credits", "Photo credits", "", body))

def build_sitemap():
    pg = Page("sitemap.html")
    groups = [("Home", [("Explore Italy", "index.html")]),
              ("Regions", [("All regions", "regions/index.html")] + [(REGIONS[s]["name"], region_url(s)) for s in REGION_SLUGS])]
    for sec in SECTION_ORDER:
        groups.append((SECTIONS[sec][0], [(f"All of {SECTIONS[sec][0].lower()}", f"{sec}/index.html")] + [(p["title"], gpage_url(p)) for p in section_pages(sec)]))
    groups.append(("Itineraries", [("All itineraries", "itineraries/index.html")] + [(ITINS[s]["title"], itin_url(s)) for s in ITIN_SLUGS]))
    cols = "".join(f'<div><h3 style="font-size:1.6rem;margin-bottom:12px">{E(g)}</h3><ul style="list-style:none;padding:0;margin:0">' +
                   "".join(f'<li style="padding:4px 0"><a href="{pg.u(h)}">{E(t)}</a> <span style="color:var(--ink-3);font-size:.85rem">/{E(h)}</span></li>' for t, h in links) +
                   "</ul></div>" for g, links in groups)
    body = (crumbs(pg, [("Home", "index.html"), ("Site map", None)]) +
            f'<section class="section wrap">{section_head("Site map", "Every page on the site and its address.")}<div class="cards" style="gap:48px">{cols}</div></section>')
    write(pg.path, layout(pg, "Site map", "Every page on Explore Italy.", "", body))

def main():
    build_home()
    build_regions_index()
    for i, s in enumerate(REGION_SLUGS):
        build_region(s, i)
    for sec in SECTION_ORDER:
        pages = section_pages(sec)
        build_section_index(sec)
        for i, p in enumerate(pages):
            build_generic(p, pages, i)
    if ITIN_SLUGS:
        build_itin_index()
    for i, s in enumerate(ITIN_SLUGS):
        build_itin(s, i)
    build_sitemap()
    build_credits()
    print(f"Built {len(BUILT)} pages: {len(REGIONS)} regions, {len(PAGES)} guides, {len(ITINS)} itineraries, {len(CREDITS)} photos")

if __name__ == "__main__":
    main()

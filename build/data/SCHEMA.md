# Content data schemas

All site content lives in JSON files in this folder; `build/build.py` turns them into static HTML.
Write valid UTF-8 JSON (no comments, no trailing commas). Validate with `python3 -m json.tool <file> > /dev/null`.

## Image object (used everywhere an `image` / `hero_image` appears)

```json
{"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/.../1280px-....jpg",
 "alt": "Plain description of what is in the photo",
 "credit": "Author, CC BY-SA 4.0, via Wikimedia Commons",
 "page": "https://commons.wikimedia.org/wiki/File:...."}
```

Get these ONLY from `python3 build/tools/commons.py` (search / article / file) - run it with the sandbox disabled
(it needs network). Never invent a URL. Pick photos that are beautiful, bright, sharp, landscape, and clearly show
the subject (no maps, diagrams, logos, people posing in the foreground, night-time blur, or dull museum record shots).
Always write a real `alt`. Tidy `credit` if the author string is messy (keep it short: "Name, LICENSE, via Wikimedia Commons").

## Region file: `regions/<slug>.json`

```json
{
 "slug": "tuscany",
 "name": "Tuscany",
 "italian_name": "Toscana",
 "area": "central",                       // one of: north | central | south | islands
 "capital": "Florence",
 "tagline": "One evocative sentence, <= 14 words, specific to the region.",
 "intro": ["Paragraph 1 (60-90 words)", "Paragraph 2 (60-90 words)"],
 "hero_image": {image},
 "known_for": ["Renaissance art", "Chianti", "..."],          // 5-7 short tags
 "best_time": "One or two sentences with months and why.",
 "getting_there": "Airports, main rail hubs, how to get around (car / train / ferry). 2-3 sentences.",
 "places": [                                                  // 5-6 must-see cities/towns/sites
   {"name": "Florence", "desc": "40-70 words: what it is and what to do there.", "image": {image}}
 ],
 "things_to_do": [ {"title": "Walk the walls of Lucca", "desc": "25-50 words"} ],   // 6-8 concrete experiences
 "flavours": [                                                // 6-10 signature foods/drinks
   {"name": "Pecorino Toscano DOP", "type": "cheese", "desc": "15-35 words"}
 ],                                                           // type: dish | cheese | wine | coffee | sweet | cured meat | olive oil | spirit | bread
 "legacy_restaurants": [                                      // 3-5 REAL historic places still operating (verify!)
   {"name": "Trattoria Sostanza", "city": "Florence", "since": "1869", "desc": "20-40 words: why it matters, what to order.", "url": "official site if one exists, else omit"}
 ],
 "stay_local": [                                              // 2-4 ways to stay like a local here, ideally with named real examples
   {"title": "Wine-estate agriturismo in Chianti", "desc": "30-50 words", "url": "optional real link"}
 ],
 "day_trips": [ {"from": "Florence", "to": "Siena", "how": "1h15 by bus", "desc": "20-40 words"} ],   // 2-4
 "hidden_gems": [ {"name": "Pitigliano", "desc": "30-50 words", "image": {image}} ],              // 3-4, image optional but preferred
 "festivals": [ {"name": "Palio di Siena", "when": "2 July & 16 August", "where": "Siena", "desc": "20-40 words", "url": "optional"} ],  // 2-4
 "culture": "60-110 words on the region's own music, dance, theatre, crafts, dialect, traditions.",
 "official_site": "https://www.visittuscany.com/en/"          // regional tourism board (verify it loads)
}
```

## Generic page file: `pages/<slug>.json`

Used for experience pages, food & drink pages, hidden gems, day trips, legacy restaurants, stay-like-a-local, planning pages.

```json
{
 "slug": "wine",
 "section": "experiences",            // experiences | taste | discover | plan   (decides where the page lives in the nav)
 "title": "Wine",                     // short nav title
 "headline": "Display headline for the page, <= 9 words",
 "tagline": "One sentence standfirst, <= 30 words.",
 "hero_image": {image},
 "intro": ["Paragraph (60-100 words)", "Paragraph"],
 "sections": [
   {
    "heading": "Section heading",
    "intro": "Optional 1-3 sentence lead-in",
    "layout": "cards",                // cards (image cards) | list (text entries) | timeline (dated sequence) | rows (big alternating image+text)
    "items": [
      {"title": "Barolo", "subtitle": "Piedmont, from Nebbiolo grapes", "desc": "30-70 words", "image": {image},
       "meta": "Optional short fact line e.g. 'Since 1760' or 'Sept-Oct' or '2h from Rome'",
       "region": "piedmont",          // optional region slug, creates a link to the region guide
       "url": "optional external link (official site / booking / info)", "url_label": "optional link text e.g. 'Book a tour'"}
    ]
   }
 ],
 "tips": ["Optional practical tips, one sentence each"],
 "links": [ {"label": "Official resource name", "url": "https://...", "desc": "What you'll find there"} ]   // external resources/booking
}
```
For `timeline` sections, put the date/era in `meta`. For `cards`/`rows` every item needs an image; `list` items need none.

## Itinerary file: `itineraries/<slug>.json`

```json
{
 "slug": "classic-italy-10-days",
 "title": "Rome, Florence & Venice",
 "headline": "Display headline, <= 8 words",
 "days": 10,
 "style": "First trip",                // short label: First trip | Food & wine | Coast | Mountains | Slow travel | Islands ...
 "tagline": "One sentence",
 "hero_image": {image},
 "summary": "80-120 words",
 "route": ["Rome", "Florence", "Venice"],
 "regions": ["lazio", "tuscany", "veneto"],   // region slugs
 "best_season": "...",
 "getting_around": "...",
 "budget_note": "Rough daily budget ranges in EUR (mid-range), one sentence",
 "days_plan": [
   {"day": "1-2", "title": "Ancient Rome", "base": "Rome",
    "desc": "70-120 words of what to actually do",
    "highlights": ["Colosseum at opening", "..."],
    "eat": "A real place or dish to try", "stay": "Neighbourhood / type of stay"}
 ],
 "tips": ["..."],
 "book": [ {"label": "Trenitalia", "url": "https://www.trenitalia.com/en.html", "desc": "Rome-Florence fast trains"} ]
}
```

Region slugs: valle-daosta, piedmont, liguria, lombardy, trentino-alto-adige, veneto, friuli-venezia-giulia,
emilia-romagna, tuscany, umbria, marche, lazio, abruzzo, molise, campania, puglia, basilicata, calabria, sicily, sardinia.

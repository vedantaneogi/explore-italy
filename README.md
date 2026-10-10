# Explore Italy

A static travel guide for planning a trip to Italy: twenty region guides, experiences (heritage, history,
music & dance, theatre, festivals, scenery), food & drink, hidden gems, day trips, legacy restaurants,
local stays, itineraries and practical planning. Plain HTML + one CSS file, no JavaScript, no build
dependencies. It can be opened from disk or deployed to any static host.

## Routes

| Path | What's there |
|---|---|
| `/index.html` | Home |
| `/regions/` | All 20 regions grouped by North, Centre, South, Islands |
| `/regions/<region>.html` | Region guide: places, things to do, flavours, legacy tables, local stays, day trips, hidden gems, festivals, culture |
| `/experiences/` | `heritage`, `history`, `music-dance`, `theatre`, `festivals`, `nature` |
| `/taste/` | `food`, `wine`, `cheese`, `coffee` |
| `/discover/` | `hidden-gems`, `day-trips`, `legacy-restaurants`, `stay-local` |
| `/itineraries/` | Day-by-day routes |
| `/plan/` | `essentials`, `getting-around`, `when-to-go`, `booking-links` |
| `/sitemap.html`, `/credits.html` | Every page; photo credits |

## Editing content

All content lives in `build/data/` as JSON (format in `build/data/SCHEMA.md`). After editing:

```bash
python3 build/build.py
```

That regenerates every HTML page. Styles are in `assets/css/style.css`.

Photos are hot-linked from Wikimedia Commons and credited on `/credits.html`.
`build/tools/commons.py` finds properly licensed photos and their credits.

## Preview locally

```bash
python3 -m http.server 8765
```

Then open http://localhost:8765.

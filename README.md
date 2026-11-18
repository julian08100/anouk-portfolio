# anoukphilipsen.com

Portfolio van kunstenaar Anouk Philipsen (GitHub Pages, eigen domein via `CNAME`).

## Structuur
- `index.html` — **de bron** (Nederlands). Bewerk alleen dit bestand.
- `en/index.html` — Engelse versie, **gegenereerd**; niet met de hand bewerken.
- `images/` — schilderijen (originele JPG + WebP 640/1200 px) en de deelafbeelding `og-anouk-philipsen.jpg`.
- `sitemap.xml`, `robots.txt`, `llms.txt`, favicons, `site.webmanifest`, `404.html`.

## Na elke wijziging aan index.html
```
python3 tools/build.py
```
Dit vernieuwt de Engelse pagina, de structured data (JSON-LD) en de sitemap, en meldt
Nederlandse tekst die nog geen Engelse vertaling heeft (voeg die toe aan `EN{}` in het script onderaan index.html).

## Nieuw schilderij toevoegen
1. Zet `images/anouk-philipsen-abstract-schilderij-<kleuren>.jpg` neer (beschrijvende naam, kleine letters, streepjes).
2. Maak WebP-versies: `cwebp -q 80 -resize 640 0 in.jpg -o <naam>-640.webp` (en 1200).
3. Kopieer een `<article class="work">` in index.html, pas `src`/`srcset`/`width`/`height`/`alt` aan
   (alt = beschrijving mét "van Anouk Philipsen") en vul de Engelse alt aan in `EN{}`.
4. `python3 tools/build.py`, committen, pushen.

## Talen
`/` is Nederlands, `/en/` Engels (met hreflang). Bezoekers op `/` met een niet-Nederlandse browser
gaan automatisch naar `/en/`; zoekmachines en AI-bots nooit (die zien beide versies via de links/sitemap).
Een keuze via het menu of `?lang=nl|en` wordt onthouden.

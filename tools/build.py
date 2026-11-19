#!/usr/bin/env python3
"""Bouwt de SEO-onderdelen van anoukphilipsen.com uit index.html (de Nederlandse bron).

Draai na ELKE wijziging aan index.html:

    python3 tools/build.py

Het script
  1. zet de structured data (JSON-LD) in index.html opnieuw neer,
  2. maakt en/index.html: een volledig Engelse, statische kopie (vertaald met het
     woordenboek EN{} en PATTERNS uit het script in index.html),
  3. schrijft sitemap.xml (met hreflang en alle schilderijen als afbeeldingen),
  4. waarschuwt voor Nederlandse tekst die nog geen Engelse vertaling in EN{} heeft.

Alleen de standaardbibliotheek; geen installatie nodig.
"""
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://anoukphilipsen.com"
EMAIL = "Anoukphilipsenart@gmail.com"
LD_RE = re.compile(r'<script type="application/ld\+json" id="ld">.*?</script>|<!--ld-->', re.S)
RAW_RE = re.compile(r"(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->)", re.S | re.I)


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def one(text, old, new):
    """Vervang precies één keer; anders stoppen (structuur gewijzigd)."""
    n = text.count(old)
    if n != 1:
        sys.exit(f"build.py: verwacht precies 1x {old[:70]!r}, gevonden {n}x")
    return text.replace(old, new)


# ---------- vertaling (zelfde logica als tr() in de pagina) ----------
def load_dictionary(src):
    block = re.search(r"const EN=\{(.*?)\};", src, re.S).group(1)
    pairs = re.findall(r"'((?:[^'\\]|\\.)*)'\s*:\s*'((?:[^'\\]|\\.)*)'", block)
    en = {k.replace("\\'", "'"): v.replace("\\'", "'") for k, v in pairs}
    pats = []
    block = re.search(r"const PATTERNS=\[(.*?)\];\n", src, re.S).group(1)
    for rx, rp in re.findall(r"\[/(.*?)/,'(.*?)'\]", block):
        pats.append((re.compile(rx), re.sub(r"\$(\d)", r"\\\1", rp)))
    return en, pats


def make_tr(en, pats, missing):
    def tr(text):
        m = re.match(r"^(\s*)([\s\S]*?)(\s*)$", text)
        core = m.group(2)
        if not core:
            return text
        out = en.get(core)
        if out is None:
            out = core
            for rx, rp in pats:
                if rx.search(core):
                    out = rx.sub(rp, core)
                    break
            else:
                missing.add(core)
        return m.group(1) + out + m.group(3)
    return tr


def translate_html(doc, tr):
    def text_part(part):
        part = re.sub(r">([^<]+)<", lambda m: ">" + html.escape(tr(html.unescape(m.group(1))), quote=False) + "<", part)
        part = re.sub(r'(\s(?:alt|aria-label)=")([^"]*)(")',
                      lambda m: m.group(1) + html.escape(tr(html.unescape(m.group(2)))) + m.group(3), part)
        part = re.sub(r'(<meta (?:name="description"|property="og:(?:title|description|image:alt)") content=")([^"]*)(")',
                      lambda m: m.group(1) + html.escape(tr(html.unescape(m.group(2)))) + m.group(3), part)
        return part
    pieces = RAW_RE.split(doc)
    return "".join(p if RAW_RE.fullmatch(p) else text_part(p) for p in pieces)


# ---------- gegevens uit de pagina ----------
def artworks(src):
    works = []
    for art in re.findall(r'<article class="work[^"]*".*?</article>', src, re.S):
        img = re.search(r"<img\b[^>]*>", art).group(0)
        attr = dict(re.findall(r'([\w-]+)="([^"]*)"', img))
        works.append({
            "name": re.search(r'class="work-name">([^<]+)<', art).group(1),
            "src": attr["src"], "alt": html.unescape(attr["alt"]),
            "width": int(attr["width"]), "height": int(attr["height"]),
        })
    return works


def meta(src, key):
    m = re.search(r'<meta (?:name|property)="%s" content="([^"]*)"' % re.escape(key), src)
    return html.unescape(m.group(1))


def json_ld(src, lang, tr):
    url = BASE + ("/en/" if lang == "en" else "/")
    person_id, site_id = BASE + "/#anouk", BASE + "/#website"
    works = artworks(src)
    title = tr(html.unescape(re.search(r"<title>(.*?)</title>", src).group(1)))
    desc = tr(meta(src, "description"))
    graph = [
        {"@type": "WebSite", "@id": site_id, "url": BASE + "/", "name": "Anouk Philipsen",
         "inLanguage": ["nl", "en"], "publisher": {"@id": person_id}},
        {"@type": "Person", "@id": person_id, "name": "Anouk Philipsen", "url": BASE + "/",
         "jobTitle": "Artist" if lang == "en" else "Kunstenaar",
         "description": tr("Abstracte schilderijen waarin kleur, vorm en beweging samenkomen."),
         "email": "mailto:" + EMAIL, "image": BASE + works[0]["src"],
         "knowsAbout": ["Abstract art", "Painting"] if lang == "en" else ["Abstracte kunst", "Schilderkunst"]},
        {"@type": "CollectionPage", "@id": url + "#webpage", "url": url, "name": title,
         "description": desc, "inLanguage": lang, "isPartOf": {"@id": site_id},
         "about": {"@id": person_id}, "primaryImageOfPage": {"@id": BASE + works[0]["src"]},
         "hasPart": [{"@id": url + "#werk-%02d" % (i + 1)} for i in range(len(works))]},
    ]
    for i, w in enumerate(works):
        graph.append({
            "@type": "VisualArtwork", "@id": url + "#werk-%02d" % (i + 1), "name": tr(w["name"]),
            "artform": "Painting" if lang == "en" else "Schilderij", "description": tr(w["alt"]),
            "creator": {"@id": person_id}, "url": url + "#werk",
            "image": {"@type": "ImageObject", "@id": BASE + w["src"], "contentUrl": BASE + w["src"],
                      "url": BASE + w["src"], "width": w["width"], "height": w["height"],
                      "caption": tr(w["alt"]), "creator": {"@id": person_id},
                      "creditText": "Anouk Philipsen", "copyrightNotice": "© Anouk Philipsen",
                      "license": BASE + "/rechten/", "acquireLicensePage": url + "#contact"},
        })
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    return '<script type="application/ld+json" id="ld">' + data.replace("</", "<\\/") + "</script>"


# ---------- Engelse pagina ----------
def english(src, tr):
    doc = translate_html(src, tr)
    doc = one(doc, '<html lang="nl" data-page="nl" data-lang="nl">', '<html lang="en" data-page="en" data-lang="en">')
    doc = one(doc, '<link rel="canonical" href="https://anoukphilipsen.com/">', '<link rel="canonical" href="https://anoukphilipsen.com/en/">')
    doc = one(doc, '<meta property="og:url" content="https://anoukphilipsen.com/">', '<meta property="og:url" content="https://anoukphilipsen.com/en/">')
    doc = one(doc, '<meta property="og:locale" content="nl_NL"><meta property="og:locale:alternate" content="en_GB">',
              '<meta property="og:locale" content="en_GB"><meta property="og:locale:alternate" content="nl_NL">')
    doc = one(doc, 'data-lang="nl" aria-current="true">Nederlands</a><a href="/en/" hreflang="en" lang="en" data-lang="en">English</a>',
              'data-lang="nl">Nederlands</a><a href="/en/" hreflang="en" lang="en" data-lang="en" aria-current="true">English</a>')
    doc = one(doc, '<a class="footer-lang" href="/en/" hreflang="en" lang="en" data-lang="en">English</a>',
              '<a class="footer-lang" href="/" hreflang="nl" lang="nl" data-lang="nl">Nederlands</a>')
    return doc


def sitemap(src):
    today = datetime.date.today().isoformat()
    imgs = "".join(
        "<image:image><image:loc>%s%s</image:loc></image:image>" % (BASE, w["src"]) for w in artworks(src))
    alts = ('<xhtml:link rel="alternate" hreflang="nl" href="%s/"/>'
            '<xhtml:link rel="alternate" hreflang="en" href="%s/en/"/>'
            '<xhtml:link rel="alternate" hreflang="x-default" href="%s/"/>') % (BASE, BASE, BASE)
    urls = "".join("\n  <url><loc>%s</loc><lastmod>%s</lastmod>%s%s</url>" % (BASE + p, today, alts, imgs)
                   for p in ("/", "/en/"))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            + urls + "\n</urlset>\n")


# Teksten die in beide talen hetzelfde mogen blijven (namen, adressen, cijfers).
SAME = {"Anouk Philipsen", "Menu", "Nederlands", "English", "Gallery Rembrandt", "Kleine Berg 42",
        "5611 JV Eindhoven", "www.galleryrembrandt.nl", "My Art at Gallery Rembrandt", EMAIL,
        "Anouk Philipsen.", "Contact", "04 / Contact", "Mail Anouk"}


def main():
    src = read("index.html")
    en, pats = load_dictionary(src)
    missing = set()
    tr_nl = lambda t: t
    src = LD_RE.sub(lambda m: json_ld(src, "nl", tr_nl), src, count=1)
    write("index.html", src)
    tr_en = make_tr(en, pats, missing)
    page_en = english(src, tr_en)
    page_en = LD_RE.sub(lambda m: json_ld(src, "en", tr_en), page_en, count=1)
    write("en/index.html", page_en)
    write("sitemap.xml", sitemap(src))
    todo = sorted(t for t in missing if t not in SAME and re.search(r"[A-Za-zÀ-ÿ]{2}", t)
                  and not re.fullmatch(r"[\d\s/.·]+", t))
    print("index.html, en/index.html en sitemap.xml bijgewerkt (%d werken)." % len(artworks(src)))
    if todo:
        print("\nLET OP: deze teksten hebben nog geen Engelse vertaling in EN{} (index.html):")
        for t in todo:
            print("  -", t)


if __name__ == "__main__":
    main()

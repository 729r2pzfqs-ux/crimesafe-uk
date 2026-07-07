#!/usr/bin/env python3
"""
Site-wide CTR/SEO fixes:
1. Add hreflang (en + x-default) alternates next to every canonical tag.
2. Fix city FAQPage schema using "Crime in X" as the area name.
3. Rewrite thin homepage + district meta descriptions.
4. Add BreadcrumbList schema (parsed from the visible breadcrumb) to
   city / district / neighbourhood / postcode pages.

Skips redirect stubs (meta refresh) and noindex pages.
"""
import html as html_mod
import json
import os
import re

CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]+)">')
CRUMB_RE = re.compile(r'<div class="breadcrumb">\s*(.*?)\s*</div>', re.S)
CRUMB_LINK_RE = re.compile(r'<a href="([^"]+)">([^<]+)</a>')

stats = {"hreflang": 0, "breadcrumb": 0, "cityfaq": 0, "desc": 0, "skipped": 0}


def hreflang_tags(canonical, pretty):
    sep = "\n    " if pretty else ""
    return (
        f'{sep}<link rel="alternate" hreflang="en" href="{canonical}">'
        f'{sep}<link rel="alternate" hreflang="x-default" href="{canonical}">'
    )


def json_ld(obj):
    # Escape "</" so the payload can never terminate the script tag.
    return json.dumps(obj).replace("</", "<\\/")


def build_breadcrumb_schema(html):
    """Parse the visible breadcrumb into BreadcrumbList JSON-LD."""
    m = CRUMB_RE.search(html)
    if not m:
        return None
    block = m.group(1)
    links = CRUMB_LINK_RE.findall(block)
    if not links:
        return None
    # Trailing plain-text segment after the last › is the current page.
    tail = re.sub(r"<[^>]+>", "", block.rsplit("</a>", 1)[-1])
    tail = tail.replace("›", " ").strip()
    items = []
    for pos, (href, name) in enumerate(links, 1):
        url = "https://crimesafe.uk" + href if href.startswith("/") else href
        items.append(
            {
                "@type": "ListItem",
                "position": pos,
                "name": html_mod.unescape(name.strip()),
                "item": url,
            }
        )
    if tail:
        items.append(
            {
                "@type": "ListItem",
                "position": len(items) + 1,
                "name": html_mod.unescape(tail),
            }
        )
    if len(items) < 2:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def replace_descriptions(html, new_desc):
    """Swap meta/og/twitter/JSON-LD descriptions for new_desc."""
    old = re.search(r'<meta name="description" content="([^"]*)"', html)
    if not old:
        return html
    old_desc = old.group(1)
    html = html.replace(f'content="{old_desc}"', f'content="{new_desc}"')
    html = html.replace(
        f'"description":"{old_desc}"', f'"description":"{new_desc}"'
    )
    return html


def process(path, add_crumbs=False, city_fix=False, new_desc=None):
    with open(path, encoding="utf-8", errors="ignore") as f:
        html = f.read()

    if 'http-equiv="refresh"' in html or 'content="noindex' in html:
        stats["skipped"] += 1
        return

    orig = html
    m = CANONICAL_RE.search(html)

    if m and "hreflang" not in html:
        canonical_tag = m.group(0)
        pretty = html[m.end() : m.end() + 1] == "\n"
        html = html.replace(
            canonical_tag, canonical_tag + hreflang_tags(m.group(1), pretty), 1
        )
        stats["hreflang"] += 1

    if city_fix and '"Is Crime in ' in html:
        # Only rewrite inside the FAQPage JSON-LD payload.
        def fix_script(sm):
            return sm.group(0).replace("Crime in ", "")

        html = re.sub(
            r'<script type="application/ld\+json">[^<]*"@type": "FAQPage".*?</script>',
            fix_script,
            html,
            flags=re.S,
        )
        stats["cityfaq"] += 1

    if new_desc:
        html = replace_descriptions(html, new_desc)
        stats["desc"] += 1

    if add_crumbs and "BreadcrumbList" not in html:
        schema = build_breadcrumb_schema(html)
        if schema:
            tag = f'<script type="application/ld+json">{json_ld(schema)}</script>'
            html = html.replace("</head>", tag + "\n</head>", 1)
            stats["breadcrumb"] += 1

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)


def walk_pages(base):
    for root, _dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".html"):
                yield os.path.join(root, name)


def main():
    # Homepage
    home_desc = (
        "UK crime statistics and safety scores for 4,900+ neighbourhoods, "
        "postcodes and every police force. Check how safe your area is with "
        "monthly police.uk data."
    )
    process("index.html", new_desc=home_desc)

    # City pages: FAQ name fix + breadcrumbs
    for page in walk_pages("city"):
        process(page, add_crumbs=True, city_fix=True)

    # District pages: richer descriptions + breadcrumbs
    for page in walk_pages("district"):
        new_desc = None
        with open(page, encoding="utf-8", errors="ignore") as f:
            head = f.read(4000)
        dm = re.search(
            r'content="Crime statistics for (.+?) district in (.+?)\. '
            r'(\d+) neighbourhoods covered\."',
            head,
        )
        if dm:
            name, force, count = dm.groups()
            new_desc = (
                f"{name} crime statistics: safety scores for {count} police "
                f"neighbourhoods in {force}. See the safest areas and monthly "
                f"crime trends from police.uk."
            )
        process(page, add_crumbs=True, new_desc=new_desc)

    # Breadcrumb + hreflang page types
    for base in ("neighbourhood", "postcode", "districts"):
        for page in walk_pages(base):
            process(page, add_crumbs=True)

    # hreflang-only page types
    for base in (
        "about", "blog", "dangerous", "embed", "faq", "forces", "maps",
        "privacy", "safest", "streets", "terms",
    ):
        for page in walk_pages(base):
            process(page)

    # Compare pages last (274k files)
    n = 0
    for d in sorted(os.listdir("compare")):
        p = os.path.join("compare", d, "index.html")
        if os.path.isfile(p):
            process(p)
        n += 1
        if n % 50000 == 0:
            print(f"  compare {n} ({stats['hreflang']} hreflang)", flush=True)
    p = "compare/index.html"
    if os.path.isfile(p):
        process(p)

    print(stats)


if __name__ == "__main__":
    main()

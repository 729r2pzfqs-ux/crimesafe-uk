#!/usr/bin/env python3
"""
Add FAQPage schema to all CrimeSafe UK pages.
Compare pages already have Q&A content — just need schema wrapper.
"""
import html as html_mod
import os, re, json

count = 0
errors = 0

def extract_compare_faqs(html):
    """Extract existing Q&A pairs from compare pages"""
    faqs = []
    # Pattern: <div font-weight: 600>Question</div> <div color: muted>Answer</div>
    blocks = re.findall(
        r'<div style="font-weight: 600[^"]*">([^<]+)</div>\s*<div style="color: var\(--muted\)">([^<]+(?:<[^/][^<]*>[^<]*</[^<]*>)*[^<]*)</div>',
        html, re.DOTALL
    )
    if not blocks:
        # Try simpler pattern
        blocks = re.findall(
            r'<div style="font-weight: 600;[^"]*">([^<]+)</div>\s*\n\s*<div style="color: var\(--muted\);">\s*\n?\s*([^<]+(?:\n[^<]+)*?)\s*</div>',
            html
        )
    
    for q, a in blocks:
        q = q.strip()
        a = re.sub(r'<[^>]+>', '', a).strip()
        a = re.sub(r'\s+', ' ', a)
        if q and a and len(a) > 20:
            faqs.append((q, a))
    
    return faqs

def extract_city_faqs(html):
    """Build FAQs from city page content"""
    city_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    city = city_match.group(1).strip() if city_match else "this city"
    city = re.sub(r'^Crime in ', '', city)
    
    score_match = re.search(r'average safety score of <strong>(\d+)/100</strong>', html)
    score = score_match.group(1) if score_match else "N/A"
    
    faqs = [
        (f"Is {city} safe?",
         f"{city} has an average safety score of {score}/100. Scores are based on official police.uk crime data across all neighbourhoods. Individual areas within {city} may vary significantly."),
        (f"How is the {city} safety score calculated?",
         f"Safety scores combine violent crime, property crime, and anti-social behaviour data from police.uk. Each neighbourhood is ranked against all UK neighbourhoods, with 100 being safest."),
        (f"What is the safest area in {city}?",
         f"Check individual neighbourhood scores within {city} for the safest areas. Scores update monthly with new police data."),
    ]
    return faqs

def extract_postcode_faqs(html):
    """Build FAQs from postcode page content"""
    pc_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    title = pc_match.group(1).strip() if pc_match else "this postcode"
    
    pc_code = re.search(r'([A-Z]{1,2}\d{1,2})', title)
    code = pc_code.group(1) if pc_code else ""
    
    faqs = [
        (f"Is {code} a safe area?",
         f"Check the safety scores for neighbourhoods within the {code} postcode area. Scores are based on official police.uk data and range from 0-100, with 100 being the safest."),
        (f"What crimes are most common in {code}?",
         f"Crime data for {code} comes from police.uk and includes violent crime, property crime, anti-social behaviour, and other categories. Check the breakdown above for specific figures."),
    ]
    return faqs

def unescape_text(text):
    """Decode HTML entities (incl. double-escaped ones like &amp;amp;) to plain text"""
    for _ in range(3):
        decoded = html_mod.unescape(text)
        if decoded == text:
            break
        text = decoded
    return text

def inject_schema(filepath, faqs):
    """Add FAQPage schema to a page"""
    global count, errors

    with open(filepath, "r") as f:
        html = f.read()

    if "FAQPage" in html:
        return

    if not faqs:
        errors += 1
        return

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": unescape_text(q),
             "acceptedAnswer": {"@type": "Answer", "text": unescape_text(a)}}
            for q, a in faqs
        ]
    }

    # Escape "</" as "<\/" (still valid JSON) so the payload can never contain
    # "</script>"/"</head>" sequences that break the script tag or get mangled
    # by later tag-based text replacements over the file.
    payload = json.dumps(schema).replace('</', '<\\/')
    tag = f'<script type="application/ld+json">{payload}</script>'
    html = html.replace('</head>', tag + '\n</head>', 1)

    # Unenriched pages carry a thin-content noindex; enrichment makes the
    # page index-worthy again, so drop it.
    html = html.replace('\n    <meta name="robots" content="noindex, follow">', '', 1)

    with open(filepath, "w") as f:
        f.write(html)
    count += 1

# 1. Compare pages (262,635)
print("⚔️ Compare pages...")
compare_dir = "compare"
dirs = sorted(os.listdir(compare_dir))
total = len(dirs)
for i, d in enumerate(dirs):
    p = os.path.join(compare_dir, d, "index.html")
    if os.path.isfile(p):
        with open(p) as f:
            html = f.read()
        faqs = extract_compare_faqs(html)
        if not faqs:
            # Fallback: extract city names and build generic FAQs
            cities = re.findall(r'<h2[^>]*>([^<]+)</h2>', html)
            scores = re.findall(r'font-size: 2rem[^>]*>(\d+)<|font-weight: 700[^>]*>(\d+)<', html)
            if len(cities) >= 2:
                a, b = cities[0].strip(), cities[1].strip()
                faqs = [
                    (f"Is {a} or {b} safer?",
                     f"Compare safety scores and crime rates for {a} and {b} based on official police.uk data above."),
                    (f"How are safety scores calculated?",
                     f"Scores range from 0-100 based on violent crime, property crime, and anti-social behaviour from police.uk. Higher scores mean safer areas."),
                ]
        inject_schema(p, faqs)
    if (i + 1) % 20000 == 0:
        print(f"  ... {i+1}/{total} ({count} done)")

print(f"  ✅ Compare: {count} enriched ({errors} errors)")

# 2. City pages (38)
city_before = count
print("\n🏙️ City pages...")
if os.path.isdir("city"):
    for d in sorted(os.listdir("city")):
        p = f"city/{d}/index.html"
        if os.path.isfile(p):
            with open(p) as f:
                html = f.read()
            faqs = extract_city_faqs(html)
            inject_schema(p, faqs)
print(f"  ✅ City: {count - city_before} enriched")

# 3. Postcode pages (2,830)
pc_before = count
print("\n📮 Postcode pages...")
if os.path.isdir("postcode"):
    for d in sorted(os.listdir("postcode")):
        p = f"postcode/{d}/index.html"
        if os.path.isfile(p):
            with open(p) as f:
                html = f.read()
            faqs = extract_postcode_faqs(html)
            inject_schema(p, faqs)
print(f"  ✅ Postcode: {count - pc_before} enriched")

# 4. Neighbourhood pages (4,909) — inside force dirs
nb_before = count  
print("\n🏘️ Neighbourhood pages...")
if os.path.isdir("neighbourhood"):
    for force in sorted(os.listdir("neighbourhood")):
        force_dir = f"neighbourhood/{force}"
        if not os.path.isdir(force_dir):
            continue
        for nb in os.listdir(force_dir):
            p = f"{force_dir}/{nb}/index.html"
            if os.path.isfile(p):
                with open(p) as f:
                    html = f.read()
                name = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                n = name.group(1).strip() if name else nb
                faqs = [
                    (f"Is {n} safe?",
                     f"Check the safety score for {n} above. Scores are based on police.uk crime data and range from 0-100."),
                    (f"What crimes happen in {n}?",
                     f"Crime data includes violent crime, burglary, anti-social behaviour, and other categories from police.uk."),
                ]
                inject_schema(p, faqs)
print(f"  ✅ Neighbourhood: {count - nb_before} enriched")

print(f"\n✅ TOTAL: {count} pages enriched ({errors} errors)")

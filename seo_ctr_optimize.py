#!/usr/bin/env python3
"""
CTR optimisation pass for crimesafe.uk.

Rewrites <title>, meta description, and OG/Twitter tags with:
  - Query-first titles (specific data, ≤65 chars)
  - Concrete numbers in descriptions (120-160 chars)
  - FAQPage JSON-LD on pages that lack it

Page types handled:
  index.html                          homepage
  forces/index.html                   forces index
  districts/index.html                districts index
  safest/index.html                   safest rankings
  dangerous/index.html                dangerous rankings
  force/{slug}/index.html             44 force pages
  district/{slug}/index.html          65 district pages
  neighbourhood/{f}/{nb}/index.html   4,926 neighbourhood pages
  city/{slug}/index.html              city pages
  postcode/{code}/index.html          postcode pages
"""

import html as html_mod
import json
import os
import re

DATA_DIR = "data"

TITLE_RE    = re.compile(r'<title>(.*?)</title>', re.DOTALL)
DESC_RE     = re.compile(r'(<meta name="description" content=")[^"]*(">)')
OG_TITLE_RE = re.compile(r'(<meta property="og:title" content=")[^"]*(">)')
OG_DESC_RE  = re.compile(r'(<meta property="og:description" content=")[^"]*(">)')
TW_TITLE_RE = re.compile(r'(<meta name="twitter:title" content=")[^"]*(">)')
TW_DESC_RE  = re.compile(r'(<meta name="twitter:description" content=")[^"]*(">)')
FAQ_RE      = re.compile(r'"@type"\s*:\s*"FAQPage"')
HEAD_CLOSE  = re.compile(r'(</head>)')
NB_LINK_RE  = re.compile(r'/neighbourhood/([^/]+)/([^/]+)/')

stats = {"modified": 0, "skipped": 0, "unchanged": 0, "errors": 0}


def slugify(text):
    text = text.lower()
    text = re.sub(r'&(?:amp;)+', ' and ', text)
    text = re.sub(r'&(?![a-z]+;)', ' and ', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    slug = text.strip('-')
    if slug == 'devon-and-cornwall-police':
        slug = 'devon-cornwall-police'
    return slug


def grade_label(score):
    if score >= 80: return "Very Safe"
    if score >= 60: return "Safe"
    if score >= 40: return "Average"
    if score >= 20: return "Below Average"
    return "High Crime"


def shortest(candidates, limit=65):
    for t in candidates:
        if len(t) <= limit:
            return t
    return candidates[-1][:limit]


def rewrite_meta(content, new_title, new_desc):
    et = html_mod.escape(new_title)
    ed = html_mod.escape(new_desc)
    content = TITLE_RE.sub(f'<title>{et}</title>', content)
    content = DESC_RE.sub(lambda m: m.group(1) + ed + m.group(2), content)
    content = OG_TITLE_RE.sub(lambda m: m.group(1) + et + m.group(2), content)
    content = OG_DESC_RE.sub(lambda m: m.group(1) + ed + m.group(2), content)
    content = TW_TITLE_RE.sub(lambda m: m.group(1) + et + m.group(2), content)
    content = TW_DESC_RE.sub(lambda m: m.group(1) + ed + m.group(2), content)
    return content


def inject_faq(content, faq_obj):
    if FAQ_RE.search(content):
        return content
    ld = json.dumps(faq_obj, ensure_ascii=False, separators=(',', ':'))
    ld = ld.replace('</', '<\\/')
    tag = f'    <script type="application/ld+json">{ld}</script>\n'
    return HEAD_CLOSE.sub(tag + r'\1', content, count=1)


def make_faq(*qa_pairs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in qa_pairs
        ],
    }


def normalise_slug(slug):
    """Canonical slug form: collapse repeated dashes, convert -amp[amp]- to -and-."""
    s = re.sub(r'-+', '-', slug)
    s = re.sub(r'-amp(?:amp)?-', '-and-', s)
    return s


def load_data():
    with open(f"{DATA_DIR}/rankings.json") as f:
        rankings = json.load(f)
    nb_lookup = {}
    score_lookup = {}
    for r in rankings:
        for slug in {r['nb_slug'], normalise_slug(r['nb_slug'])}:
            key = f"{r['force_slug']}_{slug}"
            nb_lookup[key] = r
            score_lookup[(r['force_slug'], slug)] = r['score']
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_raw = json.load(f)
    forces_by_slug = {slugify(f['name']): f for f in forces_raw['forces']}
    with open(f"{DATA_DIR}/districts.json") as f:
        districts_raw = json.load(f)
    districts_by_slug = {slugify(d['district']): d for d in districts_raw}
    return nb_lookup, score_lookup, forces_by_slug, districts_by_slug


def postcode_avg_score(content, score_lookup):
    pairs = NB_LINK_RE.findall(content)
    scores = []
    for f_slug, nb_slug in pairs:
        s = score_lookup.get((f_slug, normalise_slug(nb_slug)))
        if s is not None:
            scores.append(s)
    return round(sum(scores) / len(scores)) if scores else None


def compute_page(relpath, content, nb_lookup, score_lookup, forces_by_slug, districts_by_slug):
    """Return (title, desc, faq_or_None) for relpath, or (None, None, None) to skip."""
    parts = relpath.split('/')

    # ── Homepage ──────────────────────────────────────────────────────────────
    if relpath == 'index.html':
        return (
            "Check UK Crime Rates 2026 | 4,926 Areas Scored",
            ("Find out if your area is safe. Crime scores for 4,926 UK "
             "neighbourhoods, 44 police forces and 2,800+ postcodes. "
             "Updated monthly from official police.uk data."),
            make_faq(
                ("How do I find crime statistics for my area?",
                 "Search by neighbourhood name or police force on CrimeSafe UK. "
                 "Every area gets a safety score 0–100 based on official monthly "
                 "crime data from police.uk."),
                ("How is the crime safety score calculated?",
                 "Scores (0–100) are percentile-ranked across all 4,926 UK "
                 "neighbourhoods by crime rate per 1,000 residents. "
                 "Score 100 = lowest crime rate; score 0 = highest."),
                ("How up to date is the crime data?",
                 "Crime data is updated monthly from data.police.uk, the official "
                 "UK police crime statistics portal. Current data covers May 2026."),
            ),
        )

    # ── Forces index ──────────────────────────────────────────────────────────
    if relpath == 'forces/index.html':
        return (
            "44 UK Police Forces | Crime Statistics 2026",
            ("Browse crime statistics for all 44 UK police forces. Compare "
             "safety scores across 4,926 neighbourhoods in England, Wales, "
             "and Northern Ireland."),
            None,
        )

    # ── Districts index ───────────────────────────────────────────────────────
    if relpath == 'districts/index.html':
        return (
            "UK District Crime Statistics 2026 | 65 Areas",
            ("Browse crime rates and safety scores for 65 UK districts. "
             "Compare neighbourhoods by area using official May 2026 police "
             "data from police.uk."),
            None,
        )

    # ── Safest rankings ───────────────────────────────────────────────────────
    if relpath == 'safest/index.html':
        return (
            "100 Safest Places to Live in the UK 2026",
            ("The 100 safest places to live in the UK, ranked by crime rate. "
             "Areas scored 80–100/100 based on official May 2026 "
             "data from police.uk."),
            make_faq(
                ("What is the safest place to live in the UK?",
                 "The safest neighbourhoods score 80–100/100 based on crime rate "
                 "per 1,000 residents. These areas have the fewest recorded crimes "
                 "according to May 2026 official data from police.uk."),
                ("How is the safety score calculated?",
                 "Scores (0–100) are percentile-ranked across all 4,926 UK "
                 "neighbourhoods by crime rate per 1,000 residents. "
                 "A score of 100 means the lowest crime rate nationally."),
                ("How often is crime data updated?",
                 "Data is updated monthly from data.police.uk. "
                 "These rankings reflect May 2026 reported crimes."),
            ),
        )

    # ── Dangerous rankings ────────────────────────────────────────────────────
    if relpath == 'dangerous/index.html':
        return (
            "100 Highest Crime Areas in the UK 2026",
            ("The 100 highest-crime neighbourhoods in the UK, ranked by crime "
             "rate. Areas scored 0–20/100 based on official May 2026 "
             "data from police.uk."),
            make_faq(
                ("Which are the most dangerous areas in the UK?",
                 "The highest-crime neighbourhoods score 0–20/100 based on crime "
                 "rate per 1,000 residents using May 2026 data from police.uk. "
                 "Urban city centres typically appear at the top of this list."),
                ("How is the crime ranking calculated?",
                 "Rankings use crime rate per 1,000 residents, percentile-ranked "
                 "across all 4,926 UK neighbourhoods. "
                 "A lower score means a higher crime rate."),
                ("How often is crime data updated?",
                 "Data is updated monthly from data.police.uk. "
                 "These rankings reflect May 2026 reported crimes."),
            ),
        )

    # ── Force page: force/{slug}/index.html ───────────────────────────────────
    if len(parts) == 3 and parts[0] == 'force' and parts[2] == 'index.html':
        force = forces_by_slug.get(parts[1])
        if not force:
            return None, None, None
        fname  = force['name']
        ncount = len(force['neighbourhoods'])
        title = shortest([
            f"{fname} Crime Statistics 2026 | {ncount} Areas",
            f"{fname} Crime Stats | {ncount} Areas",
            f"{fname} Crime Statistics 2026",
        ])
        desc = (
            f"Crime stats for {ncount} neighbourhoods in {fname}. "
            f"Safety scores 0–100 by crime rate — updated monthly "
            f"from official police.uk data."
        )
        faq = make_faq(
            (f"Is {fname} safe?",
             f"{fname} covers {ncount} neighbourhoods with varying crime rates. "
             f"Safety scores range from 0 (highest crime) to 100 (lowest crime). "
             f"Search above to compare each area."),
            (f"Which is the safest neighbourhood in {fname}?",
             f"Crime rates vary across {ncount} neighbourhoods in {fname}. "
             f"Browse the full list above, sorted by safety score, to find the "
             f"lowest-crime areas."),
            ("How is the safety score calculated?",
             "Scores (0–100) are percentile-ranked across all 4,926 UK "
             "neighbourhoods by crime rate per 1,000 residents, "
             "using official monthly data from police.uk."),
        )
        return title, desc, faq

    # ── District page: district/{slug}/index.html ─────────────────────────────
    if len(parts) == 3 and parts[0] == 'district' and parts[2] == 'index.html':
        district = districts_by_slug.get(parts[1])
        if not district:
            return None, None, None
        dname   = district['district'].title()
        fname   = district['force']
        ncount  = district['neighbourhood_count']
        nb_word = "neighbourhood" if ncount == 1 else "neighbourhoods"
        title = shortest([
            f"{dname} Crime Rate 2026 | {ncount} {nb_word.title()} Ranked",
            f"{dname} Crime Rate 2026 | {ncount} Areas",
            f"{dname} Crime Statistics 2026",
        ])
        _desc_long = (
            f"Crime rates and safety scores for {ncount} {nb_word} in "
            f"{dname}, {fname}. Ranked 0–100 by crime rate using official "
            f"May 2026 police data."
        )
        _desc_short = (
            f"Crime rates and safety scores for {ncount} {nb_word} in "
            f"{dname}. Ranked 0–100 by crime rate using official "
            f"May 2026 police data."
        )
        desc = _desc_long if len(html_mod.escape(_desc_long)) <= 160 else _desc_short
        faq = make_faq(
            (f"Is {dname} a safe area?",
             f"{dname} in {fname} has {ncount} {nb_word} with varying crime rates. "
             f"Safety scores (0–100) are based on official May 2026 police.uk data."),
            (f"What is the crime rate in {dname}?",
             f"Crime rates in {dname} vary by neighbourhood. "
             f"See safety scores above, based on May 2026 police.uk data."),
            (f"Which is the safest neighbourhood in {dname}?",
             f"Browse all {ncount} {nb_word} above, ranked by safety score (0–100), "
             f"to find the lowest-crime areas in {dname}."),
        )
        return title, desc, faq

    # ── Neighbourhood: neighbourhood/{force}/{nb}/index.html ──────────────────
    if len(parts) == 4 and parts[0] == 'neighbourhood' and parts[3] == 'index.html':
        key = f"{parts[1]}_{normalise_slug(parts[2])}"
        r = nb_lookup.get(key)
        if not r:
            return None, None, None
        name  = r['name']
        score = r['score']
        total = r.get('total_crimes', 0) or 0
        grade = grade_label(score)
        _name_short = name[:38].rsplit(' ', 1)[0] if len(name) > 40 else name
        title = shortest([
            f"Is {name} Safe? Score {score}/100 — {total:,} Crimes",
            f"Is {name} Safe? Crime Score {score}/100 (2026)",
            f"{name} Safety Score {score}/100 | 2026",
            f"{_name_short}... Crime Score {score}/100",
        ])
        _desc_full = (
            f"Is {name} safe? Crime score: {score}/100 ({grade}). "
            f"{total:,} offences in May 2026. "
            f"View crime breakdown by type and compare with nearby areas."
        )
        _desc_short = (
            f"Is {name} safe? Crime score: {score}/100 ({grade}). "
            f"{total:,} offences in May 2026."
        )
        desc = _desc_full if len(html_mod.escape(_desc_full)) <= 160 else _desc_short
        # Neighbourhood pages already have FAQPage schema
        return title, desc, None

    # ── City page: city/{slug}/index.html ─────────────────────────────────────
    if len(parts) == 3 and parts[0] == 'city' and parts[2] == 'index.html':
        cslug     = parts[1]
        city_name = cslug.replace('-', ' ').title()
        # Extract stats from existing meta description or title
        existing  = re.search(r'<meta name="description" content="([^"]*)"', content)
        edesc     = existing.group(1) if existing else ''
        # Support both old ("Average Safety Score:") and new ("Average crime score:") formats
        score_m   = re.search(r'Average (?:Safety |crime )score:? (\d+)/100', edesc, re.IGNORECASE)
        # Also try the title (new format: "Avg Score Y/100")
        if not score_m:
            score_m = re.search(r'Avg Score (\d+)/100', content)
        if not score_m:
            return None, None, None
        total_m   = re.search(r'View ([\d,]+) crimes reported', edesc)
        area_m    = re.search(r'across (\d+) (?:areas|neighbourhoods)', edesc)
        avg_score  = int(score_m.group(1))
        total_str  = total_m.group(1) if total_m else "?"
        area_count = area_m.group(1) if area_m else "?"
        grade      = grade_label(avg_score)
        title = shortest([
            f"Is {city_name} Safe? Avg Score {avg_score}/100 | Crime 2026",
            f"Is {city_name} Safe? Crime Score {avg_score}/100",
            f"{city_name} Crime Rate 2026 | Score {avg_score}/100",
        ])
        _desc_city = (
            f"Is {city_name} safe? Average crime score: {avg_score}/100 ({grade}) "
            f"across {area_count} neighbourhoods — {total_str} offences in May 2026. "
            f"Find the safest places in {city_name}."
        )
        _desc_city_short = (
            f"Is {city_name} safe? Average crime score: {avg_score}/100 ({grade}) "
            f"across {area_count} neighbourhoods — {total_str} offences in May 2026."
        )
        desc = _desc_city if len(html_mod.escape(_desc_city)) <= 160 else _desc_city_short
        # City pages already have FAQPage schema
        return title, desc, None

    # ── Postcode: postcode/{code}/index.html ──────────────────────────────────
    if len(parts) == 3 and parts[0] == 'postcode' and parts[2] == 'index.html':
        outcode = parts[1].upper()
        # Extract district names from existing meta description
        existing = re.search(r'<meta name="description" content="([^"]*)"', content)
        edesc = existing.group(1) if existing else ''
        dist_m = re.search(r'\(([^)]+)\)', edesc)
        if not dist_m:
            dist_m = re.search(r'Covers ([^.]+)', edesc)
        districts_str = dist_m.group(1).strip() if dist_m else outcode
        # Compute avg score from linked neighbourhood scores
        avg_score = postcode_avg_score(content, score_lookup)
        if avg_score is not None:
            grade = grade_label(avg_score)
            title = shortest([
                f"{outcode} Crime Stats 2026 | Safety Score {avg_score}/100",
                f"{outcode} Postcode Crime Stats | Score {avg_score}/100",
                f"{outcode} Postcode Crime Statistics 2026",
            ])
            _desc_pc_long = (
                f"Crime rates and safety scores for {outcode} postcode "
                f"({districts_str}). Average score: {avg_score}/100 ({grade}) "
                f"from nearby neighbourhood data — May 2026."
            )
            _desc_pc_short = (
                f"Crime stats for {outcode} postcode. "
                f"Average safety score: {avg_score}/100 ({grade}) "
                f"based on nearby neighbourhood data — May 2026."
            )
            desc = _desc_pc_long if len(html_mod.escape(_desc_pc_long)) <= 160 else _desc_pc_short
        else:
            title = shortest([
                f"{outcode} Postcode Crime Statistics 2026 | CrimeSafe UK",
                f"{outcode} Postcode Crime Stats 2026",
            ])
            if districts_str and districts_str != outcode:
                _desc_no_score = (
                    f"Crime stats for {outcode} postcode ({districts_str}). "
                    f"Browse nearby neighbourhood safety scores from "
                    f"May 2026 police.uk data."
                )
                _desc_no_score_short = (
                    f"Crime statistics for {outcode} postcode area. "
                    f"Browse nearby neighbourhood safety scores from "
                    f"official May 2026 police.uk data."
                )
                desc = _desc_no_score if len(html_mod.escape(_desc_no_score)) <= 160 else _desc_no_score_short
            else:
                desc = (
                    f"Crime statistics for {outcode} postcode area. "
                    f"Browse nearby neighbourhood safety scores from "
                    f"official May 2026 police.uk data."
                )
        return title, desc, None

    return None, None, None


def process_file(path, nb_lookup, score_lookup, forces_by_slug, districts_by_slug):
    relpath = os.path.relpath(path, '.').replace('\\', '/')
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"  ERROR reading {path}: {e}")
        stats['errors'] += 1
        return

    # Skip redirect stubs and noindex pages
    if 'http-equiv="refresh"' in content or 'content="noindex' in content:
        stats['skipped'] += 1
        return

    orig = content
    title, desc, faq_obj = compute_page(
        relpath, content, nb_lookup, score_lookup, forces_by_slug, districts_by_slug
    )

    if title and desc:
        content = rewrite_meta(content, title, desc)
    if faq_obj:
        content = inject_faq(content, faq_obj)

    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        stats['modified'] += 1
    else:
        stats['unchanged'] += 1


def main():
    print("Loading data...")
    nb_lookup, score_lookup, forces_by_slug, districts_by_slug = load_data()
    print(f"  {len(nb_lookup):,} neighbourhood scores")
    print(f"  {len(forces_by_slug)} forces")
    print(f"  {len(districts_by_slug)} districts")

    # Directories to walk (skip compare/ — 275k pages, generator-only update)
    sections = [
        '.',
        'forces',
        'districts',
        'safest',
        'dangerous',
        'force',
        'district',
        'neighbourhood',
        'city',
        'postcode',
    ]

    total = 0
    for section in sections:
        if section == '.':
            path = 'index.html'
            if os.path.exists(path):
                process_file(path, nb_lookup, score_lookup, forces_by_slug, districts_by_slug)
                total += 1
            continue
        if not os.path.isdir(section):
            continue
        for root, dirs, files in os.walk(section):
            dirs.sort()
            for fname in sorted(files):
                if not fname.endswith('.html'):
                    continue
                fpath = os.path.join(root, fname)
                process_file(fpath, nb_lookup, score_lookup, forces_by_slug, districts_by_slug)
                total += 1
                if total % 1000 == 0:
                    print(f"  {total:,} files processed…")

    print(f"\nDone. {total:,} files scanned.")
    print(f"  Modified:  {stats['modified']:,}")
    print(f"  Unchanged: {stats['unchanged']:,}")
    print(f"  Skipped:   {stats['skipped']:,}")
    print(f"  Errors:    {stats['errors']:,}")


if __name__ == '__main__':
    main()

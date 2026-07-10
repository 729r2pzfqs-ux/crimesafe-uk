#!/usr/bin/env python3
import os

TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-CK531DR9X9"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-CK531DR9X9');</script>
    <title>PCUPPER Crime Rate 2026 | CrimeSafe UK</title>
    <meta name="description" content="Crime statistics for PCUPPER postcode area in Scotland.">
    <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet" media="print" onload="this.media='all'"><noscript><link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet"></noscript>
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>
    <nav class="nav"><div class="nav-inner"><a href="/" class="nav-logo"><svg width="28" height="28" viewBox="0 0 512 512" fill="none"><path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="currentColor" opacity="0.1"/><path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="none" stroke="currentColor" stroke-width="20" stroke-linejoin="round"/><text x="256" y="320" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="160" fill="currentColor">UK</text></svg><span>CrimeSafe UK</span></a></div></nav>
    <main id="main-content"><div class="container" style="padding:3rem 1rem;max-width:700px;margin:0 auto;">
        <h1 style="font-size:2rem;margin-bottom:0.5rem;">PCUPPER Postcode Area</h1>
        <p style="color:var(--color-text-muted);margin-bottom:2rem;">Scotland, United Kingdom</p>
        <div style="background:#fef3c7;border:1px solid #f59e0b;border-radius:var(--radius);padding:1.5rem;margin-bottom:2rem;">
            <h2 style="font-size:1.1rem;margin-bottom:0.5rem;">Limited Data Coverage</h2>
            <p style="font-size:0.95rem;margin:0;">The PCUPPER postcode is in <strong>Scotland</strong>. Our crime data covers <strong>England and Wales</strong> only via police.uk.</p>
        </div>
        <div style="text-align:center;margin-top:2rem;">
            <a href="/" style="background:var(--color-primary);color:white;padding:0.75rem 1.5rem;border-radius:var(--radius);text-decoration:none;display:inline-block;">Search England & Wales</a>
        </div>
    </div></main>
    <footer class="footer"><div class="container"><p>&copy; 2026 CrimeSafe UK</p><p>Contains public sector information from <a href="https://data.police.uk">data.police.uk</a> licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/" rel="license">Open Government Licence v3.0</a>.</p></div></footer>
</body></html>'''

def _r(a, b):
    return set(range(a, b + 1))

# Real geographic postcode districts per Scottish area — do not generate
# pages for districts that don't exist.
VALID_DISTRICTS = {
    'ab': _r(10, 16) | _r(21, 25) | _r(30, 39) | _r(41, 45) | _r(51, 56),
    'dd': _r(1, 11),
    'dg': _r(1, 14) | {16},
    'eh': _r(1, 49) | _r(51, 55),
    'fk': _r(1, 21),
    'g':  _r(1, 5) | _r(11, 15) | _r(20, 23) | _r(31, 34) | _r(40, 46)
          | _r(51, 53) | _r(60, 69) | _r(71, 78) | _r(81, 84),
    'hs': _r(1, 9),
    'iv': _r(1, 28) | _r(30, 32) | {36} | _r(40, 49) | _r(51, 56) | {63},
    'ka': _r(1, 30),
    'kw': _r(1, 17),
    'ky': _r(1, 16),
    'ml': _r(1, 12),
    'pa': _r(1, 38) | _r(41, 49) | _r(60, 78),
    'ph': _r(1, 26) | _r(30, 44) | {49, 50},
    'td': _r(1, 15),
    'ze': _r(1, 3),
}

count = 0
for prefix, nums in VALID_DISTRICTS.items():
    for num in sorted(nums):
        pc = f"{prefix}{num}"
        pc_dir = f"postcode/{pc}"
        if not os.path.exists(pc_dir):
            os.makedirs(pc_dir, exist_ok=True)
            html = TEMPLATE.replace("PCUPPER", pc.upper())
            with open(f"{pc_dir}/index.html", "w") as f:
                f.write(html)
            count += 1

print(f"Created {count} new Scottish postcode pages")

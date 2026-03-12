#!/usr/bin/env python3
"""Generate city/town landing pages for CrimeSafe UK."""

import json
import os
import re
from pathlib import Path

# Top UK cities and towns by population/search volume
CITIES = {
    "london": {"name": "London", "force": "metropolitan", "force_name": "Metropolitan Police Service", "show_all": True},
    "birmingham": {"name": "Birmingham", "force": "west-midlands", "force_name": "West Midlands Police", "neighbourhoods": [
        "Erdington", "Kingstanding", "Stockland Green", "Tyburn", "Hall Green", "Moseley and Kings Heath",
        "Sparkbrook", "Springfield", "Bordesley Green", "Hodge Hill", "Shard End", "Washwood Heath",
        "Sutton Four Oaks", "Sutton New Hall", "Sutton Trinity", "Sutton Vesey", "Acocks Green", "Sheldon",
        "South Yardley", "Stechford and Yardley North", "City Centre", "Bartley Green", "Edgbaston", "Harborne",
        "Quinton", "Aston", "Nechells", "Small Heath and Highgate", "Kings Norton", "Longbridge", "Northfield",
        "Weoley", "Handsworth Wood", "Lozells and East Handsworth", "Oscott", "Perry Barr", "Billesley",
        "Bournville", "Brandwood", "Selly Oak", "Jewellery Quarter", "Ladywood", "Soho Road", "Winson Green NHT "
    ]},
    "manchester": {"name": "Manchester", "force": "greater-manchester", "force_name": "Greater Manchester Police", "neighbourhoods": [
        "Clayton", "Miles Platting", "Newton Heath", "Beswick", "Openshaw", "Castlefield", "Southern Gateway",
        "Higher Cheetham", "Higher Crumpsall", "Lower Cheetham", "Lower Crumpsall", "Charlestown", "Higher Blackley",
        "Collyhurst", "Harpurhey", "Monsall", "Moston and New Moston", "Ancoats", "Northern Quarter", "China Town",
        "Commercial District", "The Village", "Piccadilly Station", "Piccadilly Gardens", "Abbey Hey", "Debdale",
        "Gorton North", "Gorton South", "Anson", "Ardwick", "Brunswick", "Coverdale", "Longsight", "MRI",
        "Northmoor", "West Gorton", "Rusholme", "Alexandra Park (South Manchester)", "Hulme", "Moss Side",
        "St Georges", "University", "Levenshulme", "Fallowfield", "Platt Fields", "Burnage", "Old Moat",
        "Withington", "Whalley Range", "Chorlton"
    ]},
    "leeds": {"name": "Leeds", "force": "west-yorkshire", "force_name": "West Yorkshire Police"},
    "liverpool": {"name": "Liverpool", "force": "merseyside", "force_name": "Merseyside Police", "neighbourhoods": [
        "Anfield", "Everton East", "Everton North", "Everton West", "Kirkdale East", "Kirkdale West",
        "Vauxhall", "Walton", "Fazakerley East", "Fazakerley North", "Fazakerley West", "Norris Green",
        "Croxteth", "Clubmoor East", "Clubmoor West", "County", "Kensington and Fairfield", "Old Swan East",
        "Old Swan West", "Tuebrook Breckside Park", "Tuebrook Larkhill", "West Derby Deysbrook",
        "West Derby Leyfield", "West Derby Muirhead", "Toxteth", "Dingle", "Edge Hill", "Wavertree Village",
        "City Centre North", "City Centre South", "Waterfront North", "Waterfront South"
    ]},
    "bristol": {"name": "Bristol", "force": "avon-and-somerset", "force_name": "Avon and Somerset Constabulary", "neighbourhoods": [
        "Bedminster", "Bishopsworth", "Brislington East", "Brislington West", "Bristol Airport",
        "Clifton", "Clifton Down", "Cotham", "Easton and Redfield", "Filwood", "Henbury and Brentry",
        "Hengrove and Whitchurch", "Henleaze and Westbury-on-Trym", "Horfield", "Knowle", "Redland",
        "Southville", "St George Central", "St George Troopers Hill", "St George West", "Stoke Bishop"
    ]},
    "sheffield": {"name": "Sheffield", "force": "south-yorkshire", "force_name": "South Yorkshire Police", "neighbourhoods": [
        "Sheffield North East", "Sheffield South East", "Sheffield City Centre", "Sheffield South West", "Sheffield North West"
    ]},
    "newcastle": {"name": "Newcastle", "force": "northumbria", "force_name": "Northumbria Police", "neighbourhoods": [
        "Newcastle Central", "Jesmond and Heaton", "Byker and Walker", "Fenham and Scotswood",
        "Benwell and Elswick", "Gosforth and Great Park", "Blakelaw, Kenton and Fawdon", "Westerhope and Newburn"
    ]},
    "nottingham": {"name": "Nottingham", "force": "nottinghamshire", "force_name": "Nottinghamshire Police", "neighbourhoods": [
        "City Centre", "Arboretum", "St Ann's", "Sneinton and Dales", "Meadows", "Clifton",
        "Dunkirk & Lenton", "Radford & Park", "Wollaton West", "Wollaton East and Lenton Abbey",
        "Basford", "Aspley", "Bilborough", "Leen Valley", "Bulwell", "Bulwell Forest", "Bestwood",
        "Berridge", "Sherwood", "Mapperley & Wells"
    ]},
    "cardiff": {"name": "Cardiff", "force": "south-wales", "force_name": "South Wales Police", "neighbourhoods": [
        "Butetown", "Canton", "Cathays", "Ely", "Fairwater", "Gabalfa", "Grangetown", "Heath",
        "Llandaff", "Llandaff North", "Llanishen", "Llanrumney", "Pentwyn", "Plasnewydd",
        "Pontprennau and Old St. Mellons", "Rhiwbina", "Riverside", "Rumney", "Splott",
        "Trowbridge", "Whitchurch and Tongwynlais"
    ]},
    # Note: Edinburgh/Glasgow removed - Police Scotland doesn't use data.police.uk
    "leicester": {"name": "Leicester", "force": "leicestershire", "force_name": "Leicestershire Police", "neighbourhoods": [
        "City Centre", "Cultural Quarter", "Riverside", "Clarendon Park", "Latimer", "Belgrave",
        "Rushey Mead", "Humberstone and Hamilton", "Stoneygate", "Spinney Hills", "Evington",
        "North Evington", "Knighton", "Freemen/Saffron", "Eyres Monsell", "Aylestone",
        "Abbey", "Beaumont Leys", "Braunstone Park and Rowley Fields", "Fosse", "Westcotes", "Western"
    ]},
    "coventry": {"name": "Coventry", "force": "west-midlands", "force_name": "West Midlands Police", "neighbourhoods": [
        "Foleshill", "Stoke and Wyken", "St Michael's", "Henley and Longford",
        "Binley, Willenhall, Cheylesmore and Earlsdon", "Holbrook, Radford, Sherbourne and Bablake",
        "Woodlands, Wainbody, Westwood and Whoberley"
    ]},
    "bradford": {"name": "Bradford", "force": "west-yorkshire", "force_name": "West Yorkshire Police"},
    # Note: Belfast removed - PSNI uses district names (Strandtown, etc.) not "Belfast"
    "brighton": {"name": "Brighton", "force": "sussex", "force_name": "Sussex Police", "neighbourhoods": [
        "Regency Business", "Regency Seafront", "Tarner", "Hanover", "Queens Park", "Elm Grove",
        "Kemp Town - The Village", "Kemp Town", "Rottingdean and Coastal", "Woodingdean",
        "East Brighton", "Stanmer", "Moulsecoomb", "Patcham", "Withdean", "Preston Park",
        "Central Hove", "Hove Park", "Aldrington", "West Blatchington", "Hangleton and Knoll",
        "Portslade", "North Portslade", "South Portslade", "Mile Oak", "Hollingbury and Hollingdean"
    ]},
    "hull": {"name": "Hull", "force": "humberside", "force_name": "Humberside Police", "neighbourhoods": [
        "Ashby Central", "Avenues", "Beverley Rural", "Beverley and Newland", "Cottingham North",
        "Cottingham South", "Drypool", "Holderness", "Hull Central", "Mid Holderness",
        "North Holderness", "Orchard Park", "South East Holderness", "South West Holderness", "University"
    ]},
    "plymouth": {"name": "Plymouth", "force": "devon-and-cornwall", "force_name": "Devon & Cornwall Police", "neighbourhoods": [
        "Devonport", "Efford", "Eggbuckland", "Ham, Weston Mill & Pennycross", "Higher Compton & Mannamead",
        "Honicknowle", "Keyham", "Lipson & Laira", "Mount Gould", "Mutley", "Peverell & Hartley",
        "Plymouth City Centre", "Plympton St Maurice & Yealmpstone", "Plymstock", "Southway",
        "St Budeaux & Kings Tamerton", "Stoke", "Derriford West & Crownhill", "Estover, Glenholt & Derriford East",
        "Leigham & Mainstone"
    ]},
    "stoke-on-trent": {"name": "Stoke-on-Trent", "force": "staffordshire", "force_name": "Staffordshire Police", "neighbourhoods": [
        "Abbey Hulton & Townsend", "Baddeley, Milton & Norton", "Bentilee & Ubberley", "Blurton & Longton West",
        "Bradeley & Chell Heath", "Broadway & Longton East", "Burslem Central", "Burslem Park",
        "Etruria & Hanley", "Fenton West & Mount Pleasant", "Great Chell & Packmoor", "Hanley Park & Shelton",
        "Little Chell & Stanfield", "Longton South", "Meir Hay & Sandford Hill", "Meir North & Weston Coyney",
        "Meir Park & South", "Penkhull & Stoke", "Sneyd Green", "Springfields & Trent Vale", "Tunstall"
    ]},
    "wolverhampton": {"name": "Wolverhampton", "force": "west-midlands", "force_name": "West Midlands Police", "neighbourhoods": [
        "St Matthew's", "Wolverhampton City Centre", "Ettingshall, Blakenhall and Spring Vale",
        "St Peter's, Park and Graiseley", "Bilston and East Park", "Fallings Park, Bushbury and Low Hill",
        "Tettenhall, Penn, Merry Hill and Oxley", "Wednesfield and Heath Town"
    ]},
    "derby": {"name": "Derby", "force": "derbyshire", "force_name": "Derbyshire Constabulary", "neighbourhoods": [
        "Allestree and Darley", "Alvaston North", "Alvaston South", "Chaddesden and Spondon",
        "Chellaston", "Derby City", "Derwent and Oakwood", "Littleover and Blagreaves",
        "Mackworth and Morley", "Mickleover", "Normanton", "Sinfin and Osmaston"
    ]},
    "southampton": {"name": "Southampton", "force": "hampshire", "force_name": "Hampshire Constabulary", "neighbourhoods": [
        "Bargate", "Bevois", "Bitterne North", "Coxford, Redbridge and Millbrook",
        "Peartree and Woolston", "Portswood, Swaythling, and Bassett", "Shirley and Freemantle",
        "Sholing and Bitterne"
    ]},
    "portsmouth": {"name": "Portsmouth", "force": "hampshire", "force_name": "Hampshire Constabulary", "neighbourhoods": [
        "Central Southsea and St Judes", "Cosham", "Eastney and Milton", "Fratton, Baffins",
        "Hilsea, Copnor, Drayton and Farlington", "Paulsgrove"
    ]},
    "oxford": {"name": "Oxford", "force": "thames-valley", "force_name": "Thames Valley Police"},
    "cambridge": {"name": "Cambridge", "force": "cambridgeshire", "force_name": "Cambridgeshire Constabulary"},
    "york": {"name": "York", "force": "north-yorkshire", "force_name": "North Yorkshire Police"},
    "reading": {"name": "Reading", "force": "thames-valley", "force_name": "Thames Valley Police", "neighbourhoods": [
        "Abbey and Battle", "Calcot and Tilehurst", "Kentwood and Tilehurst", "Mapledurham and Thames",
        "Minster and Katesgrove", "Peppard and Caversham", "Redlands and Park", "Southcote and Norcot",
        "Whitley and Church"
    ]},
    "norwich": {"name": "Norwich", "force": "norfolk", "force_name": "Norfolk Constabulary"},
    "swansea": {"name": "Swansea", "force": "south-wales", "force_name": "South Wales Police", "neighbourhoods": [
        "Castle", "Clydach", "Cockett", "Cwmbwrla", "Dunvant and Killay", "Gorseinon and Penyrheol",
        "Gowerton", "Landore", "Llansamlet", "Mayals", "Morriston", "Mumbles", "Penderry",
        "Penllergaer", "Pontarddulais", "Sketty", "Townhill", "Uplands"
    ]},
    "luton": {"name": "Luton", "force": "bedfordshire", "force_name": "Bedfordshire Police"},
    "milton-keynes": {"name": "Milton Keynes", "force": "thames-valley", "force_name": "Thames Valley Police", "neighbourhoods": [
        "Bradwell and Stantonbury", "Campbell Park South and Woughton", "Central Bletchley and Fenny Stratford",
        "Great Linford", "Loughton Park", "Milton Keynes City Centre and Campbell Park", "Newport Pagnell",
        "Rural Milton Keynes", "Stony Stratford and Wolverton", "West Bletchley"
    ]},
    "warrington": {"name": "Warrington", "force": "cheshire", "force_name": "Cheshire Constabulary", "neighbourhoods": [
        "Bewsey and Whitecross", "Birchwood", "Burtonwood and Winwick", "Culcheth, Glazebury and Croft",
        "Fairfield and Howley", "Grappenhall and Thelwall", "Great Sankey North", "Great Sankey South",
        "Latchford East", "Latchford West", "Lymm", "Orford", "Penketh and Cuerdley", "Poulton North",
        "Poulton South", "Stockton Heath", "Warrington Town Centre", "Westbrook"
    ]},
    "swindon": {"name": "Swindon", "force": "wiltshire", "force_name": "Wiltshire Police", "neighbourhoods": [
        "Covingham", "Eastcott", "Gorse Hill", "Grange Park", "Haydon Wick", "Lawn", "Lower Stratton",
        "Moredon", "Nythe", "Old Town", "Park North", "Park South", "Penhill", "Pinehurst", "Rodbourne",
        "Rodbourne Cheney", "Stratton Village", "Swindon Town Centre", "Upper Stratton", "Walcot East",
        "Walcot West", "Woodhall Park and Taw Hill", "Wroughton"
    ]},
    "peterborough": {"name": "Peterborough", "force": "cambridgeshire", "force_name": "Cambridgeshire Constabulary"},
    "exeter": {"name": "Exeter", "force": "devon-and-cornwall", "force_name": "Devon & Cornwall Police", "neighbourhoods": [
        "Alphington", "Exeter City Centre", "Exwick", "Mincinglake", "Pinhoe", "St Davids", "St James",
        "St Loyes", "Whipton Barton", "Countess Wear & Topsham", "Cowick & St Thomas",
        "Duryard & Pennsylvannia", "Heavitree & Polsloe", "Newtown & St Leonards"
    ]},
    "bath": {"name": "Bath", "force": "avon-and-somerset", "force_name": "Avon and Somerset Constabulary"},
    "cheltenham": {"name": "Cheltenham", "force": "gloucestershire", "force_name": "Gloucestershire Constabulary", "neighbourhoods": [
        "Charlton Kings", "Cheltenham Town Centre", "Hesters Way", "Lansdown", "Leckhampton",
        "Springbank and Fiddlers Green", "St Marks", "St Pauls and Pittville", "Swindon Village and Wymans Brook",
        "Tuffley and Grange", "Whaddon Lynworth and Oakley"
    ]},
    "gloucester": {"name": "Gloucester", "force": "gloucestershire", "force_name": "Gloucestershire Constabulary", "neighbourhoods": [
        "Barton, Tredworth and White City", "Gloucester City Centre", "Hucclecote Abbey and Upton St Leonards",
        "Kingsholm and Wotton", "Longlevens and Elmbridge", "Matson and Robinswood", "Podsmead",
        "Quedgeley, Kingsway, Hardwicke, Longney and Elmore"
    ]},
    "lincoln": {"name": "Lincoln", "force": "lincolnshire", "force_name": "Lincolnshire Police"},
}

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_header(title, description):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="S7uUZGMb9yLeKT16YkQGWumhCd0n70jt19wxR1qrYEc">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-CK531DR9X9"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-CK531DR9X9');</script>
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="preconnect" href="https://api.fontshare.com" crossorigin>
    <link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
    <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
    <meta name="theme-color" content="#01696F">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="/" class="nav-logo">
                <svg width="28" height="28" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="currentColor" opacity="0.1"/>
  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="none" stroke="currentColor" stroke-width="20" stroke-linejoin="round"/>
  <text x="256" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="160" fill="currentColor">UK</text>
</svg>
                <span>CrimeSafe UK</span>
            </a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/forces/">Forces</a>
                <a href="/districts/">Districts</a>
                <a href="/safest/">Rankings</a>
                <a href="/about/">About</a>
                <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">🌙</button>
            </div>
        </div>
    </nav>
'''

def get_footer():
    return '''
    <footer class="footer">
        <div class="container">
            <p>&copy; 2026 CrimeSafe UK. Data from <a href="https://data.police.uk">data.police.uk</a> (Open Government Licence)</p>
            <p style="margin-top: var(--space-2);">
                <a href="/about/">About</a> · 
                <a href="/privacy/">Privacy</a>
            </p>
        </div>
    </footer>
    <script>
        const toggle = document.getElementById('themeToggle');
        const html = document.documentElement;
        const stored = localStorage.getItem('theme');
        if (stored) html.setAttribute('data-theme', stored);
        else if (window.matchMedia('(prefers-color-scheme: dark)').matches) html.setAttribute('data-theme', 'dark');
        toggle.textContent = html.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            toggle.textContent = next === 'dark' ? '☀️' : '🌙';
        });
    </script>
</body>
</html>'''

def find_neighbourhoods_for_city(city_slug, city_name, force_id, forces_data, crime_data, explicit_nbs=None):
    """Find neighbourhoods that match the city name or are explicitly listed."""
    matching = []
    explicit_set = set(explicit_nbs) if explicit_nbs else set()
    
    for force in forces_data['forces']:
        if force['id'] == force_id:
            for nb in force.get('neighbourhoods', []):
                nb_name = nb.get('name', '')
                nb_id = nb.get('id', '')
                
                # Match if explicitly listed, or city name is in neighbourhood name
                if nb_name in explicit_set or (not explicit_set and (city_name.lower() in nb_name.lower() or city_slug in slugify(nb_name))):
                    # Get crime data
                    key = f"{force_id}_{nb_id}"
                    crime = crime_data.get(key, {})
                    matching.append({
                        'name': nb_name,
                        'slug': slugify(nb_name),
                        'force_slug': slugify(force['name']),
                        'score': crime.get('score', 0),
                        'total_crimes': crime.get('total_crimes', 0)
                    })
    
    # Sort by score descending (safest first)
    matching.sort(key=lambda x: x['score'], reverse=True)
    return matching

def generate_city_page(city_slug, city_info, neighbourhoods, crime_stats):
    """Generate a city landing page."""
    city_name = city_info['name']
    force_name = city_info['force_name']
    force_slug = slugify(force_name)
    
    # Calculate city-wide stats first (needed for title)
    total_crimes = sum(n.get('total_crimes', 0) for n in neighbourhoods)
    avg_score = round(sum(n.get('score', 0) for n in neighbourhoods) / max(1, len(neighbourhoods)))
    
    title = f"{city_name} Crime Rate 2026 — Avg Safety Score {avg_score}/100 | CrimeSafe UK"
    desc = f"Is {city_name} safe? Average Safety Score: {avg_score}/100 across {len(neighbourhoods)} areas. View {total_crimes:,} crimes reported, compare neighbourhoods, find the safest places."
    
    html = get_header(title, desc)
    
    # Safety grade color
    if avg_score >= 60:
        grade_color = "#16a34a"
        grade_bg = "#dcfce7"
    elif avg_score >= 40:
        grade_color = "#ca8a04"
        grade_bg = "#fef9c3"
    else:
        grade_color = "#dc2626"
        grade_bg = "#fee2e2"
    
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/city/">City</a> › {city_name}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-6) 0;">
            <div class="container">
                <h1 style="color: var(--color-text);">Crime in {city_name}</h1>
                <p class="hero-sub">Explore crime statistics and safety scores for {city_name} neighbourhoods</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-8);">
            <div class="container">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-4);">
                    <div class="stat-card" style="text-align: center; padding: var(--space-5);">
                        <div style="font-size: var(--text-2xl); font-weight: 700;">{len(neighbourhoods)}</div>
                        <div style="font-size: var(--text-sm); color: var(--color-text-muted);">Neighbourhoods</div>
                    </div>
                    <div class="stat-card" style="text-align: center; padding: var(--space-5);">
                        <div style="font-size: var(--text-2xl); font-weight: 700;">{total_crimes:,}</div>
                        <div style="font-size: var(--text-sm); color: var(--color-text-muted);">Crimes (Monthly)</div>
                    </div>
                    <div class="stat-card" style="text-align: center; padding: var(--space-5);">
                        <div style="font-size: var(--text-2xl); font-weight: 700; color: {grade_color};">{avg_score}/100</div>
                        <div style="font-size: var(--text-sm); color: var(--color-text-muted);">Safety Score</div>
                    </div>
                    <div class="stat-card" style="text-align: center; padding: var(--space-5);">
                        <div style="font-size: var(--text-sm); color: var(--color-text-muted); margin-bottom: var(--space-1);">Police Force</div>
                        <a href="/force/{force_slug}/" style="color: var(--color-primary); font-weight: 600; font-size: var(--text-sm);">{force_name}</a>
                    </div>
                </div>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-8);">
            <div class="container">
                <h2 style="margin-bottom: var(--space-4); color: var(--color-text);">Neighbourhoods in {city_name}</h2>
                <p style="margin-bottom: var(--space-6); color: var(--color-text-muted);">Click any area to view detailed crime statistics. Sorted by safety score.</p>
                <div class="force-grid">'''
    
    for nb in neighbourhoods:
        score = nb.get('score', 0)
        if score >= 60:
            color = "#16a34a"
            bg = "#dcfce7"
        elif score >= 40:
            color = "#ca8a04"
            bg = "#fef9c3"
        else:
            color = "#dc2626"
            bg = "#fee2e2"
        
        html += f'''
                    <a href="/neighbourhood/{nb['force_slug']}/{nb['slug']}/" class="force-card" style="display: flex; justify-content: space-between; align-items: center; transition: transform 0.15s, box-shadow 0.15s;" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)'" onmouseout="this.style.transform='none';this.style.boxShadow='none'">
                        <div style="display: flex; align-items: center; gap: var(--space-3);">
                            <span style="background: {bg}; color: {color}; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: var(--text-sm);">{score}</span>
                            <span style="font-weight: 500;">{nb['name']}</span>
                        </div>
                        <span style="color: var(--color-text-muted);">→</span>
                    </a>'''
    
    html += '''
                </div>
            </div>
        </section>
        
        <section style="padding: var(--space-8) 0;">
            <div class="container">
                <div class="stat-card">
                    <h2>Is ''' + city_name + ''' Safe?</h2>
                    <p style="margin-top: var(--space-4);">''' + city_name + f''' has an average safety score of <strong>{avg_score}/100</strong> across its {len(neighbourhoods)} neighbourhoods. '''
    
    if avg_score >= 60:
        html += f'''This indicates that {city_name} is generally a <strong>safe city</strong> to live in or visit.'''
    elif avg_score >= 40:
        html += f'''This indicates <strong>moderate safety levels</strong>. Some areas are safer than others - check individual neighbourhood scores.'''
    else:
        html += f'''This indicates <strong>higher than average crime rates</strong>. Some areas have lower crime - check individual neighbourhood scores for safer options.'''
    
    html += '''</p>
                    <p style="margin-top: var(--space-3);">Data is sourced from the official <a href="https://data.police.uk">data.police.uk</a> API and updated monthly.</p>
                </div>
            </div>
        </section>
    </main>
'''
    
    html += get_footer()
    return html

def load_crime_scores():
    """Load crime data and calculate per-capita percentile scores."""
    crime_dir = 'data/neighbourhood_crimes'
    
    all_rates = []
    crime_data = {}
    
    for fname in os.listdir(crime_dir):
        if not fname.endswith('.json'):
            continue
        with open(f'{crime_dir}/{fname}') as f:
            # Handle both single JSON and NDJSON formats
            content = f.read().strip()
            for line in content.split('\n'):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except:
                    continue
                
                force_id = data.get('force_id', '')
                nb_id = data.get('neighbourhood_id', '')
                total_crimes = data.get('total_crimes', 0)
                
                # Use per-capita rate for fairer scoring
                rate = data.get('crime_rate_per_1000')
                if rate is None:
                    pop = data.get('population', 12098)
                    rate = (total_crimes / pop) * 1000 if pop > 0 else 0
                
                key = f'{force_id}_{nb_id}'
                crime_data[key] = {'crime_rate': rate, 'total_crimes': total_crimes}
                all_rates.append((key, rate))
    
    # Assign percentile scores based on crime rate (lower rate = safer = higher score)
    all_rates.sort(key=lambda x: x[1])
    total = len(all_rates)
    for i, (key, _) in enumerate(all_rates):
        percentile = (i / max(1, total - 1)) * 100
        score = round(100 - percentile)
        crime_data[key]['score'] = score
    
    return crime_data

def main():
    """Generate all city pages."""
    
    # Load data
    with open('data/forces.json') as f:
        forces_data = json.load(f)
    
    crime_data = load_crime_scores()
    
    # Create output directory
    Path('city').mkdir(exist_ok=True)
    
    generated = 0
    city_scores = {}
    
    for city_slug, city_info in CITIES.items():
        neighbourhoods = []
        
        # For cities with show_all flag, get all force neighbourhoods
        if city_info.get('show_all'):
            for force in forces_data['forces']:
                if force['id'] == city_info['force']:
                    for nb in force.get('neighbourhoods', []):
                        nb_id = nb.get('id', '')
                        key = f"{city_info['force']}_{nb_id}"
                        crime = crime_data.get(key, {})
                        neighbourhoods.append({
                            'name': nb['name'],
                            'slug': slugify(nb['name']),
                            'force_slug': slugify(force['name']),
                            'score': crime.get('score', 0),
                            'total_crimes': crime.get('total_crimes', 0)
                        })
                    neighbourhoods.sort(key=lambda x: x['score'], reverse=True)
                    break
        else:
            # Find matching neighbourhoods by name or explicit list
            neighbourhoods = find_neighbourhoods_for_city(
                city_slug, city_info['name'], city_info['force'], forces_data, crime_data,
                explicit_nbs=city_info.get('neighbourhoods')
            )
        
        if not neighbourhoods:
            # Skip cities with no matching neighbourhoods
            print(f"  ⚠️  {city_info['name']}: No neighbourhoods found, skipping")
            continue
        
        if neighbourhoods:
            # Calculate average score for city
            scores = [nb['score'] for nb in neighbourhoods if nb.get('score', 0) > 0]
            if scores:
                city_scores[city_slug] = round(sum(scores) / len(scores))
            
            html = generate_city_page(city_slug, city_info, neighbourhoods, crime_data)
            
            page_dir = Path(f'city/{city_slug}')
            page_dir.mkdir(exist_ok=True)
            
            with open(page_dir / 'index.html', 'w') as f:
                f.write(html)
            
            generated += 1
            print(f"  {city_info['name']}: {len(neighbourhoods)} neighbourhoods")
    
    # Generate cities index page
    generate_cities_index(city_scores)
    
    print(f"\n✅ Generated {generated} city pages")

def get_score_class(score):
    if score is None or score == 0: return 'score-na'
    if score >= 60: return 'score-green'
    if score >= 40: return 'score-amber'
    return 'score-red'

def generate_cities_index(city_scores):
    """Generate the cities index page."""
    html = get_header("UK Cities Crime Statistics | CrimeSafe UK", 
                      "Browse crime statistics for major UK cities and towns. Compare safety scores and find the safest areas.")
    
    html += '''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › City
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>UK Cities</h1>
                <p class="hero-sub">Crime statistics for major UK cities and towns</p>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="force-grid">'''
    
    for city_slug, city_info in sorted(CITIES.items(), key=lambda x: x[1]['name']):
        score = city_scores.get(city_slug, 0)
        score_class = get_score_class(score)
        score_display = score if score else '—'
        html += f'''
                    <a href="/city/{city_slug}/" class="force-card">
                        <div class="card-header">
                            <h3>{city_info['name']}</h3>
                            <span class="score-badge {score_class}">{score_display}</span>
                        </div>
                        <p style="color: var(--color-text-muted); font-size: var(--text-sm);">{city_info['force_name']}</p>
                    </a>'''
    
    html += '''
                </div>
            </div>
        </section>
    </main>
'''
    html += get_footer()
    
    Path('city').mkdir(exist_ok=True)
    with open('city/index.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()

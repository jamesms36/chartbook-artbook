#!/usr/bin/env python3
"""
Reads artworks.json and writes index.html.
Run this after scrape.py to regenerate the site.
"""

import json
import re
from urllib.parse import unquote

with open("artworks.json") as f:
    artworks = json.load(f)

# Sort newest first
artworks.sort(key=lambda x: x.get("issue_num", 0), reverse=True)

def js_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")

def img_dims(url):
    """Extract WxH from embedded S3 filename, e.g. _1300x952.png"""
    m = re.search(r'_(\d+)x(\d+)\.(png|jpe?g|webp)', unquote(url), re.I)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

cards_js = "const artworks = [\n"
for a in artworks:
    w, h = img_dims(a['img'])
    ratio = f"{w}/{h}" if w and h else "4/3"
    cards_js += f"""  {{
    issue: "{js_str(a['issue'])}",
    issue_num: {a.get('issue_num', 0)},
    artist: "{js_str(a['artist'])}",
    title: "{js_str(a['title'])}",
    img: "{js_str(a['img'])}",
    url: "{js_str(a['url'])}",
    ratio: "{ratio}"
  }},\n"""
cards_js += "];"

count = len(artworks)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Chartbook Artbook</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #f5f2ed;
      --card-bg: #fff;
      --text: #1a1a1a;
      --muted: #888;
      --accent: #8b5e3c;
      --border: #e0d9d0;
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Georgia', serif;
      min-height: 100vh;
    }}

    /* ── Header ── */
    header {{
      padding: 4rem 2rem 3rem;
      text-align: center;
      border-bottom: 1px solid var(--border);
      max-width: 860px;
      margin: 0 auto;
    }}

    header .eyebrow {{
      font-size: 0.75rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 1rem;
      font-family: 'Helvetica Neue', sans-serif;
    }}

    header h1 {{
      font-size: clamp(2.2rem, 5vw, 3.8rem);
      font-weight: 400;
      line-height: 1.1;
      letter-spacing: -0.02em;
      margin-bottom: 1.2rem;
    }}

    header p {{
      font-size: 1.05rem;
      color: var(--muted);
      max-width: 480px;
      margin: 0 auto;
      line-height: 1.7;
      font-style: italic;
    }}

    header p a {{
      color: var(--accent);
      text-decoration: none;
    }}
    header p a:hover {{ text-decoration: underline; }}

    .count {{
      margin-top: 1rem;
      font-size: 0.8rem;
      color: var(--muted);
      font-family: 'Helvetica Neue', sans-serif;
      font-style: normal;
      letter-spacing: 0.05em;
    }}

    /* ── Sort bar ── */
    .sort-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 0.5rem;
      padding: 1.75rem 1.5rem 0;
      max-width: 1400px;
      margin: 0 auto;
    }}

    .sort-btn {{
      background: none;
      border: 1px solid var(--border);
      color: var(--muted);
      font-family: 'Helvetica Neue', sans-serif;
      font-size: 0.72rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 0.4rem 0.9rem;
      border-radius: 2px;
      cursor: pointer;
      transition: border-color 0.2s, color 0.2s;
    }}
    .sort-btn:hover {{
      border-color: var(--accent);
      color: var(--text);
    }}
    .sort-btn.active {{
      border-color: var(--accent);
      color: var(--accent);
    }}

    /* ── Gallery ── */
    .gallery {{
      padding: 3rem 1.5rem 5rem;
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      gap: 1.25rem;
      align-items: flex-start;
    }}

    .gallery-col {{
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}

    /* ── Card ── */
    .card {{
      background: var(--card-bg);
      border-radius: 4px;
      overflow: hidden;
      display: block;
      text-decoration: none;
      color: inherit;
      transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}

    .card img {{
      width: 100%;
      height: auto;
      display: block;
    }}

    .card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    }}

    .card img {{
      width: 100%;
      display: block;
      background: #222;
    }}

    .card-caption {{
      padding: 1rem 1.1rem 1.2rem;
      border-top: 1px solid var(--border);
    }}

    .card-issue {{
      font-size: 0.68rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--accent);
      font-family: 'Helvetica Neue', sans-serif;
      margin-bottom: 0.4rem;
    }}

    .card-title {{
      font-size: 0.95rem;
      line-height: 1.4;
      font-style: italic;
      margin-bottom: 0.25rem;
    }}

    .card-artist {{
      font-size: 0.8rem;
      color: var(--muted);
      font-family: 'Helvetica Neue', sans-serif;
    }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 2.5rem 1rem;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.8rem;
      font-family: 'Helvetica Neue', sans-serif;
      letter-spacing: 0.03em;
    }}

    footer a {{
      color: var(--accent);
      text-decoration: none;
    }}
    footer a:hover {{ text-decoration: underline; }}

    /* ── Lightbox ── */
    .lightbox {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(20,15,10,0.95);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      cursor: zoom-out;
      padding: 2rem;
    }}
    .lightbox.open {{ display: flex; }}

    .lightbox-inner {{
      position: relative;
      max-width: 90vw;
      max-height: 92vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1.2rem;
      cursor: default;
      padding-bottom: 0.5rem;
    }}

    .lightbox-inner img {{
      max-width: 100%;
      max-height: 65vh;
      object-fit: contain;
      border-radius: 2px;
      box-shadow: 0 20px 80px rgba(0,0,0,0.8);
      flex-shrink: 0;
    }}

    .lightbox-info {{
      text-align: center;
      color: #e8e4dc;
    }}

    .lightbox-info .lb-title {{
      font-size: 1.1rem;
      font-style: italic;
      margin-bottom: 0.3rem;
      color: #e8e4dc;
    }}

    .lightbox-info .lb-artist {{
      font-size: 0.85rem;
      color: #aaa;
      font-family: 'Helvetica Neue', sans-serif;
      margin-bottom: 0.6rem;
    }}

    .lightbox-info .lb-link {{
      font-size: 0.75rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--accent);
      text-decoration: none;
      font-family: 'Helvetica Neue', sans-serif;
      border: 1px solid var(--accent);
      padding: 0.35rem 0.8rem;
      border-radius: 2px;
      display: inline-block;
      transition: background 0.2s, color 0.2s;
    }}
    .lightbox-info .lb-link:hover {{
      background: var(--accent);
      color: #111;
    }}

    .lightbox-close {{
      position: fixed;
      top: 1.5rem;
      right: 1.5rem;
      background: none;
      border: none;
      color: var(--muted);
      font-size: 1.8rem;
      cursor: pointer;
      line-height: 1;
      z-index: 1001;
    }}
    .lightbox-close:hover {{ color: var(--text); }}

  </style>
</head>
<body>

<header>
  <p class="eyebrow">Adam Tooze · Chartbook</p>
  <h1>Artbook</h1>
  <p>
    Every issue of <a href="https://adamtooze.substack.com" target="_blank" rel="noopener">Chartbook</a>
    opens with a work of art.<br>This is a gallery of those selections.
  </p>
  <p class="count">{count} artworks</p>
</header>

<nav class="sort-bar" aria-label="Sort options">
  <button class="sort-btn active" data-sort="issue-desc">Newest first</button>
  <button class="sort-btn" data-sort="issue-asc">Oldest first</button>
  <button class="sort-btn" data-sort="random">Random</button>
</nav>

<main class="gallery" id="gallery"></main>

<footer>
  Art selections by <a href="https://adamtooze.substack.com" target="_blank" rel="noopener">Adam Tooze</a> ·
  <a href="https://adamtooze.substack.com/archive?sort=new" target="_blank" rel="noopener">Browse all issues</a>
</footer>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true">
  <button class="lightbox-close" id="lb-close" aria-label="Close">&times;</button>
  <div class="lightbox-inner" id="lb-inner" onclick="event.stopPropagation()">
    <img id="lb-img" src="" alt="" />
    <div class="lightbox-info">
      <div class="lb-title" id="lb-title"></div>
      <div class="lb-artist" id="lb-artist"></div>
      <a class="lb-link" id="lb-link" href="#" target="_blank" rel="noopener">Read issue &#8599;</a>
    </div>
  </div>
</div>

<script>
{cards_js}

function getColCount() {{
  const w = window.innerWidth;
  if (w >= 1200) return 4;
  if (w >= 900)  return 3;
  return 2;
}}

function sortedArtworks(mode) {{
  const a = artworks.slice();
  if (mode === 'issue-desc') a.sort((x, y) => y.issue_num - x.issue_num);
  else if (mode === 'issue-asc') a.sort((x, y) => x.issue_num - y.issue_num);
  else if (mode === 'random') {{
    for (let i = a.length - 1; i > 0; i--) {{
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }}
  }}
  return a;
}}

function makeCard(art) {{
  const card = document.createElement('a');
  card.className = 'card';
  card.href = '#';
  card.setAttribute('role', 'button');
  card.setAttribute('aria-label', art.title + ' by ' + art.artist);
  card.innerHTML = `
    <img src="${{art.img}}" alt="${{art.title}} — ${{art.artist}}"
         loading="lazy" style="aspect-ratio:${{art.ratio}}" />
    <div class="card-caption">
      <div class="card-issue">${{art.issue}}</div>
      <div class="card-title">${{art.title}}</div>
      <div class="card-artist">${{art.artist}}</div>
    </div>
  `;
  card.addEventListener('click', (e) => {{ e.preventDefault(); openLightbox(art); }});
  return card;
}}

const gallery = document.getElementById('gallery');
let currentSort = 'issue-desc';

function renderGallery() {{
  const cols = getColCount();
  const items = sortedArtworks(currentSort);
  gallery.innerHTML = '';
  // Create one div per column
  const colEls = Array.from({{length: cols}}, () => {{
    const d = document.createElement('div');
    d.className = 'gallery-col';
    gallery.appendChild(d);
    return d;
  }});
  // Distribute round-robin: item 0→col0, item 1→col1, ..., item cols→col0, ...
  // This guarantees consecutive items land in adjacent columns, so reading
  // left-to-right across any visual band is roughly chronological.
  items.forEach((art, i) => colEls[i % cols].appendChild(makeCard(art)));
}}

document.querySelectorAll('.sort-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    currentSort = btn.dataset.sort;
    document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderGallery();
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }});
}});

renderGallery();

let resizeTimer;
window.addEventListener('resize', () => {{
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(renderGallery, 150);
}});

// Lightbox
const lightbox = document.getElementById('lightbox');
const lbImg    = document.getElementById('lb-img');
const lbTitle  = document.getElementById('lb-title');
const lbArtist = document.getElementById('lb-artist');
const lbLink   = document.getElementById('lb-link');

function openLightbox(art) {{
  lbImg.src    = art.img;
  lbImg.alt    = art.title;
  lbTitle.textContent  = art.title;
  lbArtist.textContent = art.artist + '  ·  ' + art.issue;
  lbLink.href  = art.url;
  lightbox.classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeLightbox() {{
  lightbox.classList.remove('open');
  document.body.style.overflow = '';
  lbImg.src = '';
}}

document.getElementById('lb-close').addEventListener('click', closeLightbox);
lightbox.addEventListener('click', closeLightbox);
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') closeLightbox(); }});
</script>

</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(page)

print(f"Built index.html with {count} artworks.")

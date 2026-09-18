# Fl1pp3r69 landing (ARGUS VEIL)

Public site for https://fl1pp3r69.jonbailey.xyz/

## Deploy (production)

```powershell
cd landing
npx wrangler deploy -c wrangler.worker.toml
```

Worker name: `fl1pp3r69-site` / custom domain route on `fl1pp3r69.jonbailey.xyz`.

## Structure

| Path | Role |
|------|------|
| `index.html` | Flagship single-page landing |
| `css/site.css` | Design tokens (Obsidian / Blood / Phosphor / Amber) |
| `js/site.js` | Pipeline phase UI |
| `assets/` | Hero, emblem, OG share card, favicons |
| `llms.txt` / `sitemap.xml` / `robots.txt` | SEO + AEO |
| `projects-panel.js` | Ecosystem switcher |
| `wrangler.worker.toml` | Workers Static Assets deploy |

## Version surface

Bump cache-bust query (`?v=`) on CSS/JS/images when shipping visual changes. Use a **date stamp** (e.g. `20260917`) for CSS/JS so cache-bust does not impersonate a product release. Keep OG `share-card.jpg` + JSON-LD `softwareVersion` aligned with the tagged product (currently **4.0.0 ARGUS VEIL**). User-facing copy is ASCII only.

Fleet visits widget: `hits.jonbailey.xyz/c.js` with slug `fl1pp3r69`. CSP in `_headers` and `worker.js` must both allow that origin on script-src and connect-src. Do not remove the widget to "simplify" CSP.

## Tests (cook)

From repo root. Product version stays 4.0.0 until a tagged cut.

```powershell
py -3 .\scripts\check_version_surface.py
py -3 -m pytest .\desktop\tests -q
```

Gates: authorized-use copy, 10 FAP ids vs `fap/*/application.fam`, FAQ JSON-LD vs visible summaries, hits widget + CSP lockstep, skip-link / tablist / reduced-motion, share-card 1200x630 and hero 1600x900.

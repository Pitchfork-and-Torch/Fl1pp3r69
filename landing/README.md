# Fl1pp3r69 landing (ARGUS VEIL)

Public site for https://fl1pp3r69.jonbailey.xyz/

## Deploy (production)

```powershell
cd landing
npx wrangler deploy -c wrangler.worker.toml
```

Worker name: `fl1pp3r69-site` · custom domain route on `fl1pp3r69.jonbailey.xyz`.

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

Bump cache-bust query (`?v=`) on CSS/JS/images when shipping visual changes. Keep OG `share-card.jpg` + JSON-LD `softwareVersion` aligned with product (currently **4.0.0 ARGUS VEIL**).

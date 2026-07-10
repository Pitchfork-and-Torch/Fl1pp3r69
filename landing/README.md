# Fl1pp3r69 public landing

Ghost Continuum–style launch page with typewriter boot, dual infographics, SEO/AEO, and the shared **Other projects** panel.

## Local preview

```powershell
cd landing
python -m http.server 8790 --bind 127.0.0.1
# open http://127.0.0.1:8790/
```

## Deploy (Cloudflare Pages)

```powershell
cd landing
npx wrangler pages deploy . --project-name=fl1pp3r69 --commit-dirty=true
```

- Preview: https://fl1pp3r69.pages.dev  
- Custom domain (when DNS attached): https://fl1pp3r69.jonbailey.xyz/

Attach `fl1pp3r69.jonbailey.xyz` in Cloudflare dashboard → Pages → fl1pp3r69 → Custom domains (CNAME to `fl1pp3r69.pages.dev`).

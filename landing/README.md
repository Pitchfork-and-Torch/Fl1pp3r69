# Fl1pp3r69 public landing

**One production path:** Workers Static Assets → `https://fl1pp3r69.jonbailey.xyz/`

The site is the **launch explainer** (infographic-first). No typewriter boot, no multi-section text wall.

## Local preview

```powershell
cd landing
python -m http.server 8790 --bind 127.0.0.1
# open http://127.0.0.1:8790/
```

## Deploy (production — only path that serves the custom domain)

```powershell
cd landing
npx wrangler deploy -c wrangler.worker.toml
```

- Production: https://fl1pp3r69.jonbailey.xyz/

## Optional Pages preview only

`fl1pp3r69.pages.dev` can still be updated for previews; it is **not** the custom domain:

```powershell
npx wrangler pages deploy . --project-name=fl1pp3r69 --branch=main --commit-dirty=true
```

Do not re-attach `fl1pp3r69.jonbailey.xyz` to the Pages project while the Worker holds it.

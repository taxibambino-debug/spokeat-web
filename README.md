# spokeat.com: public site

Static site for Spoke At: landing pages (EN/SV), guides, expertise pages, author page, contact and early access.

| Folder | What it holds |
|---|---|
| `public/` | The built site that Cloudflare Pages serves. Generated: do not edit by hand. |
| `content/articles/` | Article sources (Markdown, EN and SV), slugs and the author profile |
| `content/expertise.json` | Expertise areas and subjects |
| `content/landing/` | Landing page sources (EN and SV) |
| `src/build.py` | Builds `public/` from `content/` (Python 3 + `markdown`, Node for the landing pages) |

Rebuild: `pip install markdown && python3 src/build.py`, then commit `public/` together with the source change.

## Cloudflare Pages settings
- Connect to Git: this repository, branch `main`
- Framework preset: None
- Build command: (empty)
- Build output directory: `public`

Every push to `main` publishes automatically.

## Domain
1. Cloudflare → Add a site → `spokeat.com` (Free plan); copy the two nameservers.
2. Network Solutions → spokeat.com → change nameservers to those two.
3. When active: Pages project → Custom domains → add `spokeat.com` and `www.spokeat.com`.

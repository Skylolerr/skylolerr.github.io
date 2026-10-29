# skylolerr.github.io

The project website of [Skylolerr](https://github.com/Skylolerr): Home Assistant
integrations installed with HACS. English at `/`, German at `/de/`.

Plain static HTML and one stylesheet – no build step, no JavaScript, no external
requests, no cookies or tracking. GitHub Pages serves the files as they are
(`.nojekyll` switches Jekyll off).

## Structure

| Path | Content |
|---|---|
| `index.html`, `de/index.html` | Home page with the list of projects |
| `energy-flow-mapper/`, `de/energy-flow-mapper/` | Energy Flow Mapper |
| `daily-challenge/`, `de/daily-challenge/` | Daily Challenge |
| `404.html` | Bilingual "page not found" |
| `assets/css/site.css` | The only stylesheet; light and dark theme follow the system |
| `assets/img/` | WebP screenshots and animations, icons, Open Graph images |
| `sitemap.xml`, `robots.txt` | For search engines, with hreflang alternates |
| `scripts/prepare_images.py` | Builds `assets/img/` from the projects' `docs/images` |
| `scripts/check_site.py` | Checks links, images, SEO tags, hreflang, JSON-LD and the sitemap |
| `scripts/set_domain.py` | Switches all absolute URLs to a custom domain and writes `CNAME` |

Every page exists in both languages. A change to one page goes into its translation in
the same commit, and the FAQ on a page must match its `FAQPage` JSON-LD (the check
script compares them).

## Working on the site

```bash
# Preview (then open http://127.0.0.1:8765/)
python -m http.server 8765 --bind 127.0.0.1

# Before every commit
python scripts/check_site.py

# After the README images of a project changed (needs Pillow)
python scripts/prepare_images.py
```

Version numbers are deliberately not on the pages, so they never go stale; the pages
link to the latest release instead. Update the minimum Home Assistant version and the
`lastmod` dates in `sitemap.xml` when the content changes.

## Publishing on GitHub Pages

1. Create the **public** repository `Skylolerr/skylolerr.github.io` (no README, no
   license – the files come from here):

   ```bash
   gh repo create Skylolerr/skylolerr.github.io --public --description "Project website of Skylolerr: Home Assistant integrations"
   git remote add origin https://github.com/Skylolerr/skylolerr.github.io.git
   git push -u origin main
   ```

2. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a
   branch**, branch **main**, folder **/ (root)**, then **Save**. A user site
   (`<user>.github.io`) is usually switched on automatically after the first push.
3. After a minute or two the site is online at <https://skylolerr.github.io/>.
4. Optional, for search engines: add the site to
   [Google Search Console](https://search.google.com/search-console) and
   [Bing Webmaster Tools](https://www.bing.com/webmasters) and submit
   `https://skylolerr.github.io/sitemap.xml`. Link the site from the project READMEs and
   the GitHub profile (website field) as well.

## Adding a custom domain later

All absolute URLs (canonical, hreflang, Open Graph, JSON-LD, sitemap, robots.txt) use
`https://skylolerr.github.io/`. Links between pages are root-relative (`/de/…`), so they
work on any domain.

1. Buy the domain (for example `skylolerr.dev`; `.dev` always requires HTTPS, which
   GitHub Pages provides).
2. Recommended: verify the domain for the account first (GitHub → **Settings → Pages →
   Add a domain**) so nobody else can use it on GitHub Pages.
3. Set the DNS records at the registrar:
   - Apex domain `skylolerr.dev`: four `A` records to `185.199.108.153`,
     `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (and optionally the `AAAA`
     records `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`,
     `2606:50c0:8003::153`).
   - `www.skylolerr.dev`: a `CNAME` record to `skylolerr.github.io`.
4. Switch the site and commit:

   ```bash
   python scripts/set_domain.py skylolerr.dev
   python scripts/check_site.py
   git add -A
   git commit -m "Move the site to skylolerr.dev"
   git push
   ```

   The script replaces the origin in every file and writes `CNAME`, which GitHub Pages
   reads as the custom domain.
5. On GitHub: **Settings → Pages → Custom domain** shows the domain from `CNAME`. Wait
   for the DNS check, then tick **Enforce HTTPS**.
6. `skylolerr.github.io` then redirects to the new domain. Add the new domain as a
   property in the Search Console and submit the sitemap again.

To go back, run `python scripts/set_domain.py skylolerr.github.io`; it removes `CNAME`.

## License

The content of this site © 2026 Skylolerr. The projects themselves are MIT-licensed in
their own repositories.

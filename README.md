# skylolerr.com

The project website of [Skylolerr](https://github.com/Skylolerr): Home Assistant
integrations installed with HACS. English at <https://skylolerr.com/>, German at
<https://skylolerr.com/de/>. Served by GitHub Pages from the repository
`Skylolerr/skylolerr.github.io` with the custom domain in `CNAME`.

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
| `assets/logo/` | The Skylolerr logo: SVG source and 1024 px PNG; `favicon.svg` is the same with rounded corners |
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

The canonical URL of every page is `https://skylolerr.com/…`, and `CNAME` contains
`skylolerr.com`. As soon as this repository is pushed, GitHub Pages uses that custom
domain and redirects `skylolerr.github.io` to it – so **set the DNS records first**,
otherwise the site cannot be reached until DNS works.

1. **DNS at the registrar** (Hostpoint) for `skylolerr.com`:
   - Remove any existing `A`/`AAAA` records of the domain itself (`@`) and of `www`
     (for example a parking page of the registrar).
   - Four `A` records for `@`: `185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153`.
   - Optional, four `AAAA` records for `@`: `2606:50c0:8000::153`,
     `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`.
   - A `CNAME` record for `www` pointing to `skylolerr.github.io`.
   - Recommended: verify the domain for the account first (GitHub → profile
     **Settings → Pages → Add a domain**), which asks for a `TXT` record
     `_github-pages-challenge-Skylolerr`. It stops other accounts from using the domain.
2. **Create the repository and push:**

   ```bash
   gh repo create Skylolerr/skylolerr.github.io --public --description "Project website of Skylolerr: Home Assistant integrations"
   git remote add origin https://github.com/Skylolerr/skylolerr.github.io.git
   git push -u origin main
   ```

3. **Pages settings** of the repository (**Settings → Pages**):
   - **Build and deployment → Source: Deploy from a branch**, branch **main**, folder
     **/ (root)**, **Save**.
   - **Custom domain** shows `skylolerr.com` (from `CNAME`); if not, enter it and
     **Save**. Wait until the DNS check is green.
   - Tick **Enforce HTTPS** once it can be ticked – GitHub needs a few minutes up to
     about a day to issue the certificate.
4. Check <https://skylolerr.com/>, <https://www.skylolerr.com/> and
   <https://skylolerr.github.io/> (both redirect to the first).
5. For search engines: add `skylolerr.com` to
   [Google Search Console](https://search.google.com/search-console) (domain property,
   verified with a `TXT` record) and [Bing Webmaster Tools](https://www.bing.com/webmasters)
   and submit `https://skylolerr.com/sitemap.xml`. Link the site from the project
   READMEs and the GitHub profile (website field).

## Changing the domain

All absolute URLs (canonical, hreflang, Open Graph, JSON-LD, sitemap, robots.txt) use
the origin in `CNAME`. Links between pages are root-relative (`/de/…`), so they work on
any domain. To move to another domain, or back to `skylolerr.github.io`:

```bash
python scripts/set_domain.py skylolerr.github.io   # removes CNAME
python scripts/check_site.py
```

## License

The content of this site © 2026 Skylolerr. The projects themselves are MIT-licensed in
their own repositories.

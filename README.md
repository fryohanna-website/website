# القمص يوحنا فؤاد ولسن — static site

A static rebuild of https://fryohanna.net/ (previously WordPress on Bluehost, Twenty Twenty child theme "fryohanna"). It is plain HTML, CSS and JS with no build step, so GitHub Pages serves it as it is.

- `index.html` and one `<path>/index.html` per page. Old URLs keep working, including the English pages under `en/` and the old `?p=<id>` shortlinks (the home page looks them up in `assets/shortlinks.json` and forwards).
- Each page keeps the theme's own CSS inline, exactly as WordPress served it, so the look is unchanged. `assets/css/site.css` only adds the lite YouTube player.
- `assets/js/` holds the original theme and plugin scripts (menus, accordions, the tribute sliders, the hymns video gallery, infinite scroll) plus `site.js` (YouTube players, shortlinks) and `config.js` (settings).
- `wp-content/uploads/` holds the images, at their old paths. Images that lived on Google Photos are copied into `wp-content/uploads/external/` so they no longer depend on Google links.
- `docs/inventory.md` lists what was on the old site and how each part was handled. `docs/compare/` has screenshots of the old and new site side by side.
- `tools/build.py` is the one-time converter from the crawl. The site does not need it.

Videos stay on YouTube (they were always YouTube embeds), so the repository is small.

## Preview locally

    python3 -m http.server 8000
    # open http://localhost:8000/

## Publish on GitHub Pages

1. Push this folder to `https://github.com/fryohanna-website/website` (branch `main`).
2. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main` / `(root)` → Save.**
3. The preview is then at https://fryohanna-website.github.io/website/

`.nojekyll` is included so Pages serves the files as they are. All links are relative, so the site works both under `/website/` and on its own domain.

## Moving the domain fryohanna.net to GitHub Pages

Do this only after the preview has been checked.

1. Add a file named `CNAME` at the root of the repository containing one line: `fryohanna.net`
2. On GitHub: **Settings → Pages → Custom domain** → `fryohanna.net` → Save. Wait for the DNS check, then tick **Enforce HTTPS**.
3. At the domain's DNS provider (where fryohanna.net is registered or its nameservers point; today the site is on Bluehost), delete the old A/AAAA records for the root and `www`, then add:

   | Type | Name | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | `fryohanna-website.github.io` |

   (Optional IPv6: AAAA records `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`.)

   Keep any MX (email) records as they are.
4. When the site answers on GitHub, the Bluehost WordPress can be switched off. Keep a backup of it first.

## Things that were WordPress-only

- **Push notifications (OneSignal), Google Analytics and Jetpack stats** are removed. If the church wants visitor numbers again, a privacy-friendly counter can be added with one script tag.
- **Photo gallery:** the gallery page pulled albums from Google Photos through the Photonic plugin. That stopped working on the old site too (Google closed the API), so the sections are empty on both. Send the photos and they can be added as a normal gallery.
- **Comments:** none were enabled on the old site; nothing was lost.
- **Contact:** the contact page links to Messenger and WhatsApp; there is no form. `assets/js/config.js` has a `FORMSPREE_ID` setting ready in case a form is wanted later.

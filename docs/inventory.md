# What was on fryohanna.net and how it was handled

Crawled 2026-10-11 from the live WordPress site (Bluehost, WordPress 7.1, Twenty Twenty child theme "fryohanna", Polylang for Arabic/English). The raw crawl and the WordPress REST API dumps are kept outside this repository in `../fryohanna-site-source/`.

## Pages (186)

| Section | Pages | Notes |
|---|---|---|
| Home `/` | 1 | Portrait, dates, link to the Anba Youlious tribute |
| `biography/` | 1 | Accordion sections work (original accordion script kept) |
| `media/` (sermons, liturgies, prayer meetings, hymns, misc) | 97 | Category pages, their `page/N/` pages and every post. Videos are YouTube embeds |
| `tribute/` (clergy, elders, family, parishioners, others) | 42 | Tribute posts. The clergy slider works (Owl Carousel kept) |
| `writings/` (devotions, booklets, discipleship curriculum) | 20 | Text posts |
| `tag/` | 21 | Tag archives |
| `photo-gallery/` | 1 | See "Photo gallery" below |
| `contact-us/` | 1 | Messenger and WhatsApp links (no form on the old site) |
| `en/` | 1 | English home page. The old English menu links (`/en/?page_id=58` etc.) were already 404 on the live site |
| `author/` | 1 | Author archive |

All 127 posts, 4 of 5 pages and every non-empty category from the WordPress API are present. Not built: `photo-gallery/album/` (an empty WordPress page) and the two empty categories `uncategorized/` and `en/english-sermons/`.

**Old shortlinks** (`https://fryohanna.net/?p=<id>`, 130 of them, the form Facebook shares often use) are kept working: the home page looks the id up in `assets/shortlinks.json` and forwards to the page.

## Media

- **Videos:** all on YouTube (WP YouTube Lyte players in posts, the Automatic YouTube Gallery on the hymns page). Nothing to host. The Lyte plugin script is replaced by a small player in `assets/js/site.js` (thumbnail first, YouTube loads on click). The hymns gallery keeps its original script.
- **Images:** 43 files, 4.1 MB, under `wp-content/uploads/` at their old paths. 37 of them (3.4 MB) were Google Photos links (directly or through the FIFU featured-image proxy); they are now copied into `wp-content/uploads/external/` so the site no longer depends on those Google links. Only the `og:image` social-preview tags still point at Google.
- **Audio / documents:** none on the site.
- **Files left out of the repository for size:** none. No file is over 1 MB; the whole site is about 35 MB including the comparison screenshots.

## Removed (WordPress-only or third-party)

| What | Why |
|---|---|
| Google Analytics (gtag), Jetpack stats | Tracking scripts; no server to report to. Can be re-added with one tag if wanted |
| OneSignal push notifications ("do you want notifications?" popup) | Needs the WordPress plugin and the OneSignal account |
| WordPress emoji script, speculation rules, Polylang language cookie, the "debloat" delay loader | WordPress runtime pieces with no use on a static site |
| Photonic gallery scripts (9 pages) | The galleries were already empty on the old site (Google closed the Photos API Photonic used) |
| `wp-json`, oEmbed, RSD, RSS, shortlink and canonical `<link>` tags, `generator` meta | Pointed at WordPress endpoints that will not exist |
| `<noscript>` fallbacks | Every page now works with the scripts kept locally |

The theme CSS is kept inline exactly as WordPress served it per page, so colors, fonts (IBM Plex Sans Arabic from Google Fonts) and layout are unchanged.

## Kept scripts (local copies in `assets/js/`)

jQuery 3.7.1 + migrate, the Twenty Twenty theme script (menus, mobile menu), the accordion block script, Owl Carousel 2.3.4 and its slider init (tribute pages), the Automatic YouTube Gallery scripts (hymns), YITH infinite scroll (category pages load the next page as you scroll; the page links also work without it).

## Spam or malware check

Every `<a>` link, `<script>` and inline script in all crawled pages was listed and checked, and the text was searched for the usual spam words (pharmacy, casino, adult, loans). **Nothing injected was found.** All outside links go to YouTube, wordpress.org (footer), Messenger and WhatsApp. Unlike the Damshiria site, this one looks clean.

## Decisions needed from the church

1. **Photo gallery:** the gallery page has 4 headed sections (before priesthood, ministry milestones, with other figures, the repose) that have been empty on the live site since Google closed the API. If the photos are sent, they can be added as a normal static gallery.
2. **English section:** only the English home page exists; its menu links were already broken on the old site. Keep it as is, or drop the English link?
3. **Statistics and notifications:** keep them off, or add a simple privacy-friendly visitor counter?
4. **Domain:** when the preview is approved, follow the README to point fryohanna.net at GitHub Pages, then switch off the Bluehost WordPress.

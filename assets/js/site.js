/* Static-site helpers. The rest of the behaviour (menus, accordions, the YouTube
   gallery, infinite scroll) is the original theme and plugin code in assets/js/. */
(function () {
  'use strict';

  /* Lite YouTube players (replaces the WP YouTube Lyte plugin): show the thumbnail,
     load the real player only when the visitor presses play. */
  function initLyte() {
    document.querySelectorAll('.lyMe').forEach(function (box) {
      var id = (box.id || '').replace(/^WYL_/, '');
      var pl = box.querySelector('.pL');
      if (!id || !pl || pl.dataset.ready) return;
      pl.dataset.ready = '1';
      var thumb = pl.getAttribute('data-src') || ('https://i.ytimg.com/vi/' + id + '/hqdefault.jpg');
      pl.style.backgroundImage = 'url("' + thumb + '")';
      pl.addEventListener('click', function () {
        var f = document.createElement('iframe');
        f.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0';
        f.title = box.querySelector('.tT') ? box.querySelector('.tT').textContent : 'YouTube';
        f.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen';
        f.allowFullscreen = true;
        f.className = 'lyte-frame';
        pl.replaceWith(f);
      });
    });
  }

  /* Contact form, if one is ever added: posts to Formspree when FORMSPREE_ID is set,
     otherwise opens the visitor's mail app. See assets/js/config.js. */
  function initForms() {
    var cfg = window.SITE_CONFIG || {};
    document.querySelectorAll('form[data-static-form]').forEach(function (form) {
      form.addEventListener('submit', function (ev) {
        if (cfg.FORMSPREE_ID) {
          form.action = 'https://formspree.io/f/' + cfg.FORMSPREE_ID;
          form.method = 'POST';
          return;
        }
        ev.preventDefault();
        var body = Array.prototype.map.call(form.elements, function (el) {
          return el.name ? el.name + ': ' + el.value : '';
        }).filter(Boolean).join('\n');
        window.location.href = 'mailto:' + (cfg.CONTACT_EMAIL || '') +
          '?subject=' + encodeURIComponent(document.title) + '&body=' + encodeURIComponent(body);
      });
    });
  }

  /* Old WordPress shortlinks (https://fryohanna.net/?p=123), still shared on Facebook:
     look the id up and go to the page. Only the home page receives these. */
  function followShortlink() {
    var m = /[?&](?:p|page_id)=(\d+)/.exec(window.location.search);
    if (!m) return;
    var base = document.querySelector('script[src$="assets/js/site.js"]').getAttribute('src')
      .replace(/assets\/js\/site\.js$/, '');
    fetch(base + 'assets/shortlinks.json').then(function (r) { return r.json(); }).then(function (map) {
      if (map[m[1]] !== undefined) window.location.replace(base + map[m[1]]);
    }).catch(function () {});
  }

  /* the theme calls ly.te() (the Lyte plugin's init) after infinite scroll adds posts */
  window.ly = window.ly || { te: initLyte };

  function init() { followShortlink(); initLyte(); initForms(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
  /* infinite scroll appends posts: wire up any new players */
  new MutationObserver(initLyte).observe(document.documentElement, { childList: true, subtree: true });
})();

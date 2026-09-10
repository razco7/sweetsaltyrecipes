/* Sweet / Salty — Main JavaScript */

/* ---- Path helper ---- */
const ROOT = document.documentElement.dataset.root || '.';
function p(path) { return ROOT + '/' + path; }

/* ---- Cookie consent (gates Google Analytics until accepted) ---- */
const GA_ID = 'G-61EPP7DCVE';
function loadAnalytics() {
  if (window.gaLoaded) return;
  window.gaLoaded = true;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', GA_ID);
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  document.head.appendChild(script);
}

function showCookieBanner() {
  const existing = document.querySelector('.cookie-banner');
  if (existing) return;
  const banner = document.createElement('div');
  banner.className = 'cookie-banner';
  banner.innerHTML = `
    <div class="cookie-banner-header">
      <span class="cookie-banner-icon" aria-hidden="true">🍪</span>
      <p>Yes, a baking site with a cookie banner. These ones just count which recipes get opened.</p>
    </div>
    <div class="cookie-banner-actions">
      <button class="cookie-btn cookie-decline">Decline</button>
      <button class="cookie-btn cookie-accept">Accept</button>
    </div>
  `;
  document.body.appendChild(banner);
  banner.querySelector('.cookie-accept').addEventListener('click', () => {
    localStorage.setItem('cookieConsent', 'accepted');
    loadAnalytics();
    banner.remove();
  });
  banner.querySelector('.cookie-decline').addEventListener('click', () => {
    localStorage.setItem('cookieConsent', 'declined');
    banner.remove();
  });
}

const cookieConsent = localStorage.getItem('cookieConsent');
if (cookieConsent === 'accepted') {
  loadAnalytics();
} else if (cookieConsent !== 'declined') {
  showCookieBanner();
}

// Persistent way to revisit the choice later, injected into every footer.
document.querySelectorAll('.footer-copyright').forEach(copyright => {
  copyright.append(' · ');
  const link = document.createElement('a');
  link.href = '#';
  link.className = 'cookie-preferences-link';
  link.textContent = 'Cookie preferences';
  link.addEventListener('click', e => {
    e.preventDefault();
    showCookieBanner();
  });
  copyright.appendChild(link);
});

/* ---- Recipe data ---- */
const ALL_RECIPES = [
  { title: "Savory Syrian Ka'ak", img: 'images/savory-syrian-kaak.jpg', desc: "Aleppo's crunchy sesame rings, warm with mahleb and spice", tags: ['Cookie','Middle East','Salty','Moderate'], page: 'recipe-pages/savory-syrian-kaak.html', popular: false },
  { title: 'Biscotti', img: 'images/biscotti.jpg', desc: 'Crunchy twice-baked Tuscan cookies, made for dunking', tags: ['Cookie','Italy','Sweet','Moderate'], page: 'recipe-pages/biscotti.html', popular: false },
  { title: 'Italian S Cookies', img: 'images/italian-s-cookies.jpg', desc: 'S-shaped Italian butter cookies, scented with lemon zest', tags: ['Cookie','Italy','Sweet','Easy'], page: 'recipe-pages/italian-s-cookies.html', popular: false, date: '2026-07-01' },
  { title: 'Muhallebi', img: 'images/muhallebi.jpg', desc: 'Silky Middle Eastern milk pudding with nuts and syrup', tags: ['Dessert','Middle East','Sweet','Easy'], page: 'recipe-pages/muhallebi.html', popular: false },
  { title: 'Crêpes', img: 'images/crepe.jpg', desc: 'Thin, lacy pancakes from Brittany, sweet or savory', tags: ['Breakfast','France','Sweet','Easy'], page: 'recipe-pages/crepe.html', popular: false },
  { title: 'Chocolate Soufflé', img: 'images/chocolate-souffle.jpg', desc: 'Flourless and barely set, sinking as it leaves the oven', tags: ['Pastry','France','Sweet','Moderate'], page: 'recipe-pages/chocolate-souffle.html', popular: false },
  { title: 'Cupcakes', img: 'images/cupcake.jpg', desc: 'Small single-serve cakes under a swirl of frosting', tags: ['Pastry','USA','Sweet','Moderate'], page: 'recipe-pages/cupcake.html', popular: false },
  { title: 'Sablé Cookies', img: 'images/sable-cookies.jpg', desc: 'Crisp, sandy French butter cookies with a sugared edge', tags: ['Cookie','France','Sweet','Easy'], page: 'recipe-pages/sable-cookies.html', popular: false },
  { title: 'French Macarons', img: 'images/french-macarons.jpg', desc: 'Almond-meringue shells with ruffled feet and buttercream', tags: ['Pastry','France','Sweet','Hard'], page: 'recipe-pages/french-macarons.html', popular: false },
  { title: 'Danish Butter Cookies', img: 'images/danish-butter-cookies.jpg', desc: 'Piped rings from the blue tin — pale gold, and they snap', tags: ['Cookie','Denmark','Sweet','Easy'], page: 'recipe-pages/danish-butter-cookies.html', popular: false },
  { title: 'Chocolate Chip Cookies', img: 'images/chocolate-chip-cookies.jpg', desc: 'Melted butter and brown sugar, built for chew over cake', tags: ['Cookie','USA','Sweet','Easy'], page: 'recipe-pages/chocolate-chip-cookies.html', popular: true },
  { title: 'Apple Strudel', img: 'images/apple-strudel.jpg', desc: 'Spiced apples and raisins in paper-thin Viennese pastry', tags: ['Pastry','Austria','Sweet','Moderate'], page: 'recipe-pages/apple-strudel.html', popular: true },
  { title: 'Gingerbread Cookies', img: 'images/gingerbread-cookies.jpg', desc: 'Molasses dough spiced with ginger and cloves, cut to shape', tags: ['Cookie','Germany','Sweet','Easy'], page: 'recipe-pages/gingerbread-cookies.html', popular: false },
  { title: 'French Toast', img: 'images/french-toast.jpg', desc: 'Custard-soaked bread, fried crisp outside and tender within', tags: ['Breakfast','France','Sweet','Easy'], page: 'recipe-pages/french-toast.html', popular: true },
  { title: 'Pizza', img: 'images/pizza.jpg', desc: 'A blistered Naples crust with tomato and fresh mozzarella', tags: ['Pastry','Italy','Salty','Easy'], page: 'recipe-pages/pizza.html', popular: true },
  { title: 'New York Cheesecake', img: 'images/new-york-cheesecake.jpg', desc: 'Tall and dense, baked low in a water bath so it never cracks', tags: ['Cake','USA','Sweet','Moderate'], page: 'recipe-pages/new-york-cheesecake.html', popular: false },
  { title: 'Croissants', img: 'images/croissant.jpg', desc: 'Three folds, three chills, and a hundred layers of butter', tags: ['Pastry','France','Sweet','Moderate'], page: 'recipe-pages/croissant.html', popular: false },
  { title: 'Vanillekipferl', img: 'images/vanillekipferl.jpg', desc: 'Almond-shortbread crescents rolled warm in vanilla sugar', tags: ['Cookie','Austria','Sweet','Moderate'], page: 'recipe-pages/vanillekipferl.html', popular: false, date: '2026-08-29' },
  { title: 'Gevulde Koek', img: 'images/gevulde-koek.jpg', desc: 'Dutch shortcrust cookies filled with sweet almond paste', tags: ['Cookie','Netherlands','Sweet','Moderate'], page: 'recipe-pages/gevulde-koek.html', popular: false, date: '2026-09-08' },
  { title: 'Sachertorte', img: 'images/sachertorte.jpg', desc: "Dense Viennese chocolate cake, apricot jam, dark glaze", tags: ['Cake','Austria','Sweet','Hard'], page: 'recipe-pages/sachertorte.html', popular: false, date: '2026-09-09' },
];

const TAG_LINKS = {
  'Cookie': 'collection-pages/cookie-recipes.html',
  'Pastry': 'collection-pages/pastry-recipes.html',
  'Cake': 'collection-pages/sweet-recipes.html',
  'Dessert': 'collection-pages/sweet-recipes.html',
  'Breakfast': 'collection-pages/breakfast-recipes.html',
  'France': 'collection-pages/france-recipes.html',
  'Italy': 'collection-pages/italy-recipes.html',
  'Germany': 'collection-pages/germany-recipes.html',
  'Denmark': 'collection-pages/denmark-recipes.html',
  'USA': 'collection-pages/usa-recipes.html',
  'Austria': 'collection-pages/austria-recipes.html',
  'Netherlands': 'collection-pages/netherlands-recipes.html',
  'Middle East': 'collection-pages/middle-east-recipes.html',
  'Sweet': 'collection-pages/sweet-recipes.html',
  'Salty': 'collection-pages/salty-recipes.html',
  'Easy': 'collection-pages/easy-level-recipes.html',
  'Moderate': 'collection-pages/moderate-level-recipes.html',
  'Hard': 'collection-pages/hard-level-recipes.html',
};

/* ---- Recipe grid rendering (collection & all-recipes pages) ---- */
const NEW_BADGE_DAYS = 7;
function isNewRecipe(r) {
  if (!r.date) return false;
  const daysSince = (Date.now() - new Date(r.date + 'T00:00:00')) / 86400000;
  return daysSince >= 0 && daysSince <= NEW_BADGE_DAYS;
}

function recipeCardHTML(r) {
  const href = r.page ? p(r.page) : '#';
  const popularBadge = r.popular ? '<span class="badge-popular">Popular Recipe</span>' : '';
  const newBadge = isNewRecipe(r) ? '<span class="badge-new">New!</span>' : '';
  const tags = r.tags.map(t => `<a href="${p(TAG_LINKS[t] || 'all-recipes.html')}" class="tag">${t}</a>`).join('');
  const imgTag = `<img src="${p(r.img)}" alt="${r.title}" loading="lazy" width="800" height="800">`;
  const imgWrap = r.page
    ? `<a href="${href}" class="recipe-card-img">${popularBadge}${newBadge}${imgTag}</a>`
    : `<div class="recipe-card-img">${popularBadge}${newBadge}${imgTag}</div>`;
  const titleHTML = r.page ? `<a href="${href}">${r.title}</a>` : r.title;
  return `
    <article class="recipe-card">
      ${imgWrap}
      <div class="recipe-card-body">
        <h3>${titleHTML}</h3>
        <p>${r.desc}</p>
        <div class="recipe-tags">${tags}</div>
      </div>
    </article>`;
}

document.querySelectorAll('.recipe-grid[data-tag]').forEach(grid => {
  const tag = grid.dataset.tag;
  const list = (tag === 'All' ? ALL_RECIPES.slice() : ALL_RECIPES.filter(r => r.tags.includes(tag)));
  // New recipes float to the top, most recent first; everything else keeps its original order.
  list.sort((a, b) => {
    const aNew = isNewRecipe(a), bNew = isNewRecipe(b);
    if (aNew && bNew) return new Date(b.date) - new Date(a.date);
    if (aNew) return -1;
    if (bNew) return 1;
    return 0;
  });
  grid.innerHTML = list.map(recipeCardHTML).join('');
});

/* ---- Search ---- */
const searchBtn = document.getElementById('searchBtn');
const searchOverlay = document.getElementById('searchOverlay');
const searchClose = document.getElementById('searchClose');
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

function openSearch() {
  searchOverlay.classList.add('active');
  searchInput.focus();
  renderSearch('');
}
function closeSearch() {
  searchOverlay.classList.remove('active');
  searchInput.value = '';
}

if (searchBtn) searchBtn.addEventListener('click', openSearch);
if (searchClose) searchClose.addEventListener('click', closeSearch);
if (searchOverlay) {
  searchOverlay.addEventListener('click', e => { if (e.target === searchOverlay) closeSearch(); });
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSearch(); });

function renderSearch(query) {
  const q = query.toLowerCase().trim();
  const matches = q === '' ? ALL_RECIPES : ALL_RECIPES.filter(r =>
    r.title.toLowerCase().includes(q) ||
    r.tags.some(t => t.toLowerCase().includes(q)) ||
    r.desc.toLowerCase().includes(q)
  );
  if (matches.length === 0) {
    searchResults.innerHTML = '<div class="search-empty">No recipes found for "' + query + '"</div>';
    return;
  }
  searchResults.innerHTML = matches.map(r => {
    const href = r.page ? p(r.page) : '#';
    return `
      <a class="search-result-item" href="${href}">
        <img src="${p(r.img)}" alt="${r.title}">
        <div class="result-info">
          <strong>${r.title}</strong>
          <span class="result-tags">${r.tags.join(' · ')}</span>
        </div>
      </a>`;
  }).join('');
}

if (searchInput) {
  searchInput.addEventListener('input', e => renderSearch(e.target.value));
}

/* ---- Mobile nav ---- */
const navToggle = document.getElementById('navToggle');
const mobileNav = document.getElementById('mobileNav');
if (navToggle && mobileNav) {
  navToggle.addEventListener('click', () => mobileNav.classList.toggle('open'));
}

const mobileDropdownLabel = document.querySelector('.mobile-nav .mobile-dropdown-label');
if (mobileDropdownLabel) {
  mobileDropdownLabel.addEventListener('click', () => {
    mobileDropdownLabel.classList.toggle('open');
    mobileDropdownLabel.nextElementSibling.classList.toggle('open');
  });
}

/* ---- Hero rotating text (mover approach, mirrors Webflow) ---- */
const wordMover = document.querySelector('.word-mover');
if (wordMover) {
  const slots = wordMover.querySelectorAll('.rotating-word');
  const wordBox = wordMover.closest('.word-box');
  const ease = 'cubic-bezier(0.4, 0, 0.2, 1)';
  const dur = 380;
  let current = 0;

  // CSS already sets an approximate word-box height so the first word paints
  // immediately with no JS dependency (better LCP). Use getBoundingClientRect
  // here for sub-pixel accuracy — offsetHeight rounds to integers which
  // causes 1-2px bleed from the previous word at the top — and correct the
  // CSS value now that the font has actually loaded and laid out.
  const gap = 8;
  const slotH = slots[0].getBoundingClientRect().height;
  const step = slotH + gap;
  wordBox.style.height = slotH + 'px';

  setInterval(() => {
    current++;

    wordMover.style.transition = `transform ${dur}ms ${ease}`;
    wordMover.style.transform = `translateY(-${current * step}px)`;

    // Last slot is a duplicate of the first — snap back silently after it lands
    if (current === slots.length - 1) {
      setTimeout(() => {
        wordMover.style.transition = 'none';
        wordMover.style.transform = 'translateY(0)';
        current = 0;
      }, dur + 60);
    }
  }, 2600);
}

/* ---- Newsletter forms ---- */
document.querySelectorAll('.newsletter-form').forEach(form => {
  form.addEventListener('submit', e => {
    e.preventDefault();
    const success = form.parentElement.querySelector('.newsletter-success');
    if (success) { success.classList.add('show'); form.style.display = 'none'; }
  });
});

/* ---- Auto-update copyright year ---- */
const yearEl = document.getElementById('copyright-year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

/* ---- Recipe interactive checkboxes ---- */
document.querySelectorAll('.ingredients-list li').forEach(li => {
  const cb = document.createElement('input');
  cb.type = 'checkbox';
  cb.className = 'recipe-check';
  li.prepend(cb);
  cb.addEventListener('change', () => li.classList.toggle('checked', cb.checked));
  li.addEventListener('click', e => {
    if (e.target === cb) return;
    cb.checked = !cb.checked;
    li.classList.toggle('checked', cb.checked);
  });
});

document.querySelectorAll('.instructions-list li').forEach(li => {
  li.addEventListener('click', e => {
    if (e.target.tagName === 'A') return;
    li.classList.toggle('checked');
  });
});

/* ---- Contact form (Formspree) ---- */
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = contactForm.querySelector('.btn-submit');
    const successEl = document.getElementById('formSuccess');
    const errorEl = document.getElementById('formError');
    btn.disabled = true;
    btn.textContent = 'Sending…';
    try {
      const res = await fetch('https://formspree.io/f/xvzjogvk', {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: new FormData(contactForm)
      });
      if (res.ok) {
        contactForm.style.display = 'none';
        if (successEl) successEl.classList.add('show');
      } else {
        if (errorEl) errorEl.classList.add('show');
        btn.disabled = false;
        btn.textContent = 'Send message';
      }
    } catch {
      if (errorEl) errorEl.classList.add('show');
      btn.disabled = false;
      btn.textContent = 'Send message';
    }
  });
}

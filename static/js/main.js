/**
 * AaramKart — Main UI (nav, login modal, toasts)
 */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/** Password visibility toggle (login modal + any page) */
window.togglePassword = function (inputId) {
    const el = document.getElementById(inputId);
    if (!el) return;
    el.type = el.type === 'password' ? 'text' : 'password';
};

function initLoginModal() {
    const paramsBoot = new URLSearchParams(window.location.search);
    if (paramsBoot.get('open_login') === '1') {
        const next = paramsBoot.get('next');
        const dest = new URL('/auth/login/', window.location.origin);
        if (next) dest.searchParams.set('next', next);
        window.location.replace(dest.pathname + dest.search + (window.location.hash || ''));
        return;
    }

    const modal = document.getElementById('login-modal');
    if (!modal) return;

    const setNextFields = (path) => {
        let v = path && path.startsWith('/') ? path : '/';
        if (v.includes('open_login=')) v = '/';
        modal.querySelectorAll('.login-modal-next').forEach((inp) => {
            inp.value = v;
        });
    };

    const openModal = (nextPath) => {
        let n = nextPath;
        if (n == null || n === '') {
            n = window.location.pathname;
            if (window.location.search && !window.location.search.includes('open_login')) {
                n += window.location.search;
            }
        }
        if (!n || n === '') n = '/';
        if (String(n).includes('open_login')) n = '/';
        setNextFields(n);

        modal.removeAttribute('hidden');
        modal.classList.add('login-modal--open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('login-modal-open');

        const firstInput = modal.querySelector('input[type="tel"], input[type="email"], input[type="password"]');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 50);
        }
    };

    const closeModal = () => {
        modal.setAttribute('hidden', '');
        modal.classList.remove('login-modal--open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('login-modal-open');
    };

    document.querySelectorAll('.nav-login-trigger').forEach((el) => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            const next = el.getAttribute('data-login-next');
            openModal(next != null && next !== '' ? next : undefined);
        });
    });

    document.querySelectorAll('.js-login-modal-close').forEach((el) => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            closeModal();
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('login-modal--open')) {
            closeModal();
        }
    });
}

function initAdminSidebar() {
    const shell = document.getElementById('admin-app-shell');
    if (!shell) return;

    const toggle = document.getElementById('admin-sidebar-toggle');
    const backdrop = document.getElementById('admin-sidebar-backdrop');
    const sidebar = document.getElementById('admin-sidebar');
    const mq = window.matchMedia('(max-width: 900px)');

    const setOpen = (open) => {
        shell.classList.toggle('admin-app-shell--nav-open', open);
        if (toggle) {
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            toggle.setAttribute('aria-label', open ? 'Close admin menu' : 'Open admin menu');
        }
        if (backdrop) backdrop.setAttribute('aria-hidden', open ? 'false' : 'true');
        if (mq.matches && open) document.body.style.overflow = 'hidden';
        else document.body.style.overflow = '';
    };

    const close = () => {
        if (mq.matches) setOpen(false);
    };

    toggle?.addEventListener('click', () => {
        setOpen(!shell.classList.contains('admin-app-shell--nav-open'));
    });

    backdrop?.addEventListener('click', close);

    sidebar?.querySelectorAll('a.admin-sidebar__link').forEach((a) => {
        a.addEventListener('click', () => close());
    });

    mq.addEventListener('change', () => {
        if (!mq.matches) setOpen(false);
    });
}

function initCategorySlider() {
    document.querySelectorAll('.cat-slider-wrap').forEach((wrap) => {
        const track = wrap.querySelector('.cat-slider-track');
        const lane = track?.querySelector('.cat-grid-idea');
        if (!track || !lane) return;

        const prevBtn = wrap.querySelector('.cat-slider-arrow--left');
        const nextBtn = wrap.querySelector('.cat-slider-arrow--right');
        const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const stepPx = 220;
        let offset = 0;
        let laneWidth = lane.scrollWidth;

        const normalize = () => {
            while (offset <= -laneWidth) offset += laneWidth;
            while (offset > 0) offset -= laneWidth;
        };

        const render = () => {
            track.style.transform = `translate3d(${offset}px, 0, 0)`;
        };

        const updateLaneWidth = () => {
            laneWidth = lane.scrollWidth;
            if (!laneWidth) laneWidth = 1;
            normalize();
            render();
        };

        const tick = () => {
            offset -= 0.45;
            normalize();
            render();
            window.requestAnimationFrame(tick);
        };

        const nudge = (delta) => {
            offset += delta;
            normalize();
            render();
        };

        updateLaneWidth();
        window.addEventListener('resize', updateLaneWidth);

        prevBtn?.addEventListener('click', () => nudge(stepPx));
        nextBtn?.addEventListener('click', () => nudge(-stepPx));
        if (!prefersReduced) {
            tick();
        }
    });
}

function initConversionTrustSection() {
    const sellingTrack = document.getElementById('most-selling-track');
    const sellingCarousel = document.getElementById('most-selling-carousel');
    const reviewsGrid = document.getElementById('trusted-reviews-grid');
    if (!sellingTrack || !sellingCarousel || !reviewsGrid) return;

    const leftArrow = document.querySelector('.most-selling-arrow--left');
    const rightArrow = document.querySelector('.most-selling-arrow--right');

    const sellingFallback = [
        { product_name: 'Dettol Antiseptic Liquid 500ml', wholesale_price: 198, discount_percentage: 12, stock_status: 'In Stock', image: 'https://images.unsplash.com/photo-1585435557343-3b092031a831?w=640&q=80' },
        { product_name: 'Surf Excel Detergent 1kg', wholesale_price: 162, discount_percentage: 10, stock_status: 'In Stock', image: 'https://images.unsplash.com/photo-1610557892470-55d9e80c0bce?w=640&q=80' },
        { product_name: 'Dove Shampoo Intense Repair', wholesale_price: 276, discount_percentage: 15, stock_status: 'Low Stock', image: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=640&q=80' },
        { product_name: 'Colgate Dental Cream Value Pack', wholesale_price: 240, discount_percentage: 9, stock_status: 'In Stock', image: 'https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=640&q=80' },
        { product_name: 'Amul Butter 500g', wholesale_price: 252, discount_percentage: 7, stock_status: 'Out of Stock', image: 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=640&q=80' },
    ];

    const reviewData = [
        {
            store: 'Mawlai General Store',
            locality: 'Mawlai',
            quote: 'Best margins on Personal Care items. My stock reaches Mawlai within 4 hours. Truly Aaram for my business!',
        },
        {
            store: 'Bara Bazar Distributor',
            locality: 'Iewduh (Bara Bazar)',
            quote: 'Finally a wholesale app that understands Shillong traffic. Delivery is always early, and the Household Essentials are 100% genuine.',
        },
        {
            store: 'Laitumkhrah Retail Hub',
            locality: 'Laitumkhrah',
            quote: 'Consistent pricing, verified stock, and quick support. It has made repeat ordering very smooth for our counters.',
        },
        {
            store: 'Police Bazar Mini Mart',
            locality: 'Police Bazar',
            quote: 'Our top-selling grocery lines are always available. The app saves me daily sourcing time.',
        },
        {
            store: 'Nongthymmai Traders',
            locality: 'Nongthymmai',
            quote: 'Bulk household essentials arrive packed well and on-time. Margins are steady every week.',
        },
        {
            store: 'Iewduh Value Store',
            locality: 'Iewduh',
            quote: 'Trusted quality and easy repeat orders. AaramKart has improved my stock planning a lot.',
        },
    ];

    const stockClass = (status) => {
        const s = String(status || '').toLowerCase();
        if (s.includes('low')) return 'low-stock';
        if (s.includes('out')) return 'out-of-stock';
        return 'in-stock';
    };

    const originalPacketPrice = (item) => {
        const explicit = Number(item.original_packet_price || 0);
        if (explicit > 0) return explicit;
        const singleMrp = Number(item.single_product_price || 0);
        const packQty = Number(item.pack_quantity || 0);
        if (singleMrp > 0 && packQty > 0) return singleMrp * packQty;
        return Number(item.wholesale_price || 0);
    };

    const renderSellingCards = (items) => {
        sellingTrack.innerHTML = items.map((item) => {
            const originalPacket = originalPacketPrice(item);
            const pid = item.product_id != null ? Number(item.product_id) : 0;
            const disabled = !pid;
            const href = pid ? `/product/${pid}/` : '#';
            const vid =
                item.default_variant_id != null && item.default_variant_id !== ''
                    ? Number(item.default_variant_id)
                    : '';
            const variantAttr =
                Number.isFinite(vid) && vid > 0 ? ` data-variant-id="${vid}"` : '';
            return `
            <article class="most-selling-card js-most-selling-card${disabled ? ' is-disabled' : ''}"
              tabindex="${disabled ? '-1' : '0'}"
              role="group"
              aria-label="${String(item.product_name || 'Product').replace(/"/g, '&quot;')}"
              data-product-href="${href}"
              ${disabled ? 'aria-disabled="true"' : ''}>
              <div class="most-selling-img-wrap">
                <span class="trending-badge">🔥 Trending</span>
                <img src="${item.image || ''}" alt="${item.product_name}" loading="lazy" />
              </div>
              <div class="most-selling-body">
                <h3 class="most-selling-name">${item.product_name}</h3>
                <div class="most-selling-tabs">
                  <span class="most-selling-tab">${item.category || 'General'}</span>
                  <span class="most-selling-tab">${item.subcategory || 'Popular'}</span>
                </div>
                <p class="most-selling-price">₹${item.packet_price || item.wholesale_price}</p>
                ${item.packet_price ? `<p class="most-selling-price-note">per packet</p>` : ''}
                ${(item.discount_percentage || 0) > 0 ? `<p class="most-selling-price-strike">Original Packet Price <span>₹${originalPacket}</span></p>` : ''}
                <p class="most-selling-volume">${item.quantity_sold || 0} sold</p>
                <div class="most-selling-meta">
                  <span class="discount-chip">${item.discount_percentage || 0}% OFF</span>
                  <span class="stock-pill ${stockClass(item.stock_status)}">${item.stock_status || 'In Stock'}</span>
                </div>
                <button type="button" class="most-selling-add-btn js-most-selling-add" data-product-id="${pid || ''}" data-moq="${item.moq || 1}" data-pack-qty="${item.pack_quantity || 0}" data-stock="${item.stock || 0}"${variantAttr}>
                  Add to Cart
                </button>
              </div>
            </article>
        `;
        }).join('');
    };

    const renderSellingSkeleton = () => {
        sellingTrack.innerHTML = Array.from({ length: 4 }).map(() => `
            <article class="most-selling-card skeleton-card">
              <div class="most-selling-img-wrap"><div class="skeleton-box" style="width:100%;height:100%"></div></div>
              <div class="most-selling-body">
                <div class="skeleton-line" style="width:90%"></div>
                <div class="skeleton-line" style="width:58%"></div>
                <div class="skeleton-line" style="width:76%;margin-top:0.6rem"></div>
              </div>
            </article>
        `).join('');
    };

    const renderReviews = (items) => {
        reviewsGrid.innerHTML = items.map((item) => `
            <article class="trusted-review-card">
              <div class="trusted-review-top">
                <h3 class="trusted-review-store">${item.store}</h3>
                <span class="verified-pill">Verified Purchase</span>
              </div>
              <p class="trusted-review-locality">${item.locality}</p>
              <p class="trusted-review-stars">★★★★★</p>
              <p class="trusted-review-quote">${item.quote}</p>
            </article>
        `).join('');
    };

    const startReviewSlider = () => {
        const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReduced) return;

        const originals = Array.from(reviewsGrid.children);
        if (!originals.length) return;
        originals.forEach((card) => {
            const clone = card.cloneNode(true);
            clone.setAttribute('aria-hidden', 'true');
            reviewsGrid.appendChild(clone);
        });

        let offset = 0;
        let laneWidth = originals.reduce((acc, card) => acc + card.getBoundingClientRect().width, 0);
        const styles = window.getComputedStyle(reviewsGrid);
        const gap = parseFloat(styles.columnGap || styles.gap || '0') || 0;
        laneWidth += gap * Math.max(0, originals.length - 1);

        const tick = () => {
            offset -= 0.28;
            if (Math.abs(offset) >= laneWidth) offset = 0;
            reviewsGrid.style.transform = `translate3d(${offset}px,0,0)`;
            window.requestAnimationFrame(tick);
        };
        tick();
    };

    const renderReviewSkeleton = () => {
        reviewsGrid.innerHTML = Array.from({ length: 3 }).map(() => `
            <article class="trusted-review-card skeleton-card">
              <div class="skeleton-line" style="width:52%"></div>
              <div class="skeleton-line" style="width:38%;margin-top:0.55rem"></div>
              <div class="skeleton-line" style="width:30%;margin-top:0.55rem"></div>
              <div class="skeleton-line" style="width:96%;margin-top:0.7rem"></div>
              <div class="skeleton-line" style="width:86%"></div>
            </article>
        `).join('');
    };

    const mapApiProduct = (p) => ({
        product_id: p.product_id ?? p.id ?? null,
        default_variant_id: p.default_variant_id ?? null,
        product_name: p.product_name || p.name || 'AaramKart Bestseller',
        wholesale_price: p.wholesale_price ?? p.base_price ?? p.price ?? 0,
        packet_price: p.packet_price ?? null,
        single_product_price: p.single_product_price ?? p.wholesale_price ?? p.base_price ?? p.price ?? 0,
        original_packet_price: p.original_packet_price ?? null,
        discount_percentage: p.discount_percentage ?? p.discount ?? 0,
        stock_status: p.stock_status || ((p.stock ?? 1) > 10 ? 'In Stock' : (p.stock > 0 ? 'Low Stock' : 'Out of Stock')),
        image: p.image || p.image_url || '',
        quantity_sold: p.quantity_sold ?? 0,
        moq: p.moq ?? 1,
        pack_quantity: p.pack_quantity ?? 0,
        stock: p.stock ?? 0,
        category: p.category || '',
        subcategory: p.subcategory || '',
    });

    const loadSelling = async () => {
        try {
            const res = await fetch('/api/products/most-selling/?limit=10', { credentials: 'same-origin' });
            if (!res.ok) throw new Error('products fetch failed');
            const data = await res.json();
            const raw = Array.isArray(data) ? data : (data.results || data.products || []);
            const normalized = raw.map(mapApiProduct).filter((x) => x.product_name);
            renderSellingCards(normalized.length ? normalized : sellingFallback);
        } catch {
            renderSellingCards(sellingFallback);
        }
    };

    const step = 260;
    leftArrow?.addEventListener('click', () => sellingCarousel.scrollBy({ left: -step, behavior: 'smooth' }));
    rightArrow?.addEventListener('click', () => sellingCarousel.scrollBy({ left: step, behavior: 'smooth' }));

    sellingTrack.addEventListener('click', async (e) => {
        const btn = e.target.closest('.js-most-selling-add');
        if (btn) {
            e.preventDefault();
            e.stopPropagation();
            if (document.body.dataset.auth !== '1') {
                window.location.href =
                    '/auth/login/?next=' +
                    encodeURIComponent(window.location.pathname + window.location.search);
                return;
            }
            const productId = Number(btn.dataset.productId || 0);
            const variantId = Number(btn.dataset.variantId || 0);
            const moq = Number(btn.dataset.moq || 1);
            const packQty = Number(btn.dataset.packQty || 0);
            const stock = Number(btn.dataset.stock || 0);
            if (!productId || stock <= 0) {
                showToast('Out of stock.', 'error');
                return;
            }
            const qty = packQty > 0 ? 1 : moq;
            const payload = { product_id: productId, quantity: qty };
            if (Number.isFinite(variantId) && variantId > 0) {
                payload.variant_id = variantId;
            }
            btn.disabled = true;
            btn.textContent = 'Adding...';
            try {
                const res = await fetch('/orders/cart/add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') || '',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(payload),
                });
                const data = await res.json();
                if (!res.ok || !data.success) {
                    showToast(data.error || 'Could not add to cart', 'error');
                } else {
                    const badge = document.querySelector('.cart-count-badge');
                    const totalEl = document
                        .querySelector('.cart-count-badge')
                        ?.closest('.cart-meta-item')
                        ?.querySelector('.meta-value');
                    if (badge && data.cart_count != null) badge.textContent = String(data.cart_count);
                    if (totalEl && data.cart_total != null) {
                        totalEl.textContent = `₹${Number(data.cart_total).toFixed(2)}`;
                    }
                    showToast('Added to cart', 'success');
                }
            } catch {
                showToast('Network error', 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Add to Cart';
            }
            return;
        }
        const card = e.target.closest('.js-most-selling-card');
        if (!card || card.classList.contains('is-disabled')) return;
        const href = card.getAttribute('data-product-href');
        if (!href || href === '#') return;
        window.location.assign(href);
    });

    sellingTrack.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        const card = e.target.closest('.js-most-selling-card');
        if (!card || card.classList.contains('is-disabled')) return;
        if (e.target.closest('.js-most-selling-add')) return;
        const href = card.getAttribute('data-product-href');
        if (!href || href === '#') return;
        e.preventDefault();
        window.location.assign(href);
    });

    renderSellingSkeleton();
    renderReviewSkeleton();

    window.setTimeout(() => {
        renderReviews(reviewData);
        startReviewSlider();
        loadSelling();
        window.setInterval(loadSelling, 60000);
    }, 420);
}

const AK_SCROLL_TO_REFINE_KEY = 'akScrollToSubSub';

function wireCategoryRefineScrollIntent() {
    document.body.addEventListener(
        'click',
        (e) => {
            const a = e.target.closest('a[data-scroll-to-refine]');
            if (!a || !a.getAttribute('href')) return;
            if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
            if (a.target === '_blank' || a.getAttribute('download')) return;
            try {
                sessionStorage.setItem(AK_SCROLL_TO_REFINE_KEY, '1');
            } catch (_) {
                /* private mode */
            }
        },
        true
    );
}

function categoryPageStickyHeaderOffset() {
    const nav = document.querySelector('.navbar-main');
    if (!nav) return 20;
    return Math.ceil(nav.getBoundingClientRect().height) + 12;
}

function smoothScrollToDocumentY(targetY, durationMs, onDone) {
    const startY = window.scrollY;
    const delta = targetY - startY;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion || durationMs <= 0 || Math.abs(delta) < 2) {
        window.scrollTo(0, targetY);
        if (typeof onDone === 'function') requestAnimationFrame(onDone);
        return;
    }
    const t0 = performance.now();
    const easeInOutCubic = (t) =>
        t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    function tick(now) {
        const t = Math.min(1, (now - t0) / durationMs);
        const y = startY + delta * easeInOutCubic(t);
        window.scrollTo(0, y);
        if (t < 1) {
            requestAnimationFrame(tick);
        } else if (typeof onDone === 'function') {
            onDone();
        }
    }
    requestAnimationFrame(tick);
}

function initCategoryRefineAutoScroll() {
    const el = document.getElementById('sub-sub-grid');
    if (!el) return;

    let shouldScroll = false;
    try {
        shouldScroll = sessionStorage.getItem(AK_SCROLL_TO_REFINE_KEY) === '1';
        if (shouldScroll) sessionStorage.removeItem(AK_SCROLL_TO_REFINE_KEY);
    } catch (_) {}

    if (!shouldScroll) return;

    const run = () => {
        const pad = categoryPageStickyHeaderOffset();
        const rect = el.getBoundingClientRect();
        const y = Math.max(0, rect.top + window.scrollY - pad);
        const duration = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 520;
        smoothScrollToDocumentY(y, duration, () => {
            try {
                el.focus({ preventScroll: true });
            } catch (_) {
                /* older browsers */
            }
            el.classList.add('category-refine--pulse');
            window.setTimeout(() => el.classList.remove('category-refine--pulse'), 1150);
        });
    };

    requestAnimationFrame(() => requestAnimationFrame(run));
}

document.addEventListener('DOMContentLoaded', () => {
    wireCategoryRefineScrollIntent();
    // ── DROPDOWNS (optional legacy ids) ──
    const userBtn = document.getElementById('nav-user-btn');
    const userDropdown = document.getElementById('nav-dropdown');

    if (userBtn && userDropdown) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });

        document.addEventListener('click', () => {
            userDropdown.classList.remove('show');
        });
    }

    const mobileToggle = document.getElementById('mobile-menu-toggle');
    const navActions = document.querySelector('.nav-actions');

    if (mobileToggle && navActions) {
        const setMobileNavOpen = (open) => {
            mobileToggle.classList.toggle('active', open);
            navActions.classList.toggle('active', open);
            mobileToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            mobileToggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
            document.body.classList.toggle('nav-mobile-open', open);
        };

        mobileToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            setMobileNavOpen(!navActions.classList.contains('active'));
        });

        document.querySelectorAll('.js-nav-mobile-close').forEach((el) => {
            el.addEventListener('click', () => setMobileNavOpen(false));
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && navActions.classList.contains('active')) {
                setMobileNavOpen(false);
            }
        });

        navActions.querySelectorAll('.nav-mobile-panel a[href]').forEach((link) => {
            link.addEventListener('click', () => setMobileNavOpen(false));
        });

        navActions.querySelectorAll('.nav-mobile-panel .nav-login-trigger').forEach((btn) => {
            btn.addEventListener('click', () => setMobileNavOpen(false));
        });

        window.matchMedia('(min-width: 993px)').addEventListener('change', (e) => {
            if (e.matches) setMobileNavOpen(false);
        });
    }

    initLoginModal();
    initNavSearchSuggest();
    initBulkAddGrid();
    initAdminSidebar();
    initCategorySlider();
    initConversionTrustSection();
    initCategoryRefineAutoScroll();

    const alerts = document.querySelectorAll('.messages-container .alert');
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(20px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

function createMessagesContainer() {
    const div = document.createElement('div');
    div.id = 'messages-container';
    div.className = 'messages-container';
    document.body.appendChild(div);
    return div;
}

function initNavSearchSuggest() {
    const input = document.getElementById('nav-search-input');
    const panel = document.getElementById('nav-search-suggestions');
    if (!input || !panel) return;

    const hide = () => {
        panel.setAttribute('hidden', '');
        panel.innerHTML = '';
        input.setAttribute('aria-expanded', 'false');
    };

    const escapeHtml = (s) =>
        String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/"/g, '&quot;');

    const renderLoading = () => {
        panel.removeAttribute('hidden');
        input.setAttribute('aria-expanded', 'true');
        panel.innerHTML = `
          <div class="nav-search-suggestions--loading">
            <div class="skeleton-shimmer" style="margin-bottom:8px"></div>
            <div class="skeleton-shimmer" style="margin-bottom:8px"></div>
            <div class="skeleton-shimmer"></div>
          </div>`;
    };

    const renderResults = (taxonomy, productItems) => {
        if (!taxonomy.length && !productItems.length) {
            hide();
            return;
        }
        const blocks = [];
        if (taxonomy.length) {
            blocks.push('<div class="nav-search-suggest-section-label">Browse categories</div>');
            blocks.push(
                taxonomy
                    .map((t) => {
                        const href = String(t.url || '').replace(/"/g, '&quot;');
                        const matches =
                            t.matches != null ? `${escapeHtml(String(t.matches))} match${Number(t.matches) === 1 ? '' : 'es'}` : '';
                        return `
          <a role="option" class="nav-search-suggest-item nav-search-suggest-item--taxonomy" href="${href}">
            <span class="nav-search-suggest-item__ph" aria-hidden="true">📂</span>
            <div class="nav-search-suggest-item__meta">
              <div class="nav-search-suggest-item__name">${escapeHtml(t.path)}</div>
              <div class="nav-search-suggest-item__sub">Open filtered category view</div>
            </div>
            <div class="nav-search-suggest-item__price">${matches}</div>
          </a>`;
                    })
                    .join('')
            );
        }
        if (productItems.length) {
            blocks.push('<div class="nav-search-suggest-section-label">Products</div>');
            blocks.push(
                productItems
                    .map((p) => {
                        const thumb = p.image
                            ? `<img src="${String(p.image).replace(/"/g, '&quot;')}" alt="" width="44" height="44" />`
                            : '<span class="nav-search-suggest-item__ph" aria-hidden="true"></span>';
                        return `
          <a role="option" class="nav-search-suggest-item" href="/product/${p.id}/">
            ${thumb}
            <div class="nav-search-suggest-item__meta">
              <div class="nav-search-suggest-item__name">${escapeHtml(p.name)}</div>
              <div class="nav-search-suggest-item__sub">${escapeHtml(p.brand || '')}${p.category_name ? ' · ' + escapeHtml(p.category_name) : ''}</div>
            </div>
            <div class="nav-search-suggest-item__price">${p.base_price != null ? '₹' + escapeHtml(String(p.base_price)) : '—'}</div>
          </a>`;
                    })
                    .join('')
            );
        }
        panel.innerHTML = blocks.join('');
    };

    let debounce = null;
    input.addEventListener('input', () => {
        clearTimeout(debounce);
        const q = input.value.trim();
        if (q.length < 2) {
            hide();
            return;
        }
        debounce = setTimeout(async () => {
            renderLoading();
            try {
                const [taxRes, prodRes] = await Promise.all([
                    fetch(`/api/search/suggest/?q=${encodeURIComponent(q)}&limit=5`),
                    fetch(`/api/products/?q=${encodeURIComponent(q)}&limit=4`),
                ]);
                let taxonomy = [];
                let products = [];
                if (taxRes.ok) {
                    const tdata = await taxRes.json();
                    taxonomy = Array.isArray(tdata) ? tdata : [];
                }
                if (prodRes.ok) {
                    const pdata = await prodRes.json();
                    products = Array.isArray(pdata) ? pdata : [];
                }
                renderResults(taxonomy, products);
            } catch {
                hide();
            }
        }, 220);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') hide();
    });

    document.addEventListener('click', (e) => {
        if (!panel.contains(e.target) && e.target !== input) hide();
    });
}

function initBulkAddGrid() {
    if (document.body.dataset.auth !== '1') return;

    const normalizeQty = (qty, moq, stock, packetMode, packQty) => {
        let q = Number.isFinite(qty) ? qty : moq;
        if (packetMode && packQty > 0) {
            const minPacketQty = 1;
            if (q < minPacketQty) q = minPacketQty;
            if (q > stock) q = stock;
            return Math.max(0, q);
        }
        if (q < moq) q = moq;
        if (q > stock) q = stock;
        return q;
    };

    const onCartResponse = (data) => {
        const badge = document.querySelector('.cart-count-badge');
        const totalEl = document.querySelector('.cart-count-badge')?.closest('.cart-meta-item')?.querySelector('.meta-value');
        if (badge && data.items) badge.textContent = String(data.items.length);
        if (totalEl && data.total != null) totalEl.textContent = `₹${Number(data.total).toFixed(2)}`;
    };

    const findLine = (data, productId) =>
        (data.items || []).find((it) => it.product && Number(it.product.id) === Number(productId));

    document.body.addEventListener('click', async (e) => {
        const addBtn = e.target.closest('.js-bulk-add');
        if (addBtn) {
            e.preventDefault();
            const bar = addBtn.closest('.product-bulk-bar');
            if (!bar) return;
            const pid = bar.dataset.productId;
            const itemId = bar.dataset.itemId;
            const moq = parseInt(bar.dataset.moq, 10) || 1;
            const stock = parseInt(bar.dataset.stock, 10) || 0;
            const packetMode = bar.dataset.packetMode === '1';
            const packQty = parseInt(bar.dataset.packQty, 10) || 0;
            if (!pid || stock <= 0) return;
            if (!packetMode && stock < moq) {
                showToast('Available stock is below MOQ for this product.', 'error');
                return;
            }
            if (packetMode && packQty > 0 && stock < 1) {
                showToast('This product is out of stock.', 'error');
                return;
            }
            const uiQty = parseInt(bar.dataset.qty || '', 10)
                || parseInt(bar.querySelector('.js-bulk-val')?.textContent || '', 10)
                || (packetMode && packQty > 0 ? 1 : moq);
            const qty = normalizeQty(uiQty, moq, stock, packetMode, packQty);
            if (qty <= 0) {
                showToast('Not enough stock for a full packet.', 'error');
                return;
            }
            try {
                const res = await fetch('/api/cart/', {
                    method: itemId ? 'PATCH' : 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') || '',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(
                        itemId
                            ? { item_id: Number(itemId), quantity: qty }
                            : { product_id: Number(pid), quantity: qty }
                    ),
                });
                const data = await res.json();
                if (!res.ok) {
                    showToast(data.error || 'Could not add to cart', 'error');
                    return;
                }
                onCartResponse(data);
                const line = findLine(data, pid);
                bar.dataset.itemId = line ? line.id : '';
                bar.dataset.qty = String(line ? line.quantity : qty);
                const qtyUi = bar.querySelector('.js-bulk-qty');
                const valEl = bar.querySelector('.js-bulk-val');
                if (qtyUi) qtyUi.classList.remove('hidden');
                if (valEl) valEl.textContent = String(line ? line.quantity : qty);
                showToast(itemId ? 'Cart quantity updated' : 'Added to cart', 'success');
            } catch {
                showToast('Network error', 'error');
            }
            return;
        }

        const inc = e.target.closest('.js-bulk-inc');
        const dec = e.target.closest('.js-bulk-dec');
        if (!inc && !dec) return;
        const bar = e.target.closest('.product-bulk-bar');
        if (!bar) return;
        const itemId = bar.dataset.itemId;
        const moq = parseInt(bar.dataset.moq, 10) || 1;
        const stock = parseInt(bar.dataset.stock, 10) || 0;
        const packetMode = bar.dataset.packetMode === '1';
        const packQty = parseInt(bar.dataset.packQty, 10) || 0;
        let qty = parseInt(bar.dataset.qty, 10)
            || parseInt(bar.querySelector('.js-bulk-val')?.textContent || '', 10)
            || (packetMode && packQty > 0 ? 1 : moq);
        const step = 1;
        qty += inc ? step : -step;
        qty = normalizeQty(qty, moq, stock, packetMode, packQty);
        if (qty <= 0) {
            showToast('Not enough stock for a full packet.', 'error');
            return;
        }
        if (!itemId) {
            bar.dataset.qty = String(qty);
            const valEl = bar.querySelector('.js-bulk-val');
            if (valEl) valEl.textContent = String(qty);
            return;
        }
        if (qty === parseInt(bar.dataset.qty, 10) && dec) return;
        try {
            const res = await fetch('/api/cart/', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || '',
                },
                credentials: 'same-origin',
                body: JSON.stringify({ item_id: Number(itemId), quantity: qty }),
            });
            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || 'Update failed', 'error');
                return;
            }
            onCartResponse(data);
            bar.dataset.qty = String(qty);
            const valEl = bar.querySelector('.js-bulk-val');
            if (valEl) valEl.textContent = String(qty);
        } catch {
            showToast('Network error', 'error');
        }
    });
}

function showToast(message, type = 'success') {
    const container = document.getElementById('messages-container') || createMessagesContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button type="button" class="alert-close" onclick="this.parentElement.remove()">×</button>
    `;
    container.appendChild(alert);

    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(20px)';
        setTimeout(() => alert.remove(), 300);
    }, 4000);
}

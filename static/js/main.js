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
        const params = new URLSearchParams(window.location.search);
        let n = nextPath;
        if (n == null && params.get('open_login') === '1') {
            n = params.get('next');
        }
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

        if (params.get('open_login') === '1') {
            const u = new URL(window.location.href);
            u.searchParams.delete('open_login');
            u.searchParams.delete('next');
            const q = u.searchParams.toString();
            window.history.replaceState({}, '', u.pathname + (q ? '?' + q : '') + (u.hash || ''));
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

    const params = new URLSearchParams(window.location.search);
    if (params.get('open_login') === '1') {
        openModal(params.get('next') || undefined);
    }
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

document.addEventListener('DOMContentLoaded', () => {
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
        mobileToggle.addEventListener('click', () => {
            mobileToggle.classList.toggle('active');
            navActions.classList.toggle('active');
        });
    }

    initLoginModal();
    initNavSearchSuggest();
    initBulkAddGrid();
    initAdminSidebar();

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

    const renderResults = (items) => {
        if (!items.length) {
            hide();
            return;
        }
        panel.innerHTML = items
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
            .join('');
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
                const res = await fetch(`/api/products/?q=${encodeURIComponent(q)}&limit=3`);
                if (!res.ok) throw new Error('bad');
                const data = await res.json();
                renderResults(Array.isArray(data) ? data : []);
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

    const onCartResponse = (data) => {
        const badge = document.querySelector('.cart-count-badge');
        const totalEl = document.querySelector('.cart-meta-item .meta-value');
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
            const moq = parseInt(bar.dataset.moq, 10) || 1;
            const stock = parseInt(bar.dataset.stock, 10) || 0;
            if (!pid || stock <= 0) return;
            if (stock < moq) {
                showToast('Available stock is below MOQ for this product.', 'error');
                return;
            }
            const qty = Math.min(moq, stock);
            try {
                const res = await fetch('/api/cart/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') || '',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ product_id: Number(pid), quantity: qty }),
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
                addBtn.classList.add('hidden');
                const qtyUi = bar.querySelector('.js-bulk-qty');
                const valEl = bar.querySelector('.js-bulk-val');
                if (qtyUi) qtyUi.classList.remove('hidden');
                if (valEl) valEl.textContent = String(line ? line.quantity : qty);
                showToast('Added to bulk cart', 'success');
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
        const pid = bar.dataset.productId;
        const moq = parseInt(bar.dataset.moq, 10) || 1;
        const stock = parseInt(bar.dataset.stock, 10) || 0;
        if (!itemId) return;
        let qty = parseInt(bar.dataset.qty, 10) || moq;
        qty += inc ? 1 : -1;
        qty = Math.max(moq, Math.min(qty, stock));
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

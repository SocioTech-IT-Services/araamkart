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

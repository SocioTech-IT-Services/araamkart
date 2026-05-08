/**
 * AaramKart — Cart & Product Logic
 */

// ── PRODUCT PAGE LOGIC ──

let currentPricingTiers = [];
let currentProductId = null;
let currentMoq = 1;
let currentStock = 0;
/** @type {{ packQuantity: number, packetPrice: number, minPackets: number, maxPackets: number, unitLabel: string } | null} */
let packetPricing = null;

function initProductPage(tiers, productId, moq, stock, packetPricingOpts) {
    currentPricingTiers = tiers;
    currentProductId = productId;
    currentMoq = moq;
    currentStock = stock;
    packetPricing = packetPricingOpts || null;

    const qtyInput = document.getElementById('qty-input');
    if (qtyInput) {
        qtyInput.addEventListener('input', updatePricePreview);
        updatePricePreview();
    }

    const addToCartBtn = document.getElementById('add-to-cart-btn');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', handleAddToCart);
    }

    const stickyAddBtn = document.getElementById('sticky-add-to-cart-btn');
    if (stickyAddBtn) {
        stickyAddBtn.addEventListener('click', handleAddToCart);
    }

    bindTierCards();
    updateStockMeter();
    syncStickyTotal();
}

function changeQty(delta) {
    const input = document.getElementById('qty-input');
    if (!input) return;
    
    let val = parseInt(input.value, 10) + delta;
    if (packetPricing) {
        const { minPackets, maxPackets } = packetPricing;
        if (isNaN(val)) val = minPackets;
        val = Math.max(minPackets, Math.min(val, maxPackets));
    } else {
        if (val < currentMoq) val = currentMoq;
        if (val > currentStock) val = currentStock;
    }
    
    input.value = val;
    if (window.navigator && typeof window.navigator.vibrate === 'function') {
        window.navigator.vibrate(10);
    }
    updatePricePreview();
    updateStockMeter();
}

function updatePricePreview() {
    const input = document.getElementById('qty-input');
    const preview = document.getElementById('preview-price');
    if (!input || !preview) return;

    if (packetPricing) {
        const packets = parseInt(input.value, 10);
        if (isNaN(packets) || packets < packetPricing.minPackets) {
            preview.textContent = '—';
            syncStickyTotal();
            syncAddToCartButtonPrice();
            return;
        }
        const total = packets * packetPricing.packetPrice;
        preview.textContent = `₹${total.toLocaleString('en-IN')}`;
        syncStickyTotal();
        syncAddToCartButtonPrice();
        return;
    }

    const qty = parseInt(input.value, 10);
    if (isNaN(qty) || qty < 1) {
        preview.textContent = '—';
        syncAddToCartButtonPrice();
        return;
    }

    const unitPrice = getPriceForQty(qty);
    const total = unitPrice * qty;
    preview.textContent = `₹${total.toLocaleString('en-IN')}`;
    syncStickyTotal();
    syncAddToCartButtonPrice();
    highlightActiveTierCard(qty);
}

function getPriceForQty(qty) {
    let applicablePrice = currentPricingTiers[0]?.price || 0;
    
    // Sort tiers by min_qty descending to find the highest applicable tier
    const sorted = [...currentPricingTiers].sort((a, b) => b.min - a.min);
    
    for (const tier of sorted) {
        if (qty >= tier.min) {
            applicablePrice = tier.price;
            break;
        }
    }
    return applicablePrice;
}

async function handleAddToCart() {
    let qty = parseInt(document.getElementById('qty-input').value, 10);
    if (packetPricing) {
        qty *= packetPricing.packQuantity;
    }
    
    try {
        const response = await fetch('/orders/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                product_id: currentProductId,
                quantity: qty
            })
        });

        const data = await response.json();
        if (data.success) {
            showToast(data.message, 'success');
            const badge = document.querySelector('.cart-count-badge');
            if (badge && data.cart_count != null) badge.textContent = String(data.cart_count);
            const totalEl = document.querySelector('.cart-count-badge')?.closest('.cart-meta-item')?.querySelector('.meta-value');
            if (totalEl && data.cart_total != null) {
                totalEl.textContent = `₹${Number(data.cart_total).toFixed(2)}`;
            }
        } else {
            showToast(data.error, 'error');
        }
    } catch (err) {
        showToast('Something went wrong. Please try again.', 'error');
    }
}

function bindTierCards() {
    const qtyInput = document.getElementById('qty-input');
    if (!qtyInput) return;
    document.querySelectorAll('.tier-card').forEach(card => {
        card.addEventListener('click', () => {
            const min = parseInt(card.dataset.min || '0', 10);
            if (min > 0) {
                qtyInput.value = Math.max(min, currentMoq);
                updatePricePreview();
                updateStockMeter();
            }
        });
    });
}

function highlightActiveTierCard(qty) {
    let activeCard = null;
    document.querySelectorAll('.tier-card').forEach(card => {
        card.classList.remove('is-active');
        const min = parseInt(card.dataset.min || '0', 10);
        if (qty >= min) {
            if (!activeCard || min >= parseInt(activeCard.dataset.min || '0', 10)) {
                activeCard = card;
            }
        }
    });
    if (activeCard) activeCard.classList.add('is-active');
}

function updateStockMeter() {
    const fill = document.getElementById('stock-meter-fill');
    const text = document.getElementById('stock-meter-text');
    const qtyInput = document.getElementById('qty-input');
    if (!fill || !text || !qtyInput || !currentStock) return;

    if (packetPricing) {
        const packets = parseInt(qtyInput.value || '0', 10);
        const { maxPackets, unitLabel } = packetPricing;
        const ratio = maxPackets
            ? Math.min(100, Math.max(0, Math.round((packets / maxPackets) * 100)))
            : 0;
        fill.style.width = `${ratio}%`;
        text.textContent = `Available: ${maxPackets} packets (${currentStock} ${unitLabel}) · Selected: ${packets} packet(s)`;
        return;
    }

    const qty = parseInt(qtyInput.value || '0', 10);
    const ratio = Math.min(100, Math.max(0, Math.round((qty / currentStock) * 100)));
    fill.style.width = `${ratio}%`;
    text.textContent = `In Stock: ${currentStock} | Selected: ${qty}`;
}

function syncStickyTotal() {
    const preview = document.getElementById('preview-price');
    const sticky = document.getElementById('sticky-preview-price');
    if (preview && sticky) sticky.textContent = preview.textContent || '₹0';
}

function syncAddToCartButtonPrice() {
    const preview = document.getElementById('preview-price');
    const addBtnPrice = document.getElementById('add-to-cart-btn-price');
    if (!addBtnPrice) return;
    const v = (preview && preview.textContent ? preview.textContent.trim() : '');
    addBtnPrice.textContent = v && v !== '—' ? ` • ${v}` : '';
}

// ── CART PAGE LOGIC ──

async function updateCartItem(itemId, newQty) {
    const qtyInput = document.getElementById(`qty-${itemId}`);
    const minusBtn = document.getElementById(`minus-${itemId}`);
    const plusBtn = document.getElementById(`plus-${itemId}`);
    const min = parseInt(qtyInput.min, 10);
    const max = parseInt(qtyInput.max, 10);
    const packetMode = qtyInput.dataset.packetMode === '1';
    const packQty = parseInt(qtyInput.dataset.packQty || '0', 10);
    const prevQty = parseInt(qtyInput.value, 10) || min;

    newQty = parseInt(newQty, 10);
    if (Number.isNaN(newQty)) newQty = min;

    if (packetMode && packQty > 0) {
        const minMultiple = Math.ceil(min / packQty) * packQty;
        if (newQty < minMultiple) newQty = minMultiple;
        newQty = Math.round(newQty / packQty) * packQty;
        if (newQty < minMultiple) newQty = minMultiple;
        if (newQty > max) {
            newQty = Math.floor(max / packQty) * packQty;
            if (newQty === prevQty && plusBtn) {
                showToast('Limit reached for available stock.', 'error');
            }
        }
        if (newQty <= 0) {
            showToast(`Not enough stock for a full packet of ${packQty}.`, 'error');
            newQty = parseInt(qtyInput.value, 10) || minMultiple;
        }
    } else {
        if (newQty < min) {
            newQty = min;
            if (newQty === prevQty && minusBtn) showToast('Minimum order quantity reached.', 'error');
        }
        if (newQty > max) {
            newQty = max;
            if (newQty === prevQty && plusBtn) showToast('Limit reached for available stock.', 'error');
        }
    }

    qtyInput.value = newQty;
    toggleQtyButtons(itemId);
    qtyInput.classList.remove('is-pulse');
    void qtyInput.offsetWidth;
    qtyInput.classList.add('is-pulse');

    try {
        const response = await fetch('/orders/cart/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                item_id: itemId,
                quantity: newQty
            })
        });

        const data = await response.json();
        if (data.success) {
            // Update prices on UI
            const unitEl = document.getElementById(`unit-price-${itemId}`);
            if (unitEl) {
                if (unitEl.dataset.packetMode === '1') {
                    const pu = unitEl.dataset.packetUnit || 'pcs';
                    const singular = pu === 'pcs' ? 'piece' : pu;
                    unitEl.textContent = `₹${data.unit_price} per ${singular}`;
                } else {
                    unitEl.textContent = `₹${data.unit_price} / unit`;
                }
            }
            document.getElementById(`line-total-${itemId}`).textContent = `₹${data.line_total}`;
            animateRollTotal('cart-total', data.cart_total);
            animateRollTotal('grand-total', data.cart_total);
            toggleQtyButtons(itemId);
        } else {
            showToast(data.error, 'error');
            qtyInput.value = String(prevQty);
            toggleQtyButtons(itemId);
        }
    } catch (err) {
        showToast('Failed to update cart.', 'error');
        qtyInput.value = String(prevQty);
        toggleQtyButtons(itemId);
    }
}

function toggleQtyButtons(itemId) {
    const qtyInput = document.getElementById(`qty-${itemId}`);
    const minusBtn = document.getElementById(`minus-${itemId}`);
    const plusBtn = document.getElementById(`plus-${itemId}`);
    if (!qtyInput) return;
    const min = parseInt(qtyInput.min, 10);
    const max = parseInt(qtyInput.max, 10);
    const packetMode = qtyInput.dataset.packetMode === '1';
    const packQty = parseInt(qtyInput.dataset.packQty || '0', 10);
    const qty = parseInt(qtyInput.value, 10) || min;
    const maxAllowed = packetMode && packQty > 0 ? Math.floor(max / packQty) * packQty : max;
    if (minusBtn) minusBtn.disabled = qty <= min;
    if (plusBtn) plusBtn.disabled = qty >= maxAllowed;
}

async function removeCartItem(itemId) {
    await confirmCartRemoval(async () => {
        try {
            const response = await fetch('/orders/cart/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ item_id: itemId })
            });

            const data = await response.json();
            if (data.success) {
                const row = document.getElementById(`cart-item-${itemId}`);
                if (row) {
                    row.classList.add('is-removing');
                    window.setTimeout(() => row.remove(), 260);
                }
                animateRollTotal('cart-total', data.cart_total);
                animateRollTotal('grand-total', data.cart_total);
                document.getElementById('cart-badge').textContent = data.cart_count;
                if (data.cart_count === 0) {
                    window.setTimeout(() => location.reload(), 280); // Show empty state after animation
                }
                return true;
            }
            showToast('Failed to remove item.', 'error');
            return false;
        } catch (err) {
            showToast('Failed to remove item.', 'error');
            return false;
        }
    });
}

function confirmCartRemoval(onConfirmAsync) {
    return new Promise((resolve) => {
        const modal = document.getElementById('cart-remove-modal');
        const confirmBtn = document.getElementById('cart-remove-confirm');
        const cancelBtn = document.getElementById('cart-remove-cancel');
        const spinner = document.getElementById('cart-remove-spinner');
        const confirmLabel = document.getElementById('cart-remove-confirm-label');
        if (!modal || !confirmBtn || !cancelBtn) {
            showToast('Custom remove popup is unavailable. Please refresh the page.', 'error');
            resolve(false);
            return;
        }

        let loading = false;
        const close = (accepted) => {
            if (loading) return;
            modal.classList.remove('is-open');
            modal.setAttribute('aria-hidden', 'true');
            confirmBtn.classList.remove('is-loading');
            confirmBtn.disabled = false;
            cancelBtn.disabled = false;
            if (spinner) spinner.style.display = 'none';
            if (confirmLabel) confirmLabel.textContent = 'Remove';
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            modal.removeEventListener('click', onBackdrop);
            document.removeEventListener('keydown', onKeydown);
            resolve(accepted);
        };

        const onConfirm = async () => {
            loading = true;
            confirmBtn.classList.add('is-loading');
            confirmBtn.disabled = true;
            cancelBtn.disabled = true;
            if (spinner) spinner.style.display = 'inline-block';
            if (confirmLabel) confirmLabel.textContent = 'Removing...';
            await new Promise((r) => window.setTimeout(r, 400));
            const ok = typeof onConfirmAsync === 'function' ? await onConfirmAsync() : true;
            loading = false;
            if (ok) {
                close(true);
            } else {
                confirmBtn.classList.remove('is-loading');
                confirmBtn.disabled = false;
                cancelBtn.disabled = false;
                if (spinner) spinner.style.display = 'none';
                if (confirmLabel) confirmLabel.textContent = 'Remove';
            }
        };
        const onCancel = () => close(false);
        const onBackdrop = (e) => {
            if (e.target === modal) close(false);
        };
        const onKeydown = (e) => {
            if (e.key === 'Escape') close(false);
        };

        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
        modal.addEventListener('click', onBackdrop);
        document.addEventListener('keydown', onKeydown);
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
    });
}

function animateRollTotal(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('is-rolling');
    window.setTimeout(() => {
        const n = Number(value);
        el.textContent = `₹${Number.isFinite(n) ? n.toFixed(2) : value}`;
        el.classList.remove('is-rolling');
    }, 140);
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.qty-input[id^="qty-"]').forEach((input) => {
        const itemId = input.id.replace('qty-', '');
        toggleQtyButtons(itemId);
    });
});

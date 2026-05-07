/**
 * AaramKart — Cart & Product Logic
 */

// ── PRODUCT PAGE LOGIC ──

let currentPricingTiers = [];
let currentProductId = null;
let currentMoq = 1;
let currentStock = 0;

function initProductPage(tiers, productId, moq, stock) {
    currentPricingTiers = tiers;
    currentProductId = productId;
    currentMoq = moq;
    currentStock = stock;

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
    
    let val = parseInt(input.value) + delta;
    if (val < currentMoq) val = currentMoq;
    if (val > currentStock) val = currentStock;
    
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

    const qty = parseInt(input.value);
    if (isNaN(qty) || qty < 1) {
        preview.textContent = '—';
        return;
    }

    const unitPrice = getPriceForQty(qty);
    const total = unitPrice * qty;
    preview.textContent = `₹${total.toLocaleString('en-IN')}`;
    syncStickyTotal();
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
    const qty = parseInt(document.getElementById('qty-input').value);
    
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
            // Update cart badge
            const badge = document.getElementById('cart-badge');
            if (badge) badge.textContent = data.cart_count;
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

// ── CART PAGE LOGIC ──

async function updateCartItem(itemId, newQty) {
    const qtyInput = document.getElementById(`qty-${itemId}`);
    const min = parseInt(qtyInput.min);
    const max = parseInt(qtyInput.max);

    if (newQty < min) newQty = min;
    if (newQty > max) newQty = max;

    qtyInput.value = newQty;

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
            document.getElementById(`unit-price-${itemId}`).textContent = `₹${data.unit_price} / unit`;
            document.getElementById(`line-total-${itemId}`).textContent = `₹${data.line_total}`;
            document.getElementById('cart-total').textContent = `₹${data.cart_total}`;
            document.getElementById('grand-total').textContent = `₹${data.cart_total}`;
        } else {
            showToast(data.error, 'error');
        }
    } catch (err) {
        showToast('Failed to update cart.', 'error');
    }
}

async function removeCartItem(itemId) {
    if (!confirm('Remove this item from cart?')) return;

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
            document.getElementById(`cart-item-${itemId}`).remove();
            document.getElementById('cart-total').textContent = `₹${data.cart_total}`;
            document.getElementById('grand-total').textContent = `₹${data.cart_total}`;
            document.getElementById('cart-badge').textContent = data.cart_count;
            
            if (data.cart_count === 0) {
                location.reload(); // Show empty state
            }
        }
    } catch (err) {
        showToast('Failed to remove item.', 'error');
    }
}

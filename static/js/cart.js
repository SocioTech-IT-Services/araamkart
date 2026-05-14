/**
 * AaramKart — Cart & Product Logic
 */

// ── PRODUCT PAGE LOGIC ──

let currentPricingTiers = [];
let currentProductId = null;
let currentMoq = 1;
let currentStock = 0;
/** @type {{ packQuantity: number, packetPrice: number, originalPacketPrice?: number, discountPerPacket?: number, minPackets: number, maxPackets: number, unitLabel: string } | null} */
let packetPricing = null;
/** @type {Array<{ id: number, label: string, sku: string, pack_size: number, stock: number, single_sp: number, single_mrp: number | null, packet_price: number, packet_mrp: number, savings_per_packet: number }>} */
let productVariants = [];
let selectedVariantId = null;

function fmtMoneyInr(n) {
    const x = Number(n);
    if (!Number.isFinite(x)) return '—';
    return x.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function initProductPage(tiers, productId, moq, stock, packetPricingOpts, variantsList, defaultVariantId) {
    currentPricingTiers = tiers;
    currentProductId = productId;
    currentMoq = moq;
    currentStock = stock;
    packetPricing = packetPricingOpts || null;
    productVariants = Array.isArray(variantsList) ? variantsList : [];
    selectedVariantId = defaultVariantId != null ? Number(defaultVariantId) : null;

    if (packetPricing && productVariants.length > 0) {
        const v =
            productVariants.find((row) => Number(row.id) === Number(selectedVariantId)) ||
            productVariants[0];
        if (v) {
            selectedVariantId = Number(v.id);
            applyVariantToPacketPricing(v);
        }
        renderProductVariantButtons();
    }

    const qtyInput = document.getElementById('qty-input');
    if (qtyInput) {
        qtyInput.addEventListener('input', updatePricePreview);
        qtyInput.addEventListener('change', updatePricePreview);
        syncPacketOrderSummaryFromInput();
        updatePacketPiecesBadge();
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

    bindProductActionRipples();
    bindTierCards();
    updateStockMeter();
    syncStickyTotal();
}

function applyVariantToPacketPricing(v) {
    if (!v || !packetPricing) return;
    const pk = Math.max(1, Number(v.pack_size) || 1);
    const stockPackets = Math.max(0, Number(v.stock) || 0);
    const sellPkt = Number(v.packet_price);
    const listPktRaw = v.packet_mrp != null && v.packet_mrp !== '' ? Number(v.packet_mrp) : NaN;
    const listPkt = Number.isFinite(listPktRaw) ? listPktRaw : (Number.isFinite(sellPkt) ? sellPkt : 0);

    packetPricing.packQuantity = pk;
    packetPricing.packetPrice = Number.isFinite(sellPkt) ? sellPkt : 0;
    packetPricing.originalPacketPrice = listPkt;
    packetPricing.discountPerPacket = Math.max(
        0,
        Number(v.savings_per_packet) ||
            (packetPricing.originalPacketPrice - packetPricing.packetPrice)
    );
    packetPricing.minPackets = stockPackets > 0 ? 1 : 0;
    packetPricing.maxPackets = stockPackets;
    currentStock = stockPackets;

    const hero = document.getElementById('pdp-packet-hero-price');
    if (hero) hero.textContent = `₹${fmtMoneyInr(v.packet_price)}`;
    const perLine = document.getElementById('pdp-per-piece-line');
    const perUnitNum = Number(v.packet_price) / pk;
    if (perLine) perLine.textContent = `₹${fmtMoneyInr(perUnitNum)}/pc · Price per piece`;

    const origPktEl = document.getElementById('pdp-original-packet-mrp-display');
    if (origPktEl) {
        const op = Number(v.packet_mrp);
        origPktEl.textContent = Number.isFinite(op) ? fmtMoneyInr(op) : '—';
    }
    const sellPktEl = document.getElementById('pdp-packet-selling-display');
    if (sellPktEl) sellPktEl.textContent = fmtMoneyInr(v.packet_price);

    const titleSuf = document.getElementById('product-title-variant');
    if (titleSuf) titleSuf.textContent = v.label ? ` · ${v.label}` : '';

    const pq = document.getElementById('pdp-pack-qty-hint');
    if (pq) pq.textContent = String(pk);
    const mx = document.getElementById('pdp-max-packets-hint');
    if (mx) mx.textContent = String(stockPackets);

    const qtyInput = document.getElementById('qty-input');
    if (qtyInput && packetPricing) {
        let q = parseInt(qtyInput.value, 10);
        if (Number.isNaN(q)) q = packetPricing.minPackets;
        q = Math.max(packetPricing.minPackets, Math.min(q, packetPricing.maxPackets || q));
        qtyInput.min = String(Math.max(1, packetPricing.minPackets || 1));
        qtyInput.max = String(Math.max(0, packetPricing.maxPackets || 0));
        qtyInput.value = String(q);
    }

    syncPacketOrderSummaryFromInput();
}

function renderProductVariantButtons() {
    const strip = document.getElementById('product-variant-strip');
    if (!strip || !productVariants.length) return;
    strip.innerHTML = '';
    productVariants.forEach((v) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'product-variant-chip';
        btn.setAttribute('role', 'option');
        btn.dataset.variantId = String(v.id);
        btn.textContent = v.label != null && String(v.label).length ? String(v.label) : String(v.id);
        const st = Math.max(0, Number(v.stock) || 0);
        if (st <= 0) {
            btn.disabled = true;
            btn.classList.add('is-disabled');
            btn.title = 'Out of stock';
        }
        if (Number(v.id) === Number(selectedVariantId)) {
            btn.classList.add('is-active');
            btn.setAttribute('aria-selected', 'true');
        } else {
            btn.setAttribute('aria-selected', 'false');
        }
        btn.addEventListener('click', () => {
            if (btn.disabled) return;
            selectedVariantId = Number(v.id);
            applyVariantToPacketPricing(v);
            strip.querySelectorAll('.product-variant-chip').forEach((b) => {
                b.classList.toggle('is-active', b.dataset.variantId === String(v.id));
                b.setAttribute('aria-selected', b.dataset.variantId === String(v.id) ? 'true' : 'false');
            });
            updatePricePreview();
            syncPacketOrderSummaryFromInput();
            updatePacketPiecesBadge();
            updateStockMeter();
            syncStickyTotal();
            syncAddToCartButtonPrice();
        });
        strip.appendChild(btn);
    });
}

function bindProductActionRipples() {
    document.querySelectorAll('.js-product-action-ripple').forEach((button) => {
        if (button.dataset.rippleBound === '1') return;
        button.dataset.rippleBound = '1';
        button.addEventListener('click', (event) => {
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const ripple = document.createElement('span');
            ripple.className = 'product-action-ripple';
            ripple.style.width = `${size}px`;
            ripple.style.height = `${size}px`;
            ripple.style.left = `${event.clientX - rect.left}px`;
            ripple.style.top = `${event.clientY - rect.top}px`;
            button.appendChild(ripple);
            window.setTimeout(() => ripple.remove(), 620);
        });
    });
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
    syncPacketOrderSummaryFromInput();
    updatePacketPiecesBadge();
    updateStockMeter();
}

function updatePricePreview() {
    const input = document.getElementById('qty-input');
    const preview = document.getElementById('preview-price');
    if (!input) return;

    if (packetPricing) {
        const packets = parseInt(input.value, 10);
        if (isNaN(packets) || packets < packetPricing.minPackets) {
            updatePacketOrderSummary(0);
            if (preview) preview.textContent = '—';
            syncStickyTotal();
            syncAddToCartButtonPrice();
            return;
        }
        const total = packets * packetPricing.packetPrice;
        updatePacketOrderSummary(packets);
        updatePacketPiecesBadge(packets);
        if (preview) preview.textContent = `₹${total.toLocaleString('en-IN')}`;
        syncStickyTotal();
        syncAddToCartButtonPrice();
        return;
    }

    if (!preview) return;

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

function syncPacketOrderSummaryFromInput() {
    if (!packetPricing) return;
    const input = document.getElementById('qty-input');
    if (!input) return;
    let packets = parseInt(input.value, 10);
    if (Number.isNaN(packets)) packets = packetPricing.minPackets || 0;
    packets = Math.max(packetPricing.minPackets || 0, Math.min(packets, packetPricing.maxPackets || packets));
    updatePacketOrderSummary(packets);
    updatePacketPiecesBadge(packets);
}

function updatePacketPiecesBadge(packetCount) {
    if (!packetPricing) return;
    const badge = document.getElementById('packet-pieces-badge');
    const countEl = document.getElementById('packet-pieces-count');
    const input = document.getElementById('qty-input');
    if (!badge || !countEl || !input) return;

    let packets = Number(packetCount);
    if (!Number.isFinite(packets)) {
        packets = parseInt(input.value || '0', 10);
    }
    if (!Number.isFinite(packets)) packets = packetPricing.minPackets || 0;

    const packQuantity = Number(packetPricing.packQuantity || 0);
    const totalPieces = Math.max(0, packets) * packQuantity;
    countEl.textContent = `(${totalPieces} Pieces)`;
    badge.setAttribute('aria-label', `${packets} packet(s) equals ${totalPieces} pieces`);
}

function formatMoney(value) {
    const amount = Number(value || 0);
    return `₹${amount.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

function updatePacketOrderSummary(packets) {
    if (!packetPricing) return;
    const safePackets = Math.max(0, Number(packets || 0));
    const packQuantity = Number(packetPricing.packQuantity || 0);
    const packetPrice = Number(packetPricing.packetPrice || 0);
    const originalPacketPrice = Number(packetPricing.originalPacketPrice || packetPrice);
    const discountPerPacket = Number(packetPricing.discountPerPacket || Math.max(0, originalPacketPrice - packetPrice));
    const values = {
        packets: safePackets,
        totalItems: safePackets * packQuantity,
        originalPrice: safePackets * originalPacketPrice,
        savings: safePackets * discountPerPacket,
        finalAmount: safePackets * packetPrice
    };

    const packetEl = document.getElementById('summary-packets');
    const itemsEl = document.getElementById('summary-total-items');
    const originalEl = document.getElementById('summary-original-price');
    const savingsEl = document.getElementById('summary-savings');
    const savingsBadgeEl = document.getElementById('summary-savings-badge');
    const finalEl = document.getElementById('summary-final-amount');

    if (packetEl) packetEl.textContent = String(values.packets);
    if (itemsEl) itemsEl.textContent = String(values.totalItems);
    if (originalEl) originalEl.textContent = formatMoney(values.originalPrice);
    if (savingsEl) savingsEl.textContent = formatMoney(values.savings);
    if (savingsBadgeEl) savingsBadgeEl.textContent = formatMoney(values.savings).replace('₹', '');
    if (finalEl) finalEl.textContent = formatMoney(values.finalAmount);
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
    const qty = parseInt(document.getElementById('qty-input').value, 10);

    if (packetPricing && productVariants.length > 0) {
        const v = productVariants.find((row) => Number(row.id) === Number(selectedVariantId));
        if (!v || !(Number(v.stock) > 0)) {
            showToast('This option is out of stock.', 'error');
            return;
        }
    }

    const body = {
        product_id: currentProductId,
        quantity: qty,
    };
    if (productVariants.length > 0 && selectedVariantId != null) {
        body.variant_id = selectedVariantId;
    }

    try {
        const response = await fetch('/orders/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(body),
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
    if (!fill || !text || !qtyInput) return;

    if (packetPricing) {
        const packets = parseInt(qtyInput.value || '0', 10);
        const { maxPackets } = packetPricing;
        if (!maxPackets) {
            fill.style.width = '0%';
            text.textContent = 'Out of stock for this option';
            return;
        }
        const ratio = maxPackets
            ? Math.min(100, Math.max(0, Math.round((packets / maxPackets) * 100)))
            : 0;
        fill.style.width = `${ratio}%`;
        text.textContent = `Available: ${maxPackets} packets · Selected: ${packets} packet(s)`;
        return;
    }

    if (!currentStock) return;

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

function changeCartItemQty(itemId, delta) {
    const qtyInput = document.getElementById(`qty-${itemId}`);
    if (!qtyInput) return;
    const currentQty = parseInt(qtyInput.value, 10) || parseInt(qtyInput.min, 10) || 1;
    updateCartItem(itemId, currentQty + delta);
}

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
        if (newQty < min) newQty = min;
        if (newQty > max) {
            newQty = max;
            if (newQty === prevQty && plusBtn) {
                showToast('Limit reached for available stock.', 'error');
            }
        }
        if (newQty <= 0) {
            showToast('Not enough stock for a full packet.', 'error');
            newQty = parseInt(qtyInput.value, 10) || min;
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
                    unitEl.textContent = `₹${data.unit_price} / packet`;
                } else {
                    unitEl.textContent = `₹${data.unit_price} / unit`;
                }
            }
            document.getElementById(`line-total-${itemId}`).textContent = `₹${data.line_total}`;
            updateCartPiecesLabel(itemId, data.quantity ?? newQty, data.packet_size, data.total_pieces);
            updateLineSavings(itemId, data.line_savings);
            updateCartSummaryTotals(data);
            toggleQtyButtons(itemId);
        } else {
            showToast(data.error, 'error');
            qtyInput.value = String(prevQty);
            updateCartPiecesLabel(itemId, prevQty);
            toggleQtyButtons(itemId);
        }
    } catch (err) {
        showToast('Failed to update cart.', 'error');
        qtyInput.value = String(prevQty);
        updateCartPiecesLabel(itemId, prevQty);
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
    const qty = parseInt(qtyInput.value, 10) || min;
    const maxAllowed = max;
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
                updateCartSummaryTotals(data);
                document.getElementById('cart-badge').textContent = data.cart_count;
                showToast('✓ Item removed successfully.', 'success');
                if (data.cart_count === 0) {
                    try {
                        sessionStorage.setItem('akCartRemovedToast', '✓ Item removed successfully.');
                    } catch (_) {
                        /* private mode */
                    }
                    window.setTimeout(() => location.reload(), 900); // Show empty state after animation and toast.
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

function animateRollTotal(id, value, prefix = '₹') {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('is-rolling');
    window.setTimeout(() => {
        const n = Number(value);
        el.textContent = `${prefix}${Number.isFinite(n) ? n.toFixed(2) : value}`;
        el.classList.remove('is-rolling');
    }, 140);
}

function setMoneyText(id, value, prefix = '₹') {
    const el = document.getElementById(id);
    if (!el) return;
    const n = Number(value);
    el.textContent = `${prefix}${Number.isFinite(n) ? n.toFixed(2) : value}`;
}

function updateCartSummaryTotals(data) {
    const finalTotal = data.cart_total;
    const originalTotal = data.original_total ?? data.cart_total;
    const totalSavings = data.total_savings ?? 0;
    animateRollTotal('cart-subtotal', originalTotal);
    animateRollTotal('grand-total', finalTotal);
    animateRollTotal('bulk-discount', totalSavings, '-₹');
    setMoneyText('breakdown-original', originalTotal);
    setMoneyText('breakdown-savings', totalSavings, '-₹');
    setMoneyText('breakdown-final', finalTotal);
}

function updateCartPiecesLabel(itemId, quantity, packetSize, totalPieces) {
    const label = document.getElementById(`total-pieces-${itemId}`);
    const qtyInput = document.getElementById(`qty-${itemId}`);
    if (!label || !qtyInput) return;
    const text = document.getElementById(`total-pieces-text-${itemId}`);
    const packQty = Number(packetSize || qtyInput.dataset.packQty || 0);
    if (!packQty) return;
    const packets = Number(quantity || qtyInput.value || 0);
    const pieces = Number(totalPieces || packets * packQty);
    if (text) text.textContent = `Total: ${pieces} Pieces`;
}

function updateLineSavings(itemId, value) {
    const el = document.getElementById(`line-savings-${itemId}`);
    if (!el) return;
    const n = Number(value || 0);
    el.textContent = `Saved ₹${Number.isFinite(n) ? n.toFixed(2) : value}`;
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        const pendingToast = sessionStorage.getItem('akCartRemovedToast');
        if (pendingToast) {
            sessionStorage.removeItem('akCartRemovedToast');
            showToast(pendingToast, 'success');
        }
    } catch (_) {
        /* private mode */
    }

    document.querySelectorAll('.qty-input[id^="qty-"]').forEach((input) => {
        const itemId = input.id.replace('qty-', '');
        toggleQtyButtons(itemId);
        updateCartPiecesLabel(itemId, input.value);
    });
});

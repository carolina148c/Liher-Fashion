function getCsrfToken() {
    // Intenta buscar el token en un input oculto dentro de un formulario (como el que añadimos)
    const tokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenElement) {
        return tokenElement.value;
    }

    // Como alternativa, busca el token en las cookies (método estándar de Django)
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
        // 🛑 FUNCIÓN ELIMINAR CORREGIDA: Incluye itemId en la URL y el CSRF token
    async function removeItem(itemId) { 
    if (confirm('¿Estás seguro de que quieres eliminar este producto?')) {
        try {
            // CAMBIA '/cart/remove/' por '/carrito/eliminar/'
            const response = await fetch(`/carrito/eliminar/${itemId}/`, {
                method: 'POST',
                headers: { 
                    'X-CSRFToken': getCsrfToken()
                }
            });
            const data = await response.json();
            
            if (data.success) {
                // Usa el itemId para encontrar y remover la fila correcta
                document.getElementById(`item-row-${itemId}`).remove(); 
                updateCartTotals(data);
                
                // Si el carrito está vacío, recarga para mostrar el mensaje de "carrito vacío"
                // En tu data del views.py podrías incluir un items_count, 
                // pero si solo tienes total_items, usa eso.
                if (data.total_items === 0) { 
                    location.reload();
                }
            } else {
                alert(data.message || 'Error al eliminar el producto.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error de conexión al eliminar el producto.');
        }
    }
}

        async function applyCoupon() {
            const couponCode = document.getElementById('coupon-code').value.trim();
            const messageDiv = document.getElementById('coupon-message');
            if (!couponCode) {
                messageDiv.innerHTML = '<span style="color: #dc2626;">Por favor ingresa un código de cupón</span>';
                return;
            }

            try {
                const response = await fetch('/cart/apply-coupon/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({ 'coupon_code': couponCode })
                });
                const data = await response.json();
                if (data.success) {
                    messageDiv.innerHTML = `<span style="color: #059669;">✓ Cupón aplicado: ${data.discount_percentage}% de descuento</span>`;
                    updateCartTotals(data);
                } else {
                    messageDiv.innerHTML = `<span style="color: #dc2626;">✗ ${data.error}</span>`;
                }
            } catch (error) {
                console.error('Error:', error);
                messageDiv.innerHTML = '<span style="color: #dc2626;">Error al aplicar cupón por conexión.</span>';
            }
        }

        function updateCartTotals(data) {
            document.getElementById('subtotal-amount').textContent = `$${parseFloat(data.subtotal).toFixed(0)}`;
            document.getElementById('discount-amount').textContent = data.discount ? `-$${parseFloat(data.discount).toFixed(0)}` : '$0';
            document.getElementById('shipping-amount').textContent = data.shipping_cost === 0 ? "Gratis" : `$${parseFloat(data.shipping_cost).toFixed(0)}`;
            document.getElementById('total-amount').textContent = `$${parseFloat(data.total).toFixed(0)}`;
        }

        function proceedToCheckout() {
            window.location.href = '{% url "Pago" %}';
        }

        function continueShopping() {
            window.location.href = '{% url "Vista_productos" %}';
        }
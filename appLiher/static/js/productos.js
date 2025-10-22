        // ----------------------------------------------------
        // FUNCIONES CORE DE JAVASCRIPT
        // ----------------------------------------------------

        // Obtiene el CSRF token, necesario para las peticiones POST de Django
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

        /**
         * Llama a la vista de Django para añadir el producto al carrito.
         * Usa la respuesta JSON para mostrar una alerta.
         * @param {number} productoId - El ID del producto de Inventario.
         */
        async function agregarAlCarritoConAlerta(productoId) {
            // Asegúrate que esta URL coincida con la ruta definida en tu urls.py
            const url = `{% url 'anadir_al_carrito' producto_id=0 %}`.replace('0', productoId);
            
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                    // Simula el envío de la cantidad (Tu vista espera 'cantidad')
                    body: JSON.stringify({ 'cantidad': 1 }) 
                });

                const data = await response.json(); 

                if (response.ok && data.success) {
                    // Muestra la alerta con el mensaje de éxito que viene de Python
                    alert(`✅ ¡Éxito! ${data.message}`); 
                    // Actualiza el contador del carrito en el header
                    actualizarContadorCarrito(data.total_items); 
                } else {
                    // Muestra la alerta con el mensaje de error o falta de stock
                    alert(`❌ Error: ${data.message || 'Error desconocido al añadir al carrito.'}`);
                }
            } catch (error) {
                console.error('Error de conexión o en la solicitud:', error);
                alert('🚨 Ocurrió un error al intentar conectar con el servidor.');
            }
        }

        /**
         * Actualiza el contador de ítems en el encabezado.
         * @param {number} newCount - El nuevo número de ítems en el carrito.
         */
        function actualizarContadorCarrito(newCount) {
            if (typeof newCount !== 'undefined') {
                const carritoElement = document.querySelector('a[href*="carrito"]');
                if (carritoElement) {
                    // Actualiza el texto directamente con el nuevo conteo
                    carritoElement.textContent = `carrito(${newCount})`; 
                }
            }
            // NOTA: Si necesitas actualizar el contador sin el conteo de la respuesta AJAX, 
            // tendrías que hacer un FETCH a una URL de Django dedicada a contar ítems.
        }

        function comprarAhora() {
            // Esta función debería redirigir a la página de checkout.
            alert("Redirigiendo a la página de pago (Comprar Ahora)...");
            // window.location.href = "/checkout/"; // Ejemplo de redirección
        }
        
        // ----------------------------------------------------
        // LÓGICA DE ANIMACIÓN (la de tu código original)
        // ----------------------------------------------------
        document.addEventListener('DOMContentLoaded', function() {
            // Animación de entrada escalonada
            const cards = document.querySelectorAll('.fade-in-up');
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.animationPlayState = 'running';
                    }
                });
            }, {
                threshold: 0.1
            });

            cards.forEach(card => {
                observer.observe(card);
            });
            
            // Efecto de hover mejorado para los selectores
            const selects = document.querySelectorAll('select');
            selects.forEach(select => {
                select.addEventListener('focus', function() {
                    this.parentElement.style.transform = 'scale(1.02)';
                    this.parentElement.style.transition = 'transform 0.2s ease';
                });
                select.addEventListener('blur', function() {
                    this.parentElement.style.transform = 'scale(1)';
                });
            });
        });
        // Animación para las tarjetas al cargar
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.stat-card, .main-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });



// ===== FORMATO DE PRECIOS EN LA TABLA =====
document.addEventListener('DOMContentLoaded', function() {
    formatTablePrices();
});

function formatTablePrices() {
    const priceElements = document.querySelectorAll('.price-value');
    
    priceElements.forEach(element => {
        const rawPrice = element.getAttribute('data-price');
        if (rawPrice) {
            try {
                // Convertir a número y formatear con puntos
                const numericPrice = parseFloat(rawPrice);
                if (!isNaN(numericPrice)) {
                    const formattedPrice = numericPrice.toLocaleString('es-CO');
                    element.textContent = `$${formattedPrice}`;
                }
            } catch (e) {
                console.error('Error formateando precio:', e);
            }
        }
    });
}

// ===== EXPANSIÓN DE IMÁGENES =====
document.addEventListener('DOMContentLoaded', function() {
    initImageExpansion();
});

function initImageExpansion() {
    const productImages = document.querySelectorAll('.product-image img');
    
    productImages.forEach(img => {
        img.style.cursor = 'pointer';
        img.addEventListener('click', function() {
            expandImage(this.src, this.alt);
        });
    });
}

function expandImage(src, alt) {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        cursor: zoom-out;
    `;
    
    const img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    `;
    
    overlay.appendChild(img);
    
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
        }
    });
    
    // Cerrar con ESC
    const keyHandler = function(e) {
        if (e.key === 'Escape') {
            document.body.removeChild(overlay);
            document.removeEventListener('keydown', keyHandler);
        }
    };
    
    document.addEventListener('keydown', keyHandler);
    document.body.appendChild(overlay);
}

// ===== MEJORAS DE USABILIDAD =====
document.addEventListener('DOMContentLoaded', function() {
    enhanceTableUsability();
});

function enhanceTableUsability() {
    const tableRows = document.querySelectorAll('.products-table tbody tr');
    
    tableRows.forEach(row => {
        // Efecto hover mejorado
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
            this.style.transition = 'background-color 0.2s ease';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
        
        // Click en fila (opcional - para futuras funcionalidades)
        row.addEventListener('click', function(e) {
            // Evitar que se active cuando se hace click en acciones
            if (!e.target.closest('.table-actions')) {
                // Aquí puedes agregar funcionalidad futura
                console.log('Fila clickeada:', this);
            }
        });
    });
}
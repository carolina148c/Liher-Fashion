        // Variables globales
        let allProducts = [];
        let currentSearchTerm = '';

        // Función para inicializar la búsqueda
        function initializeSearch() {
            const searchInput = document.getElementById('searchInput');
            const clearButton = document.getElementById('clearSearch');
            const tableBody = document.getElementById('inventoryTableBody');
            
            // Obtener todas las filas de productos
            const productRows = tableBody.querySelectorAll('.product-row');
            
            // Guardar información de todos los productos
            allProducts = Array.from(productRows).map(row => ({
                element: row,
                name: row.dataset.productName || '',
                id: row.dataset.productId || '',
                category: row.dataset.category || '',
                color: row.dataset.color || '',
                size: row.dataset.size || '',
                status: row.dataset.status || ''
            }));

            // Event listener para la búsqueda en tiempo real
            searchInput.addEventListener('input', function() {
                currentSearchTerm = this.value.toLowerCase().trim();
                performSearch();
                updateClearButton();
            });

            // Event listener para limpiar búsqueda
            clearButton.addEventListener('click', function() {
                clearSearch();
            });

            // Permitir limpiar con Escape
            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    clearSearch();
                }
            });
        }

        // Función para realizar la búsqueda
        function performSearch() {
            if (currentSearchTerm === '') {
                showAllProducts();
                return;
            }

            let visibleCount = 0;
            let hasProducts = allProducts.length > 0;

            allProducts.forEach(product => {
                const isMatch = 
                    product.name.includes(currentSearchTerm) ||
                    product.id.includes(currentSearchTerm) ||
                    product.category.includes(currentSearchTerm) ||
                    product.color.includes(currentSearchTerm) ||
                    product.size.includes(currentSearchTerm) ||
                    product.status.includes(currentSearchTerm);

                if (isMatch) {
                    product.element.style.display = '';
                    highlightSearchTerm(product.element, currentSearchTerm);
                    visibleCount++;
                } else {
                    product.element.style.display = 'none';
                    removeHighlights(product.element);
                }
            });

            // Mostrar información de resultados
            updateSearchResults(visibleCount, currentSearchTerm);
            
            // Mostrar mensaje de "no resultados" si es necesario
            const noResultsRow = document.getElementById('noResults');
            const emptyRow = document.querySelector('.empty-row');
            
            if (hasProducts && visibleCount === 0) {
                noResultsRow.classList.add('show');
                if (emptyRow) emptyRow.style.display = 'none';
            } else {
                noResultsRow.classList.remove('show');
                if (emptyRow && allProducts.length === 0) {
                    emptyRow.style.display = '';
                }
            }
        }

        // Función para mostrar todos los productos
        function showAllProducts() {
            allProducts.forEach(product => {
                product.element.style.display = '';
                removeHighlights(product.element);
            });
            
            // Ocultar información de resultados
            const searchResultsInfo = document.getElementById('searchResultsInfo');
            searchResultsInfo.classList.remove('show');
            
            // Ocultar mensaje de no resultados
            const noResultsRow = document.getElementById('noResults');
            noResultsRow.classList.remove('show');
            
            // Mostrar fila vacía si no hay productos
            const emptyRow = document.querySelector('.empty-row');
            if (emptyRow && allProducts.length === 0) {
                emptyRow.style.display = '';
            }
        }

        // Función para resaltar términos de búsqueda
        function highlightSearchTerm(row, searchTerm) {
            if (!searchTerm) return;

            const textElements = [
                row.querySelector('.product-name'),
                row.querySelector('.product-id'),
                row.querySelector('.category-cell'),
                row.querySelector('.color-cell'),
                row.querySelector('.size-cell'),
                row.querySelector('.status-badge')
            ];

            textElements.forEach(element => {
                if (element && element.textContent) {
                    const originalText = element.getAttribute('data-original-text') || element.textContent;
                    element.setAttribute('data-original-text', originalText);
                    
                    const regex = new RegExp(`(${escapeRegExp(searchTerm)})`, 'gi');
                    const highlightedText = originalText.replace(regex, '<span class="highlight">$1</span>');
                    element.innerHTML = highlightedText;
                }
            });
        }

        // Función para remover resaltados
        function removeHighlights(row) {
            const textElements = [
                row.querySelector('.product-name'),
                row.querySelector('.product-id'),
                row.querySelector('.category-cell'),
                row.querySelector('.color-cell'),
                row.querySelector('.size-cell'),
                row.querySelector('.status-badge')
            ];

            textElements.forEach(element => {
                if (element && element.getAttribute('data-original-text')) {
                    element.textContent = element.getAttribute('data-original-text');
                    element.removeAttribute('data-original-text');
                }
            });
        }

        // Función para escapar caracteres especiales en regex
        function escapeRegExp(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\                                <th>Talla</th>');
        }

        // Función para actualizar información de resultados
        function updateSearchResults(count, searchTerm) {
            const searchResultsInfo = document.getElementById('searchResultsInfo');
            const resultsCount = document.getElementById('resultsCount');
            const searchTermSpan = document.getElementById('searchTerm');

            if (searchTerm && count >= 0) {
                resultsCount.textContent = count;
                searchTermSpan.textContent = searchTerm;
                searchResultsInfo.classList.add('show');
            } else {
                searchResultsInfo.classList.remove('show');
            }
        }

        // Función para actualizar botón de limpiar
        function updateClearButton() {
            const clearButton = document.getElementById('clearSearch');
            const searchInput = document.getElementById('searchInput');
            
            if (searchInput.value.length > 0) {
                clearButton.style.display = 'block';
            } else {
                clearButton.style.display = 'none';
            }
        }

        // Función para limpiar búsqueda
        function clearSearch() {
            const searchInput = document.getElementById('searchInput');
            searchInput.value = '';
            currentSearchTerm = '';
            showAllProducts();
            updateClearButton();
            searchInput.focus();
        }

        // Manejo del sidebar
        const burgerIcon = document.getElementById('burgerIcon');
        const barraSidebar = document.getElementById('barraSidebar');
        const overlay = document.getElementById('overlay');

        function toggleSidebar() {
            burgerIcon.classList.toggle('activo');
            
            if (window.innerWidth <= 768) {
                barraSidebar.classList.toggle('activa');
                overlay.classList.toggle('activo');
            } else {
                barraSidebar.classList.toggle('oculta');
            }
        }

        burgerIcon.addEventListener('click', toggleSidebar);
        overlay.addEventListener('click', toggleSidebar);

        // Ajustar sidebar en redimensionamiento de ventana
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                overlay.classList.remove('activo');
                barraSidebar.classList.remove('activa');
            } else {
                barraSidebar.classList.remove('oculta');
            }
        });

        // Animación de entrada para las estadísticas
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        });

        document.querySelectorAll('.inventory-stat-item').forEach(item => {
            observer.observe(item);
        });

        // Inicializar cuando el DOM esté listo
        document.addEventListener('DOMContentLoaded', function() {
            initializeSearch();
        });

        // Auto-ocultar mensajes después de 5 segundos
        document.addEventListener('DOMContentLoaded', function() {
            const messages = document.querySelectorAll('.messages li');
            messages.forEach(message => {
                setTimeout(() => {
                    message.style.opacity = '0';
                    message.style.transform = 'translateX(100%)';
                    setTimeout(() => {
                        message.remove();
                    }, 300);
                }, 5000);
            });
        });
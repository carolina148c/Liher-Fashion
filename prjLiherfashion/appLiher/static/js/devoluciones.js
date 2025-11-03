// Variables para el filtrado
let currentFilter = 'all';
let allRows = [];

// Inicializar cuando la página carga
document.addEventListener('DOMContentLoaded', function() {
    // Almacenar todas las filas de la tabla
    allRows = Array.from(document.querySelectorAll('.table tbody tr'));
    
    // Configurar eventos para las tarjetas de estadísticas
    setupStatCards();
    
    // Configurar eventos para botones y filtros
    setupFilterButtons();
    
    // Configurar efectos hover para filas
    setupTableHoverEffects();
});

// Configurar las tarjetas de estadísticas como filtros
function setupStatCards() {
    const statCards = document.querySelectorAll('.stat-card');
    
    statCards.forEach(card => {
        card.addEventListener('click', function() {
            const filterType = this.getAttribute('data-filter');
            
            // Remover clase active de todas las tarjetas
            statCards.forEach(c => c.classList.remove('active'));
            
            // Si se hace clic en la misma tarjeta, mostrar todas las filas
            if (currentFilter === filterType) {
                currentFilter = 'all';
                showAllRows();
                resetFilterSelect();
            } else {
                // Agregar clase active a la tarjeta seleccionada
                this.classList.add('active');
                currentFilter = filterType;
                filterTableByStatus(filterType);
                // También actualizar el select de filtros
                updateFilterSelect(filterType);
            }
        });
    });
}

// Configurar botones de filtro
function setupFilterButtons() {
    // Botón aplicar filtros
    document.querySelector('.btn-primary').addEventListener('click', function() {
        // Obtener valores de los filtros
        const estadoSelect = document.querySelector('.form-select');
        const clienteInput = document.querySelector('input[placeholder="Buscar por cliente"]');
        const pedidoInput = document.querySelector('input[placeholder="Ej. ORD-001"]');
        
        console.log('Aplicando filtros:', {
            estado: estadoSelect.value,
            cliente: clienteInput.value,
            pedido: pedidoInput.value
        });
        
        // Aquí puedes agregar más lógica de filtrado
        applyAllFilters();
    });

    // Botón limpiar filtros
    document.querySelector('.btn-secondary').addEventListener('click', function() {
        clearAllFilters();
    });

    // Sincronizar el select con las tarjetas de estadísticas
    document.querySelector('.form-select').addEventListener('change', function() {
        const selectedStatus = this.value.toLowerCase();
        const statCards = document.querySelectorAll('.stat-card');
        
        // Remover todas las clases active
        statCards.forEach(card => card.classList.remove('active'));
        
        if (selectedStatus === 'todos los estados') {
            currentFilter = 'all';
            showAllRows();
        } else {
            // Encontrar y activar la tarjeta correspondiente
            statCards.forEach(card => {
                const cardFilter = card.getAttribute('data-filter');
                if (selectedStatus.includes(cardFilter) || 
                    (cardFilter === 'proceso' && selectedStatus.includes('proceso'))) {
                    card.classList.add('active');
                    currentFilter = cardFilter;
                    filterTableByStatus(cardFilter);
                }
            });
        }
    });
}

// Filtrar tabla por estado
function filterTableByStatus(status) {
    allRows.forEach(row => {
        const statusBadge = row.querySelector('.status-badge');
        if (statusBadge) {
            const rowStatus = statusBadge.textContent.toLowerCase().trim();
            
            if (status === 'proceso' && rowStatus === 'en proceso') {
                row.style.display = '';
            } else if (rowStatus.includes(status.toLowerCase())) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

// Mostrar todas las filas
function showAllRows() {
    allRows.forEach(row => {
        row.style.display = '';
    });
}

// Actualizar el select de filtros
function updateFilterSelect(status) {
    const select = document.querySelector('.form-select');
    const statusMap = {
        'pendiente': 'Pendiente',
        'aprobada': 'Aprobada', 
        'rechazada': 'Rechazada',
        'proceso': 'En proceso'
    };
    
    // Buscar la opción correspondiente
    for (let option of select.options) {
        if (option.text === statusMap[status]) {
            option.selected = true;
            break;
        }
    }
}

// Resetear el select de filtros
function resetFilterSelect() {
    const select = document.querySelector('.form-select');
    select.selectedIndex = 0;
}

// Aplicar todos los filtros (función expandible)
function applyAllFilters() {
    const estadoSelect = document.querySelector('.form-select');
    const clienteInput = document.querySelector('input[placeholder="Buscar por cliente"]');
    const pedidoInput = document.querySelector('input[placeholder="Ej. ORD-001"]');
    
    const filters = {
        estado: estadoSelect.value,
        cliente: clienteInput.value.toLowerCase(),
        pedido: pedidoInput.value.toLowerCase()
    };
    
    allRows.forEach(row => {
        let shouldShow = true;
        
        // Filtro por estado
        if (filters.estado && filters.estado !== 'Todos los estados') {
            const statusBadge = row.querySelector('.status-badge');
            const rowStatus = statusBadge ? statusBadge.textContent.trim() : '';
            if (rowStatus !== filters.estado) {
                shouldShow = false;
            }
        }
        
        // Filtro por cliente
        if (filters.cliente) {
            const clientName = row.querySelector('.client-name');
            const clientText = clientName ? clientName.textContent.toLowerCase() : '';
            if (!clientText.includes(filters.cliente)) {
                shouldShow = false;
            }
        }
        
        // Filtro por número de pedido
        if (filters.pedido) {
            const pedidoCell = row.cells[0];
            const pedidoText = pedidoCell ? pedidoCell.textContent.toLowerCase() : '';
            if (!pedidoText.includes(filters.pedido)) {
                shouldShow = false;
            }
        }
        
        row.style.display = shouldShow ? '' : 'none';
    });
}

// Limpiar todos los filtros
function clearAllFilters() {
    // Limpiar todos los campos de filtro
    document.querySelectorAll('.form-input, .form-select').forEach(input => {
        if (input.type === 'date') {
            input.value = '';
        } else {
            input.value = '';
            if (input.tagName === 'SELECT') {
                input.selectedIndex = 0;
            }
        }
    });
    
    // Remover filtros activos y mostrar todas las filas
    document.querySelectorAll('.stat-card').forEach(card => {
        card.classList.remove('active');
    });
    currentFilter = 'all';
    showAllRows();
}

// Configurar efectos hover para las filas de la tabla
function setupTableHoverEffects() {
    document.querySelectorAll('.table tbody tr').forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(2px)';
            this.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
            this.style.boxShadow = 'none';
        });
    });
}

// Función adicional para búsqueda en tiempo real (opcional)
function setupRealTimeSearch() {
    const clienteInput = document.querySelector('input[placeholder="Buscar por cliente"]');
    const pedidoInput = document.querySelector('input[placeholder="Ej. ORD-001"]');
    
    [clienteInput, pedidoInput].forEach(input => {
        if (input) {
            input.addEventListener('input', debounce(applyAllFilters, 300));
        }
    });
}

// Función debounce para optimizar búsquedas en tiempo real
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Activar búsqueda en tiempo real (descomenta la siguiente línea si la quieres)
// setupRealTimeSearch();




        // Variables globales
        let currentFilter = 'all';
        let allRows = [];

        // Inicializar cuando la página carga
        document.addEventListener('DOMContentLoaded', function() {
            // Almacenar todas las filas de la tabla
            allRows = Array.from(document.querySelectorAll('.table tbody tr'));
            
            // Configurar sidebar
            setupSidebar();
            
            // Configurar eventos para las tarjetas de estadísticas
            setupStatCards();
            
            // Configurar eventos para botones y filtros
            setupFilterButtons();
            
            // Configurar efectos hover para filas
            setupTableHoverEffects();
        });

        // Configurar sidebar y responsividad
        function setupSidebar() {
            const toggleBtn = document.getElementById('toggleSidebar');
            const sidebar = document.getElementById('barraSidebar');
            const overlay = document.getElementById('overlay');
            const contenido = document.getElementById('contenidoPrincipal');

            // Toggle sidebar en móvil
            toggleBtn.addEventListener('click', function() {
                sidebar.classList.toggle('mostrar');
                overlay.classList.toggle('activo');
            });

            // Cerrar sidebar al hacer clic en overlay
            overlay.addEventListener('click', function() {
                sidebar.classList.remove('mostrar');
                overlay.classList.remove('activo');
            });

            // Cerrar sidebar al hacer clic en un enlace (en móvil)
            document.querySelectorAll('.menu-barra a').forEach(link => {
                link.addEventListener('click', function() {
                    if (window.innerWidth <= 768) {
                        sidebar.classList.remove('mostrar');
                        overlay.classList.remove('activo');
                    }
                });
            });
        }

        // Configurar las tarjetas de estadísticas como filtros
        function setupStatCards() {
            const statCards = document.querySelectorAll('.stat-card');
            
            statCards.forEach(card => {
                card.addEventListener('click', function() {
                    const filterType = this.getAttribute('data-filter');
                    
                    // Remover clase active de todas las tarjetas
                    statCards.forEach(c => c.classList.remove('active'));
                    
                    // Si se hace clic en la misma tarjeta, mostrar todas las filas
                    if (currentFilter === filterType) {
                        currentFilter = 'all';
                        showAllRows();
                        resetFilterSelect();
                    } else {
                        // Agregar clase active a la tarjeta seleccionada
                        this.classList.add('active');
                        currentFilter = filterType;
                        filterTableByStatus(filterType);
                        // También actualizar el select de filtros
                        updateFilterSelect(filterType);
                    }
                });
            });
        }

        // Configurar botones de filtro
        function setupFilterButtons() {
            // Botón aplicar filtros
            document.querySelector('.btn-primary').addEventListener('click', function() {
                applyAllFilters();
            });

            // Botón limpiar filtros
            document.querySelector('.btn-secondary').addEventListener('click', function() {
                clearAllFilters();
            });

            // Sincronizar el select con las tarjetas de estadísticas
            document.querySelector('.form-select').addEventListener('change', function() {
                const selectedStatus = this.value.toLowerCase();
                const statCards = document.querySelectorAll('.stat-card');
                
                // Remover todas las clases active
                statCards.forEach(card => card.classList.remove('active'));
                
                if (selectedStatus === 'todos los estados') {
                    currentFilter = 'all';
                    showAllRows();
                } else {
                    // Encontrar y activar la tarjeta correspondiente
                    statCards.forEach(card => {
                        const cardFilter = card.getAttribute('data-filter');
                        if (selectedStatus.includes(cardFilter) || 
                            (cardFilter === 'proceso' && selectedStatus.includes('proceso'))) {
                            card.classList.add('active');
                            currentFilter = cardFilter;
                            filterTableByStatus(cardFilter);
                        }
                    });
                }
            });
        }

        // Filtrar tabla por estado
        function filterTableByStatus(status) {
            allRows.forEach(row => {
                const statusBadge = row.querySelector('.status-badge');
                if (statusBadge) {
                    const rowStatus = statusBadge.textContent.toLowerCase().trim();
                    
                    if (status === 'proceso' && rowStatus === 'en proceso') {
                        row.style.display = '';
                    } else if (rowStatus.includes(status.toLowerCase())) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        }

        // Mostrar todas las filas
        function showAllRows() {
            allRows.forEach(row => {
                row.style.display = '';
            });
        }

        // Actualizar el select de filtros
        function updateFilterSelect(status) {
            const select = document.querySelector('.form-select');
            const statusMap = {
                'pendiente': 'Pendiente',
                'aprobada': 'Aprobada', 
                'rechazada': 'Rechazada',
                'proceso': 'En proceso'
            };
            
            // Buscar la opción correspondiente
            for (let option of select.options) {
                if (option.text === statusMap[status]) {
                    option.selected = true;
                    break;
                }
            }
        }

        // Resetear el select de filtros
        function resetFilterSelect() {
            const select = document.querySelector('.form-select');
            select.selectedIndex = 0;
        }

        // Aplicar todos los filtros
        function applyAllFilters() {
            const estadoSelect = document.querySelector('.form-select');
            const clienteInput = document.querySelector('input[placeholder="Buscar por cliente"]');
            const pedidoInput = document.querySelector('input[placeholder="Ej. ORD-001"]');
            
            const filters = {
                estado: estadoSelect.value,
                cliente: clienteInput.value.toLowerCase(),
                pedido: pedidoInput.value.toLowerCase()
            };
            
            allRows.forEach(row => {
                let shouldShow = true;
                
                // Filtro por estado
                if (filters.estado && filters.estado !== 'Todos los estados') {
                    const statusBadge = row.querySelector('.status-badge');
                    const rowStatus = statusBadge ? statusBadge.textContent.trim() : '';
                    if (rowStatus !== filters.estado) {
                        shouldShow = false;
                    }
                }
                
                // Filtro por cliente
                if (filters.cliente) {
                    const clientName = row.querySelector('.client-name');
                    const clientText = clientName ? clientName.textContent.toLowerCase() : '';
                    if (!clientText.includes(filters.cliente)) {
                        shouldShow = false;
                    }
                }
                
                // Filtro por número de pedido
                if (filters.pedido) {
                    const pedidoCell = row.cells[0];
                    const pedidoText = pedidoCell ? pedidoCell.textContent.toLowerCase() : '';
                    if (!pedidoText.includes(filters.pedido)) {
                        shouldShow = false;
                    }
                }
                
                row.style.display = shouldShow ? '' : 'none';
            });
        }

        // Limpiar todos los filtros
        function clearAllFilters() {
            // Limpiar todos los campos de filtro
            document.querySelectorAll('.form-input, .form-select').forEach(input => {
                if (input.type === 'date') {
                    input.value = '';
                } else {
                    input.value = '';
                    if (input.tagName === 'SELECT') {
                        input.selectedIndex = 0;
                    }
                }
            });
            
            // Remover filtros activos y mostrar todas las filas
            document.querySelectorAll('.stat-card').forEach(card => {
                card.classList.remove('active');
            });
            currentFilter = 'all';
            showAllRows();
        }

        // Configurar efectos hover para las filas de la tabla
        function setupTableHoverEffects() {
            // Los efectos hover ya están definidos en CSS
            // Esta función se mantiene para consistencia con el código original
        }
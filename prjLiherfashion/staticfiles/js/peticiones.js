        // Datos de peticiones (simulación de base de datos)
let petitions = [
    {
        id: '#PET-001',
        product: 'Blusa estampada floral',
        ref: 'REF: SL5001 • M • Negro',
        user: 'Manuela Vasquez Herrera',
        email: 'manuela.333@gmail.com',
        quantity: 20,
        date: '07/06/2025',
        status: 'Pendiente'
    },
    {
        id: '#PET-002',
        product: 'Blusa estampada floral',
        ref: 'REF: SL5001 • M • Negro',
        user: 'Manuela Vasquez Herrera',
        email: 'manuela.333@gmail.com',
        quantity: 20,
        date: '07/06/2025',
        status: 'En revisión'
    },
    {
        id: '#PET-003',
        product: 'Blusa estampada floral',
        ref: 'REF: SL5001 • M • Negro',
        user: 'Manuela Vasquez Herrera',
        email: 'manuela.333@gmail.com',
        quantity: 20,
        date: '07/06/2025',
        status: 'Aceptada'
    },
    {
        id: '#PET-004',
        product: 'Blusa estampada floral',
        ref: 'REF: SL5001 • M • Negro',
        user: 'Manuela Vasquez Herrera',
        email: 'manuela.333@gmail.com',
        quantity: 20,
        date: '07/06/2025',
        status: 'Rechazada'
    },
    {
        id: '#PET-005',
        product: 'Blusa estampada floral',
        ref: 'REF: SL5001 • M • Negro',
        user: 'Manuela Vasquez Herrera',
        email: 'manuela.333@gmail.com',
        quantity: 20,
        date: '07/06/2025',
        status: 'Respondida'
    }
];

// Variables para paginación y filtros
let currentPage = 1;
const itemsPerPage = 5;
let filteredPetitions = [...petitions];

// Obtener la clase CSS para cada estado
function getStatusClass(status) {
    const statusMap = {
        'Pendiente': 'status-pendiente',
        'En revisión': 'status-revision',
        'Aceptada': 'status-aceptada',
        'Rechazada': 'status-rechazada',
        'Respondida': 'status-respondida'
    };
    return statusMap[status] || 'status-pendiente';
}

// Renderizar tabla
function renderTable() {
    const tbody = document.getElementById('petitions-tbody');
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const paginatedData = filteredPetitions.slice(start, end);

    tbody.innerHTML = '';

    paginatedData.forEach((petition, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="petition-id">${petition.id}</td>
            <td>
                <div class="product-info">
                    <span class="product-name">${petition.product}</span>
                    <span class="product-ref">${petition.ref}</span>
                </div>
            </td>
            <td>
                <div class="user-info">
                    <span class="user-name">${petition.user}</span>
                    <span class="user-email">${petition.email}</span>
                </div>
            </td>
            <td>${petition.quantity}</td>
            <td>${petition.date}</td>
            <td><span class="status-badge ${getStatusClass(petition.status)}">${petition.status}</span></td>
            <td>
                <div class="actions-cell">
                    <button class="icon-btn view" onclick="viewDetails(${start + index})">
                        <svg class="eye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                    <div class="dropdown">
                        <button class="status-btn" onclick="toggleDropdown(${start + index})">${petition.status} ▼</button>
                        <div id="dropdown-${start + index}" class="dropdown-content">
                            <button onclick="changeStatus(${start + index}, 'Pendiente')">Pendiente</button>
                            <button onclick="changeStatus(${start + index}, 'En revisión')">En revisión</button>
                            <button onclick="changeStatus(${start + index}, 'Aceptada')">Aceptada</button>
                            <button onclick="changeStatus(${start + index}, 'Rechazada')">Rechazada</button>
                            <button onclick="changeStatus(${start + index}, 'Respondida')">Respondida</button>
                        </div>
                    </div>
                    <button class="icon-btn delete" onclick="deletePetition(${start + index})">🗑️</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    updatePaginationInfo();
    renderPagination();
}

// Toggle dropdown
function toggleDropdown(index) {
    const dropdown = document.getElementById(`dropdown-${index}`);
    
    // Cerrar todos los dropdowns
    document.querySelectorAll('.dropdown-content').forEach(dd => {
        if (dd !== dropdown) {
            dd.classList.remove('show');
        }
    });
    
    dropdown.classList.toggle('show');
}

// Cambiar estado
function changeStatus(index, newStatus) {
    filteredPetitions[index].status = newStatus;
    
    // Actualizar en el array principal
    const petitionId = filteredPetitions[index].id;
    const mainIndex = petitions.findIndex(p => p.id === petitionId);
    if (mainIndex !== -1) {
        petitions[mainIndex].status = newStatus;
    }
    
    renderTable();
    updateStats();
    
    // Cerrar dropdown
    document.getElementById(`dropdown-${index}`).classList.remove('show');
}

// Ver detalles
function viewDetails(index) {
    const petition = filteredPetitions[index];
    const modal = document.getElementById('modal-details');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <p><strong>ID:</strong> ${petition.id}</p>
        <p><strong>Producto:</strong> ${petition.product}</p>
        <p><strong>Referencia:</strong> ${petition.ref}</p>
        <p><strong>Usuario:</strong> ${petition.user}</p>
        <p><strong>Email:</strong> ${petition.email}</p>
        <p><strong>Cantidad:</strong> ${petition.quantity}</p>
        <p><strong>Fecha:</strong> ${petition.date}</p>
        <p><strong>Estado:</strong> <span class="status-badge ${getStatusClass(petition.status)}">${petition.status}</span></p>
    `;
    
    modal.style.display = 'block';
}

// Eliminar petición
function deletePetition(index) {
    if (confirm('¿Está seguro de eliminar esta petición?')) {
        const petitionId = filteredPetitions[index].id;
        
        // Eliminar del array filtrado
        filteredPetitions.splice(index, 1);
        
        // Eliminar del array principal
        const mainIndex = petitions.findIndex(p => p.id === petitionId);
        if (mainIndex !== -1) {
            petitions.splice(mainIndex, 1);
        }
        
        // Ajustar página si es necesario
        const totalPages = Math.ceil(filteredPetitions.length / itemsPerPage);
        if (currentPage > totalPages && totalPages > 0) {
            currentPage = totalPages;
        }
        
        renderTable();
        updateStats();
    }
}

// Actualizar información de paginación
function updatePaginationInfo() {
    const start = (currentPage - 1) * itemsPerPage + 1;
    const end = Math.min(currentPage * itemsPerPage, filteredPetitions.length);
    const total = filteredPetitions.length;
    
    document.getElementById('pagination-info').textContent = 
        `Mostrando ${start} - ${end} de ${total} peticiones`;
    document.getElementById('total-peticiones').textContent = `${total} peticiones`;
}

// Renderizar paginación
function renderPagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(filteredPetitions.length / itemsPerPage);
    
    pagination.innerHTML = '';
    
    // Botón anterior
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn';
    prevBtn.textContent = '< Anterior';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
        }
    };
    pagination.appendChild(prevBtn);
    
    // Páginas numeradas
    const maxPagesToShow = 5;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
    
    if (endPage - startPage < maxPagesToShow - 1) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = 'page-btn' + (i === currentPage ? ' active' : '');
        pageBtn.textContent = i;
        pageBtn.onclick = () => {
            currentPage = i;
            renderTable();
        };
        pagination.appendChild(pageBtn);
    }
    
    // Puntos suspensivos y última página
    if (endPage < totalPages) {
        const dots = document.createElement('span');
        dots.textContent = '...';
        pagination.appendChild(dots);
        
        const lastBtn = document.createElement('button');
        lastBtn.className = 'page-btn';
        lastBtn.textContent = totalPages;
        lastBtn.onclick = () => {
            currentPage = totalPages;
            renderTable();
        };
        pagination.appendChild(lastBtn);
    }
    
    // Botón siguiente
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.textContent = 'Siguiente >';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderTable();
        }
    };
    pagination.appendChild(nextBtn);
}

// Aplicar filtros
function applyFilters() {
    const petitionFilter = document.getElementById('filter-petition').value.toLowerCase();
    const userFilter = document.getElementById('filter-user').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    const dateFromFilter = document.getElementById('filter-date-from').value;
    const dateToFilter = document.getElementById('filter-date-to').value;
    
    filteredPetitions = petitions.filter(petition => {
        const matchesPetition = !petitionFilter || petition.id.toLowerCase().includes(petitionFilter);
        const matchesUser = !userFilter || 
            petition.user.toLowerCase().includes(userFilter) || 
            petition.email.toLowerCase().includes(userFilter);
        const matchesStatus = !statusFilter || petition.status === statusFilter;
        
        // Conversión simple de fecha para comparación
        let matchesDate = true;
        if (dateFromFilter || dateToFilter) {
            const petitionDate = new Date(petition.date.split('/').reverse().join('-'));
            if (dateFromFilter) {
                matchesDate = matchesDate && petitionDate >= new Date(dateFromFilter);
            }
            if (dateToFilter) {
                matchesDate = matchesDate && petitionDate <= new Date(dateToFilter);
            }
        }
        
        return matchesPetition && matchesUser && matchesStatus && matchesDate;
    });
    
    currentPage = 1;
    renderTable();
}

// Limpiar filtros
function clearFilters() {
    document.getElementById('filter-petition').value = '';
    document.getElementById('filter-user').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-dat-to').value = '';
    
    filteredPetitions = [...petitions];
    currentPage = 1;
    renderTable();
}

// Actualizar estadísticas
function updateStats() {
    const pendientes = petitions.filter(p => p.status === 'Pendiente').length;
    const revision = petitions.filter(p => p.status === 'En revisión').length;
    const aceptadas = petitions.filter(p => p.status === 'Aceptada').length;
    const rechazadas = petitions.filter(p => p.status === 'Rechazada').length;
    
    document.getElementById('stat-pendientes').textContent = pendientes;
    document.getElementById('stat-revision').textContent = revision;
    document.getElementById('stat-pendientes-2').textContent = aceptadas;
    document.getElementById('stat-cancelados').textContent = rechazadas;
}

// Event Listeners
document.getElementById('btn-apply-filters').addEventListener('click', applyFilters);
document.getElementById('btn-clear-filters').addEventListener('click', clearFilters);

// Cerrar modal
document.querySelector('.close').addEventListener('click', function() {
    document.getElementById('modal-details').style.display = 'none';
});

window.addEventListener('click', function(event) {
    const modal = document.getElementById('modal-details');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// Cerrar dropdowns al hacer clic fuera
window.addEventListener('click', function(event) {
    if (!event.target.matches('.status-btn')) {
        document.querySelectorAll('.dropdown-content').forEach(dd => {
            dd.classList.remove('show');
        });
    }
});

// Filtros en tiempo real (opcional)
document.getElementById('filter-petition').addEventListener('input', function() {
    if (this.value.length === 0 || this.value.length >= 3) {
        applyFilters();
    }
});

document.getElementById('filter-user').addEventListener('input', function() {
    if (this.value.length === 0 || this.value.length >= 3) {
        applyFilters();
    }
});

document.getElementById('filter-status').addEventListener('change', applyFilters);

// Actualizar tiempo
function updateTime() {
    const now = new Date();
    const minutes = Math.floor(Math.random() * 10) + 1;
    document.getElementById('last-update').textContent = `Última actualización: hace ${minutes} minutos`;
}

// Actualizar cada minuto
setInterval(updateTime, 60000);

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    renderTable();
    updateStats();
});

// Función para agregar más peticiones de prueba (opcional)
function addSamplePetitions() {
    const statuses = ['Pendiente', 'En revisión', 'Aceptada', 'Rechazada', 'Respondida'];
    const products = [
        'Blusa estampada floral',
        'Camisa de lino',
        'Vestido casual',
        'Pantalón de mezclilla',
        'Falda plisada'
    ];
    const users = [
        { name: 'María González', email: 'maria.g@gmail.com' },
        { name: 'Juan Pérez', email: 'juan.p@hotmail.com' },
        { name: 'Ana Martínez', email: 'ana.m@yahoo.com' },
        { name: 'Carlos Rodríguez', email: 'carlos.r@gmail.com' },
        { name: 'Laura Sánchez', email: 'laura.s@outlook.com' }
    ];
    
    for (let i = 6; i <= 73; i++) {
        const user = users[Math.floor(Math.random() * users.length)];
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        const product = products[Math.floor(Math.random() * products.length)];
        
        petitions.push({
            id: `#PET-${String(i).padStart(3, '0')}`,
            product: product,
            ref: `REF: SL${5000 + i} • ${['S', 'M', 'L', 'XL'][Math.floor(Math.random() * 4)]} • ${['Negro', 'Blanco', 'Azul', 'Rojo'][Math.floor(Math.random() * 4)]}`,
            user: user.name,
            email: user.email,
            quantity: Math.floor(Math.random() * 50) + 1,
            date: `${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}/06/2025`,
            status: status
        });
    }
    
    filteredPetitions = [...petitions];
    renderTable();
    updateStats();
}

// Llamar a esta función si quieres agregar más datos de prueba
addSamplePetitions();
// Filtrar por estado desde las tarjetas estadísticas
function filterByStatus(status) {
    document.getElementById('filter-status').value = status;
    applyFilters();
    
    // Scroll suave hacia la tabla
    document.querySelector('.table-container').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
    });
}

// Actualizar la función updateStats para incluir las aceptadas
function updateStats() {
    const pendientes = petitions.filter(p => p.status === 'Pendiente').length;
    const revision = petitions.filter(p => p.status === 'En revisión').length;
    const aceptadas = petitions.filter(p => p.status === 'Aceptada').length;
    const rechazadas = petitions.filter(p => p.status === 'Rechazada').length;
    
    document.getElementById('stat-pendientes').textContent = pendientes;
    document.getElementById('stat-revision').textContent = revision;
    document.getElementById('stat-aceptadas').textContent = aceptadas;
    document.getElementById('stat-rechazadas').textContent = rechazadas;
}
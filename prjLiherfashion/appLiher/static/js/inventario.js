// ===== CATALOGO.JS - PARA AGREGAR PRODUCTO Y VARIANTES =====

let selectedColors = [];
let variantesGeneradas = [];
let editIndex = null;
let stockData = {};

// Mapa de colores para los indicadores visuales
const colorMap = {
    'Rojo': '#dc3545',
    'Azul': '#007bff',
    'Negro': '#343a40',
    'Blanco': '#ffffff',
    'Verde': '#28a745',
    'Amarillo': '#ffc107',
    'Rosa': '#ff4081',
    'Gris': '#6c757d',
    'Morado': '#6f42c1',
    'Naranja': '#fd7e14',
    'Cafe': '#795548',
    'Beige': '#d7ccc8'
};

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    initImagePreview();
    initModalVariantes();
});

// ===== PREVIEW DE IMAGEN PRINCIPAL =====
function initImagePreview() {
    const fileInput = document.querySelector('input[type="file"][name="imagen"]');
    const imagePreview = document.querySelector('.image-preview');
    
    if (!fileInput || !imagePreview) return;
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            // Validar que sea una imagen
            if (!file.type.startsWith('image/')) {
                alert('Por favor selecciona un archivo de imagen válido (JPG, PNG o GIF)');
                fileInput.value = '';
                imagePreview.innerHTML = '';
                return;
            }
            
            // Validar tamaño (máximo 5MB)
            const maxSize = 5 * 1024 * 1024; // 5MB en bytes
            if (file.size > maxSize) {
                alert('La imagen no debe superar los 5MB. Tamaño actual: ' + (file.size / (1024 * 1024)).toFixed(2) + 'MB');
                fileInput.value = '';
                imagePreview.innerHTML = '';
                return;
            }
            
            // Mostrar indicador de carga
            imagePreview.classList.add('loading');
            imagePreview.innerHTML = '';
            
            // Crear preview
            const reader = new FileReader();
            
            reader.onload = function(event) {
                imagePreview.classList.remove('loading');
                imagePreview.innerHTML = '';
                
                const img = document.createElement('img');
                img.src = event.target.result;
                img.alt = 'Vista previa';
                img.style.cssText = `
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 6px;
                `;
                
                imagePreview.appendChild(img);
            };
            
            reader.onerror = function() {
                imagePreview.classList.remove('loading');
                alert('Error al cargar la imagen. Por favor intenta de nuevo.');
                imagePreview.innerHTML = '';
                fileInput.value = '';
            };
            
            reader.readAsDataURL(file);
        } else {
            // Si se cancela la selección, limpiar preview
            imagePreview.innerHTML = '';
        }
    });
}

// ===== INICIALIZAR MODAL DE VARIANTES =====
function initModalVariantes() {
    const btnAbrir = document.getElementById("btnAbrirModal");
    const modal = document.getElementById("modalVariante");
    
    if (!btnAbrir || !modal) return;
    
    btnAbrir.addEventListener("click", () => {
        modal.classList.remove("hidden");
        editIndex = null; // Asegurar que no estamos en modo edición
    });
}

// ELEMENTOS
const modal = document.getElementById("modalVariante");
const stockGrid = document.getElementById("stockGrid");
const previewGrid = document.getElementById("previewGrid");

// CERRAR MODAL
function cerrarModal() {
    if (confirm('¿Estás seguro de que deseas cerrar sin guardar?')) {
        modal.classList.add("hidden");
        limpiarModal();
    }
}

function limpiarModal() {
    document.getElementById("tallaSelect").value = "";
    document.getElementById("colorSelect").value = "";
    selectedColors = [];
    stockData = {};
    document.getElementById("colorTags").innerHTML = "";
    if (stockGrid) stockGrid.innerHTML = "";
    if (previewGrid) {
        previewGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #999; padding: 20px;">Seleccione una talla y colores para ver la vista previa</div>';
    }
    editIndex = null;
}

// AGREGAR COLOR
function addColor() {
    const select = document.getElementById("colorSelect");
    const color = select.value;

    if (!color || selectedColors.includes(color)) {
        select.value = "";
        return;
    }

    selectedColors.push(color);
    select.value = "";

    actualizarColorTags();
    generarStockInputs();
    generarPreview();
}

// REMOVER COLOR
function removeColor(color) {
    selectedColors = selectedColors.filter(c => c !== color);
    delete stockData[color];
    actualizarColorTags();
    generarStockInputs();
    generarPreview();
}

// ACTUALIZAR TAGS DE COLORES
function actualizarColorTags() {
    const container = document.getElementById("colorTags");
    
    if (selectedColors.length === 0) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = selectedColors.map(color => `
        <div class="color-tag">
            ${color}
            <button type="button" class="color-tag-remove" onclick="removeColor('${color}')">×</button>
        </div>
    `).join('');
}

// GENERAR INPUTS DE STOCK CON DISEÑO MEJORADO
function generarStockInputs() {
    if (!stockGrid || selectedColors.length === 0) {
        if (stockGrid) stockGrid.innerHTML = "";
        return;
    }

    stockGrid.innerHTML = selectedColors.map(color => {
        const colorHex = colorMap[color] || '#999';
        const stockValue = stockData[color] || '';
        
        return `
            <div class="stock-card">
                <div class="stock-card-header">
                    <span class="color-indicator" style="background-color: ${colorHex};"></span>
                    ${color}
                </div>
                <label style="font-size: 12px; color: #666; margin-bottom: 4px; display: block;">
                    Stock <span class="required">*</span>
                </label>
                <input 
                    type="number" 
                    class="stock-input" 
                    placeholder="Ingrese cantidad" 
                    min="0"
                    value="${stockValue}"
                    onchange="updateStock('${color}', this.value)"
                    id="stock_${color}"
                >
                <button type="button" class="upload-btn">
                    📎 Subir Imagen
                </button>
                <div class="optional-text">Opcional</div>
            </div>
        `;
    }).join('');
}

// ACTUALIZAR STOCK
function updateStock(color, value) {
    stockData[color] = value;
    generarPreview();
}

// GENERAR PREVIEW
function generarPreview() {
    if (!previewGrid) return;
    
    const talla = document.getElementById("tallaSelect").value;
    
    if (!talla || selectedColors.length === 0) {
        previewGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #999; padding: 20px;">Seleccione una talla y colores para ver la vista previa</div>';
        return;
    }

    previewGrid.innerHTML = selectedColors.map(color => {
        const stock = stockData[color] || '0';
        return `
            <div class="preview-card">
                <div class="preview-card-title">${talla} - ${color}</div>
                <div class="preview-card-stock">Stock: ${stock} unidades</div>
            </div>
        `;
    }).join('');
}

// GUARDAR VARIANTES
function guardarVariantes() {
    const talla = document.getElementById("tallaSelect").value;

    // Validaciones
    if (!talla) {
        alert("Por favor selecciona una talla");
        return;
    }

    if (selectedColors.length === 0) {
        alert("Por favor agrega al menos un color");
        return;
    }

    // Validar stock para cada color
    let todoOk = true;
    for (const color of selectedColors) {
        const stock = stockData[color];
        if (!stock || stock === '0' || stock < 0) {
            alert(`Por favor ingresa un stock válido para el color ${color}`);
            todoOk = false;
            break;
        }
    }

    if (!todoOk) return;

    // Guardar las variantes
    selectedColors.forEach(color => {
        const stock = stockData[color];

        if (editIndex !== null) {
            // Modo edición
            variantesGeneradas[editIndex] = { talla, color, stock };
        } else {
            // Verificar si ya existe
            const existe = variantesGeneradas.some(v => v.talla === talla && v.color === color);
            if (existe) {
                alert(`La variante ${talla} - ${color} ya existe`);
                return;
            }

            variantesGeneradas.push({ talla, color, stock });
        }
    });

    cerrarModalExitoso();
    renderVariantes();
    actualizarContadorVariantes();
    inyectarInputsHidden();
}

// CERRAR MODAL EXITOSAMENTE (sin confirmación)
function cerrarModalExitoso() {
    if (modal) modal.classList.add("hidden");
    limpiarModal();
}

// RENDERIZAR LISTA DE VARIANTES
function renderVariantes() {
    const variantsSection = document.querySelector(".variants-section");
    if (!variantsSection) return;
    
    const emptyState = document.querySelector(".empty-state");
    
    // Remover estado vacío si existe
    if (emptyState && variantesGeneradas.length > 0) {
        emptyState.remove();
    }

    // Buscar o crear contenedor de lista
    let lista = document.getElementById("variantesLista");
    
    if (!lista) {
        lista = document.createElement("div");
        lista.id = "variantesLista";
        lista.style.cssText = `
            display: grid;
            gap: 12px;
            margin-top: 16px;
        `;
        variantsSection.appendChild(lista);
    }

    // Si no hay variantes, mostrar estado vacío
    if (variantesGeneradas.length === 0) {
        lista.innerHTML = "";
        
        // Verificar si ya existe un empty-state antes de agregar uno nuevo
        if (!variantsSection.querySelector('.empty-state')) {
            const emptyStateDiv = document.createElement('div');
            emptyStateDiv.className = 'empty-state';
            emptyStateDiv.innerHTML = `
                <div class="empty-icon">📦</div>
                <div class="empty-title">No hay variantes agregadas</div>
                <div class="empty-subtitle">Haz clic en "Agregar Nueva Variante" para comenzar</div>
            `;
            variantsSection.appendChild(emptyStateDiv);
        }
        return;
    }

    // Renderizar variantes
    lista.innerHTML = variantesGeneradas.map((v, i) => `
        <div style="
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div style="display: flex; gap: 24px; align-items: center;">
                <div>
                    <span style="font-size: 12px; color: #999;">Talla</span>
                    <div style="font-size: 14px; font-weight: 600; color: #333;">${v.talla}</div>
                </div>
                <div>
                    <span style="font-size: 12px; color: #999;">Color</span>
                    <div style="font-size: 14px; font-weight: 600; color: #333;">${v.color}</div>
                </div>
                <div>
                    <span style="font-size: 12px; color: #999;">Stock</span>
                    <div style="font-size: 14px; font-weight: 600; color: #ff4081;">${v.stock} unidades</div>
                </div>
            </div>
            <div style="display: flex; gap: 8px;">
                <button 
                    type="button"
                    onclick="editarVariante(${i})"
                    style="
                        background: white;
                        border: 1px solid #d0d0d0;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-size: 13px;
                        cursor: pointer;
                        transition: all 0.3s;
                    "
                    onmouseover="this.style.background='#f5f5f5'"
                    onmouseout="this.style.background='white'"
                >
                    ✏️ Editar
                </button>
                <button 
                    type="button"
                    onclick="eliminarVariante(${i})"
                    style="
                        background: #fff5f5;
                        border: 1px solid #ffcdd2;
                        color: #c62828;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-size: 13px;
                        cursor: pointer;
                        transition: all 0.3s;
                    "
                    onmouseover="this.style.background='#ffebee'"
                    onmouseout="this.style.background='#fff5f5'"
                >
                    🗑️ Eliminar
                </button>
            </div>
        </div>
    `).join('');
}

// EDITAR VARIANTE
function editarVariante(i) {
    const v = variantesGeneradas[i];
    editIndex = i;

    // Limpiar modal
    limpiarModal();
    
    // Abrir modal
    if (modal) modal.classList.remove("hidden");

    // Cargar datos de la variante
    document.getElementById("tallaSelect").value = v.talla;
    selectedColors = [v.color];
    stockData[v.color] = v.stock;

    // Actualizar interfaz
    actualizarColorTags();
    generarStockInputs();
    generarPreview();
}

// ELIMINAR VARIANTE
function eliminarVariante(i) {
    if (confirm('¿Estás seguro de eliminar esta variante?')) {
        variantesGeneradas.splice(i, 1);
        renderVariantes();
        actualizarContadorVariantes();
        inyectarInputsHidden();
    }
}

// ACTUALIZAR CONTADOR EN EL FOOTER
function actualizarContadorVariantes() {
    const footerInfo = document.querySelector(".footer-info");
    if (footerInfo) {
        const total = variantesGeneradas.length;
        footerInfo.textContent = `${total} Variante${total !== 1 ? 's' : ''}`;
    }
}

// INYECTAR INPUTS HIDDEN PARA DJANGO
function inyectarInputsHidden() {
    const form = document.querySelector("form");
    if (!form) return;

    // Remover inputs antiguos
    const old = document.getElementById("hiddenVariantes");
    if (old) old.remove();

    // Crear nuevo contenedor
    const container = document.createElement("div");
    container.id = "hiddenVariantes";

    // Agregar inputs hidden para cada variante
    variantesGeneradas.forEach((v, i) => {
        container.innerHTML += `
            <input type="hidden" name="variantes[${i}][talla]" value="${v.talla}">
            <input type="hidden" name="variantes[${i}][color]" value="${v.color}">
            <input type="hidden" name="variantes[${i}][stock]" value="${v.stock}">
        `;
    });

    form.appendChild(container);
}

console.log('✅ Catálogo JS (Agregar Producto) cargado correctamente');
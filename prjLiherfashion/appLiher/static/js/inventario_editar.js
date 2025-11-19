// ===== EDITAR_CATALOGO.JS - PARA EDITAR PRODUCTO Y VARIANTES =====

let selectedColors = [];
let variantesExistentes = [];
let variantesNuevas = [];
let variantesEditadas = new Map();
let variantesEliminadas = [];
let editIndex = null;
let stockData = {};
let imagenesData = {};

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
    cargarVariantesExistentes();
});

// ===== CARGAR VARIANTES EXISTENTES DESDE EL HTML =====
function cargarVariantesExistentes() {
    const variantCards = document.querySelectorAll('.variant-card');
    
    variantCards.forEach((card, index) => {
        const id = card.dataset.id;
        const talla = card.dataset.talla;
        const color = card.dataset.color;
        const stock = card.dataset.stock;
        const imagen = card.dataset.imagen || null;
        
        variantesExistentes.push({
            id: id,
            talla: talla,
            color: color,
            stock: stock,
            imagen: imagen,
            eliminada: false
        });
    });
    
    renderVariantesExistentes();
    actualizarContadorVariantes();
}

// ===== PREVIEW DE IMAGEN PRINCIPAL =====
function initImagePreview() {
    const fileInput = document.querySelector('input[type="file"][name="imagen"]');
    const imagePreview = document.querySelector('.image-preview');
    
    if (!fileInput || !imagePreview) return;
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            if (!file.type.startsWith('image/')) {
                alert('Por favor selecciona un archivo de imagen válido');
                fileInput.value = '';
                return;
            }
            
            const maxSize = 5 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('La imagen no debe superar los 5MB');
                fileInput.value = '';
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(event) {
                imagePreview.innerHTML = `<img src="${event.target.result}" alt="Vista previa">`;
            };
            reader.readAsDataURL(file);
        }
    });
}

// ===== MODAL =====
function initModalVariantes() {
    const btnAbrir = document.getElementById("btnAbrirModal");
    const modal = document.getElementById("modalVariante");
    
    if (!btnAbrir || !modal) return;
    
    btnAbrir.addEventListener("click", () => {
        modal.classList.remove("hidden");
        editIndex = null;
    });
}

const modal = document.getElementById("modalVariante");
const stockGrid = document.getElementById("stockGrid");
const previewGrid = document.getElementById("previewGrid");

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
    imagenesData = {};
    document.getElementById("colorTags").innerHTML = "";
    if (stockGrid) stockGrid.innerHTML = "";
    if (previewGrid) {
        previewGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #999; padding: 20px;">Seleccione una talla y colores para ver la vista previa</div>';
    }
    editIndex = null;
}

// ===== COLORES =====
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

function removeColor(color) {
    selectedColors = selectedColors.filter(c => c !== color);
    delete stockData[color];
    delete imagenesData[color];
    actualizarColorTags();
    generarStockInputs();
    generarPreview();
}

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

// ===== STOCK E IMÁGENES =====
function generarStockInputs() {
    if (!stockGrid || selectedColors.length === 0) {
        if (stockGrid) stockGrid.innerHTML = "";
        return;
    }

    stockGrid.innerHTML = selectedColors.map(color => {
        const colorHex = colorMap[color] || '#999';
        const stockValue = stockData[color] || '';
        const hasImage = imagenesData[color];
        
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
                <label class="upload-btn">
                    ${hasImage ? '✅' : '📎'} ${hasImage ? 'Imagen cargada' : 'Subir Imagen'}
                    <input type="file" accept="image/*" onchange="handleImageUpload('${color}', this)" hidden>
                </label>
                <div class="optional-text">Opcional</div>
            </div>
        `;
    }).join('');
}

function updateStock(color, value) {
    stockData[color] = value;
    generarPreview();
}

function handleImageUpload(color, input) {
    const file = input.files[0];
    if (file) {
        if (!file.type.startsWith('image/')) {
            alert('Por favor selecciona una imagen válida');
            input.value = '';
            return;
        }
        
        imagenesData[color] = file;
        generarStockInputs();
        generarPreview();
    }
}

// ===== PREVIEW =====
function generarPreview() {
    if (!previewGrid) return;
    
    const talla = document.getElementById("tallaSelect").value;
    
    if (!talla || selectedColors.length === 0) {
        previewGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #999; padding: 20px;">Seleccione una talla y colores para ver la vista previa</div>';
        return;
    }

    previewGrid.innerHTML = selectedColors.map(color => {
        const stock = stockData[color] || '0';
        const hasImage = imagenesData[color] ? '🖼️' : '';
        return `
            <div class="preview-card">
                <div class="preview-card-title">${talla} - ${color} ${hasImage}</div>
                <div class="preview-card-stock">Stock: ${stock} unidades</div>
            </div>
        `;
    }).join('');
}

// ===== GUARDAR NUEVAS VARIANTES =====
function guardarVariantes() {
    const talla = document.getElementById("tallaSelect").value;

    if (!talla) {
        alert("Por favor selecciona una talla");
        return;
    }

    if (selectedColors.length === 0) {
        alert("Por favor agrega al menos un color");
        return;
    }

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

    selectedColors.forEach(color => {
        const stock = stockData[color];
        const imagen = imagenesData[color] || null;

        const existe = variantesNuevas.some(v => v.talla === talla && v.color === color);
        if (existe) {
            alert(`La variante ${talla} - ${color} ya fue agregada`);
            return;
        }

        variantesNuevas.push({ talla, color, stock, imagen });
    });

    cerrarModalExitoso();
    renderVariantesExistentes();
    actualizarContadorVariantes();
    inyectarInputsHidden();
}

function cerrarModalExitoso() {
    if (modal) modal.classList.add("hidden");
    limpiarModal();
}

// ===== RENDERIZAR VARIANTES =====
function renderVariantesExistentes() {
    const variantsSection = document.querySelector(".variants-section");
    if (!variantsSection) return;
    
    const emptyState = document.querySelector(".empty-state");
    
    let lista = document.getElementById("variantesLista");
    
    if (!lista) {
        if (emptyState) emptyState.remove();
        lista = document.createElement("div");
        lista.id = "variantesLista";
        lista.className = "variants-list";
        variantsSection.appendChild(lista);
    }

    const todasVariantes = [
        ...variantesExistentes.filter(v => !v.eliminada),
        ...variantesNuevas
    ];

    if (todasVariantes.length === 0) {
        lista.innerHTML = "";
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

    lista.innerHTML = todasVariantes.map((v, i) => {
        const esNueva = !v.id;
        const editada = variantesEditadas.has(v.id);
        
        return `
            <div class="variant-card">
                <div style="display: flex; gap: 24px; align-items: center;">
                    ${v.imagen ? `<img src="${typeof v.imagen === 'string' ? v.imagen : URL.createObjectURL(v.imagen)}" alt="${v.color}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">` : '<div style="width: 50px; height: 50px; background: #f0f0f0; border-radius: 4px; display: flex; align-items: center; justify-content: center;"></div>'}
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
                    ${esNueva ? '<span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">NUEVA</span>' : ''}
                    ${editada ? '<span style="background: #fff3e0; color: #f57c00; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">EDITADA</span>' : ''}
                </div>
                <div style="display: flex; gap: 8px;">
                    <button 
                        type="button"
                        onclick="${esNueva ? `eliminarVarianteNueva(${i - variantesExistentes.filter(v => !v.eliminada).length})` : `editarVarianteExistente('${v.id}')`}"
                        class="btn-action-variant"
                    >
                        ${esNueva ? '🗑️ Eliminar' : '✏️ Editar'}
                    </button>
                    ${!esNueva ? `<button type="button" onclick="marcarComoEliminada('${v.id}')" class="btn-delete-variant">🗑️ Eliminar</button>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// ===== EDITAR VARIANTE EXISTENTE =====
function editarVarianteExistente(id) {
    const variante = variantesExistentes.find(v => v.id === id);
    if (!variante) return;

    const nuevoStock = prompt(`Editar stock para ${variante.talla} - ${variante.color}:`, variante.stock);
    
    if (nuevoStock === null) return;
    
    if (nuevoStock === '' || isNaN(nuevoStock) || parseInt(nuevoStock) < 0) {
        alert('Por favor ingresa un stock válido');
        return;
    }

    variante.stock = parseInt(nuevoStock);
    variantesEditadas.set(id, { stock: nuevoStock });
    
    renderVariantesExistentes();
    inyectarInputsHidden();
}

// ===== ELIMINAR =====
function marcarComoEliminada(id) {
    if (!confirm('¿Estás seguro de eliminar esta variante?')) return;
    
    const variante = variantesExistentes.find(v => v.id === id);
    if (variante) {
        variante.eliminada = true;
        variantesEliminadas.push(id);
    }
    
    renderVariantesExistentes();
    actualizarContadorVariantes();
    inyectarInputsHidden();
}

function eliminarVarianteNueva(index) {
    if (confirm('¿Estás seguro de eliminar esta variante?')) {
        variantesNuevas.splice(index, 1);
        renderVariantesExistentes();
        actualizarContadorVariantes();
        inyectarInputsHidden();
    }
}

// ===== CONTADOR =====
function actualizarContadorVariantes() {
    const footerInfo = document.querySelector(".footer-info");
    if (footerInfo) {
        const total = variantesExistentes.filter(v => !v.eliminada).length + variantesNuevas.length;
        footerInfo.textContent = `${total} Variante${total !== 1 ? 's' : ''}`;
    }
}

// ===== INYECTAR INPUTS HIDDEN =====
function inyectarInputsHidden() {
    const form = document.querySelector("form");
    if (!form) return;

    const old = document.getElementById("hiddenVariantes");
    if (old) old.remove();

    const container = document.createElement("div");
    container.id = "hiddenVariantes";

    // Variantes editadas
    variantesEditadas.forEach((datos, id) => {
        container.innerHTML += `
            <input type="hidden" name="variantes_editadas[${id}][stock]" value="${datos.stock}">
        `;
    });

    // Variantes eliminadas
    variantesEliminadas.forEach(id => {
        container.innerHTML += `<input type="hidden" name="variantes_eliminadas[]" value="${id}">`;
    });

    // Variantes nuevas
    variantesNuevas.forEach((v, i) => {
        container.innerHTML += `
            <input type="hidden" name="variantes_nuevas[${i}][talla]" value="${v.talla}">
            <input type="hidden" name="variantes_nuevas[${i}][color]" value="${v.color}">
            <input type="hidden" name="variantes_nuevas[${i}][stock]" value="${v.stock}">
        `;
    });

    form.appendChild(container);
}

console.log('✅ Editar Catálogo JS cargado correctamente');
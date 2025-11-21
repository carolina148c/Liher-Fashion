// ===== INVENTARIO.JS - PARA AGREGAR Y EDITAR PRODUCTOS =====

// Variables globales
let selectedColors = [];
let variantesGeneradas = [];
let variantesExistentes = [];
let variantesEditadas = new Map();
let variantesEliminadas = [];
let editIndex = null;
let stockData = {};
let imageData = {};

// Mapeos para convertir IDs a nombres
let nombresTallas = {};
let nombresColores = {};

// Elementos del DOM
const modal = document.getElementById("modalVariante");
const stockGrid = document.getElementById("stockGrid");
const previewGrid = document.getElementById("previewGrid");

// Detectar modo (agregar o editar)
const isEditMode = document.querySelector('form[action*="editar"]') !== null;

// ===== INICIALIZACIÓN =====

document.addEventListener('DOMContentLoaded', function() {
    initImagePreview();
    initModalVariantes();
    initMapeosNombres();
    initPriceFormatting();
    
    if (isEditMode) {
        cargarVariantesExistentes();
    } else {
        cargarDesdeStorage();
        
        if (variantesGeneradas.length > 0) {
            renderVariantes();
            actualizarContadorVariantes();
            inyectarInputsHidden();
        }
    }
    
    setupFormHandlers();
});

// ===== FUNCIONES DE INICIALIZACIÓN =====

function initMapeosNombres() {
    // Llenar mapeo de tallas desde el select
    const tallaSelect = document.getElementById("tallaSelect");
    if (tallaSelect) {
        Array.from(tallaSelect.options).forEach(option => {
            if (option.value && option.dataset.nombre) {
                nombresTallas[option.value] = option.dataset.nombre;
            }
        });
    }
    
    // Llenar mapeo de colores desde el select
    const colorSelect = document.getElementById("colorSelect");
    if (colorSelect) {
        Array.from(colorSelect.options).forEach(option => {
            if (option.value && option.dataset.nombre) {
                nombresColores[option.value] = option.dataset.nombre;
            }
        });
    }
}

function initPriceFormatting() {
    const priceInput = document.querySelector('input[name="precio"]');
    if (priceInput && priceInput.value) {
        let currentValue = priceInput.value;
        if (currentValue && !currentValue.includes('.')) {
            formatPrice(priceInput);
        }
    }
    
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            preparePriceForSubmit();
        });
    }
}

function setupFormHandlers() {
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function() {
            if (!isEditMode) {
                setTimeout(limpiarStorage, 1000);
            }
            inyectarInputsHidden();
        });
    }
    
    const btnCancelar = document.querySelector('.btn-cancel');
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function() {
            if (!isEditMode) {
                limpiarStorage();
            }
        });
    }
}

// ===== FUNCIONES DE PERSISTENCIA =====

function guardarEnStorage() {
    if (!isEditMode) {
        const variantesParaStorage = variantesGeneradas.map(v => ({
            ...v,
            imagenBase64: v.imagenBase64 || null
        }));
        sessionStorage.setItem('variantesProducto', JSON.stringify(variantesParaStorage));
    }
}

function cargarDesdeStorage() {
    if (!isEditMode) {
        const guardadas = sessionStorage.getItem('variantesProducto');
        if (guardadas) {
            try {
                variantesGeneradas = JSON.parse(guardadas);
            } catch (e) {
                console.error('Error al cargar variantes:', e);
                variantesGeneradas = [];
            }
        }
    }
}

function limpiarStorage() {
    if (!isEditMode) {
        sessionStorage.removeItem('variantesProducto');
    }
}

// ===== FUNCIONES PARA OBTENER NOMBRES =====

function getNombreTalla(idTalla) {
    return nombresTallas[idTalla] || idTalla;
}

function getNombreColor(idColor) {
    return nombresColores[idColor] || idColor;
}

function getNombreTallaFromSelect(idTalla) {
    const select = document.getElementById("tallaSelect");
    const option = select.querySelector(`option[value="${idTalla}"]`);
    return option ? option.dataset.nombre : idTalla;
}

function getNombreColorFromSelect(idColor) {
    const select = document.getElementById("colorSelect");
    const option = select.querySelector(`option[value="${idColor}"]`);
    return option ? option.dataset.nombre : idColor;
}

// ===== CARGAR VARIANTES EXISTENTES (MODO EDICIÓN) =====

function cargarVariantesExistentes() {
    const variantCards = document.querySelectorAll('.variant-card[data-id]');
    
    variantCards.forEach((card) => {
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
    
    renderVariantes();
    actualizarContadorVariantes();
}

// ===== FUNCIONES DE IMAGEN PRINCIPAL =====

function initImagePreview() {
    const fileInput = document.querySelector('input[type="file"][name="imagen"]');
    const imagePreview = document.querySelector('.image-preview');
    
    if (!fileInput || !imagePreview) return;
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            if (!file.type.startsWith('image/')) {
                alert('Por favor selecciona un archivo de imagen válido (JPG, PNG o GIF)');
                fileInput.value = '';
                imagePreview.innerHTML = '';
                return;
            }
            
            const maxSize = 5 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('La imagen no debe superar los 5MB. Tamaño actual: ' + (file.size / (1024 * 1024)).toFixed(2) + 'MB');
                fileInput.value = '';
                imagePreview.innerHTML = '';
                return;
            }
            
            imagePreview.classList.add('loading');
            imagePreview.innerHTML = '';
            
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
                    cursor: zoom-in;
                    transition: opacity 0.3s;
                `;
                
                img.addEventListener('click', function() {
                    expandirImagen(event.target.result);
                });
                
                img.addEventListener('mouseover', function() {
                    this.style.opacity = '0.8';
                });
                
                img.addEventListener('mouseout', function() {
                    this.style.opacity = '1';
                });
                
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
            imagePreview.innerHTML = '';
        }
    });
}

// ===== FUNCIONES DEL MODAL =====

function initModalVariantes() {
    const btnAbrir = document.getElementById("btnAbrirModal");
    const modal = document.getElementById("modalVariante");
    
    if (!btnAbrir || !modal) return;
    
    btnAbrir.addEventListener("click", () => {
        modal.classList.remove("hidden");
        editIndex = null;
    });
}

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
    imageData = {};
    document.getElementById("colorTags").innerHTML = "";
    if (stockGrid) stockGrid.innerHTML = "";
    if (previewGrid) {
        previewGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #999; padding: 20px;">Seleccione una talla y colores para ver la vista previa</div>';
    }
    editIndex = null;
}

function cerrarModalExitoso() {
    if (modal) modal.classList.add("hidden");
    limpiarModal();
}

// ===== GESTIÓN DE COLORES =====

function addColor() {
    const select = document.getElementById("colorSelect");
    const colorId = select.value;
    const colorNombre = getNombreColorFromSelect(colorId);

    if (!colorId || selectedColors.includes(colorId)) {
        select.value = "";
        return;
    }

    selectedColors.push(colorId);
    select.value = "";

    actualizarColorTags();
    generarStockInputs();
    generarPreview();
}

function removeColor(colorId) {
    selectedColors = selectedColors.filter(c => c !== colorId);
    delete stockData[colorId];
    delete imageData[colorId];
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

    container.innerHTML = selectedColors.map(colorId => {
        const colorNombre = getNombreColor(colorId);
        return `
            <div class="color-tag">
                ${colorNombre}
                <button type="button" class="color-tag-remove" onclick="removeColor('${colorId}')">×</button>
            </div>
        `;
    }).join('');
}

// ===== GESTIÓN DE STOCK E IMÁGENES =====

function generarStockInputs() {
    if (!stockGrid || selectedColors.length === 0) {
        if (stockGrid) stockGrid.innerHTML = "";
        return;
    }

    stockGrid.innerHTML = selectedColors.map(colorId => {
        const colorNombre = getNombreColor(colorId);
        const stockValue = stockData[colorId] || '';
        const imagePreview = imageData[colorId] || '';
        
        return `
            <div class="stock-card">
                <div class="stock-card-header">
                    ${colorNombre}
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
                    onchange="updateStock('${colorId}', this.value)"
                    id="stock_${colorId}"
                >
                
                <div style="margin: 12px 0;">
                    <label style="font-size: 12px; color: #666; margin-bottom: 4px; display: block;">
                        Imagen de la variante
                    </label>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <button type="button" class="upload-btn" onclick="document.getElementById('imageInput_${colorId}').click()">
                            📎 Subir Imagen
                        </button>
                        <input 
                            type="file" 
                            id="imageInput_${colorId}" 
                            accept="image/*" 
                            style="display: none;" 
                            onchange="handleImageUpload('${colorId}', this)"
                        >
                        ${imagePreview ? 
                            `<button type="button" class="btn-remove" onclick="removeImage('${colorId}')" style="padding: 6px 12px; font-size: 11px; background: #fff5f5; color: #c62828; border: 1px solid #ffcdd2; border-radius: 4px; cursor: pointer;">
                                🗑️ Quitar
                            </button>` : 
                            ''
                        }
                    </div>
                </div>
                <div class="optional-text">Opcional - Máx. 5MB</div>    
            </div>
        `;
    }).join('');
}

function handleImageUpload(colorId, input) {
    const file = input.files[0];
    
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('Por favor selecciona un archivo de imagen válido (JPG, PNG o GIF)');
        input.value = '';
        return;
    }
    
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        alert('La imagen no debe superar los 5MB. Tamaño actual: ' + (file.size / (1024 * 1024)).toFixed(2) + 'MB');
        input.value = '';
        return;
    }
    
    const reader = new FileReader();
    
    reader.onload = function(event) {
        imageData[colorId] = event.target.result;
        generarStockInputs();
        generarPreview();
    };
    
    reader.onerror = function() {
        alert('Error al cargar la imagen. Por favor intenta de nuevo.');
        input.value = '';
    };
    
    reader.readAsDataURL(file);
}

function removeImage(colorId) {
    delete imageData[colorId];
    const input = document.getElementById(`imageInput_${colorId}`);
    if (input) input.value = '';
    generarStockInputs();
    generarPreview();
}

function updateStock(colorId, value) {
    stockData[colorId] = value;
    generarPreview();
}

// ===== VISTA PREVIA =====

function generarPreview() {
    if (!previewGrid) return;
    
    const tallaId = document.getElementById("tallaSelect").value;
    const tallaNombre = getNombreTallaFromSelect(tallaId);
    
    if (!tallaId || selectedColors.length === 0) {
        previewGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #999; padding: 20px;">Seleccione una talla y colores para ver la vista previa</div>';
        return;
    }

    previewGrid.innerHTML = selectedColors.map(colorId => {
        const colorNombre = getNombreColor(colorId);
        const stock = stockData[colorId] || '0';
        const imagen = imageData[colorId] || '';
        
        return `
            <div class="preview-card">
                ${imagen ? 
                    `<div class="preview-image" style="width: 100%; height: 80px; margin-bottom: 8px; border-radius: 4px; overflow: hidden; cursor: pointer;" onclick="expandirImagen('${imagen}')">
                        <img src="${imagen}" alt="${colorNombre}" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>` :
                    `<div class="preview-image-placeholder" style="width: 100%; height: 80px; margin-bottom: 8px; background: #f5f5f5; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 14px;">
                        Sin imagen
                    </div>`
                }
                <div class="preview-card-title">${tallaNombre} - ${colorNombre}</div>
                <div class="preview-card-stock">Stock: ${stock} unidades</div>
            </div>
        `;
    }).join('');
}

// ===== GESTIÓN DE VARIANTES =====

function guardarVariantes() {
    const tallaId = document.getElementById("tallaSelect").value;
    const tallaNombre = getNombreTallaFromSelect(tallaId);

    if (!tallaId) {
        alert("Por favor selecciona una talla");
        return;
    }

    if (selectedColors.length === 0) {
        alert("Por favor agrega al menos un color");
        return;
    }

    let todoOk = true;
    for (const colorId of selectedColors) {
        const stock = stockData[colorId];
        if (!stock || stock === '0' || stock < 0) {
            const colorNombre = getNombreColor(colorId);
            alert(`Por favor ingresa un stock válido para el color ${colorNombre}`);
            todoOk = false;
            break;
        }
    }

    if (!todoOk) return;

    selectedColors.forEach(colorId => {
        const stock = stockData[colorId];
        const imagenBase64 = imageData[colorId] || null;

        if (editIndex !== null) {
            variantesGeneradas[editIndex] = { talla: tallaId, color: colorId, stock, imagenBase64 };
        } else {
            const existe = variantesGeneradas.some(v => v.talla === tallaId && v.color === colorId);
            if (existe) {
                const tallaNombre = getNombreTalla(tallaId);
                const colorNombre = getNombreColor(colorId);
                alert(`La variante ${tallaNombre} - ${colorNombre} ya existe`);
                return;
            }

            variantesGeneradas.push({ talla: tallaId, color: colorId, stock, imagenBase64 });
        }
    });

    if (!isEditMode) {
        guardarEnStorage();
    }
    
    cerrarModalExitoso();
    renderVariantes();
    actualizarContadorVariantes();
    inyectarInputsHidden();
}

function renderVariantes() {
    const variantsSection = document.querySelector(".variants-section");
    if (!variantsSection) return;
    
    const emptyState = document.querySelector(".empty-state");
    
    let lista = document.getElementById("variantesLista");
    
    if (!lista) {
        if (emptyState && (variantesGeneradas.length > 0 || variantesExistentes.length > 0)) {
            emptyState.remove();
        }
        lista = document.createElement("div");
        lista.id = "variantesLista";
        lista.className = "variants-list";
        variantsSection.appendChild(lista);
    }

    const todasVariantes = [
        ...variantesExistentes.filter(v => !v.eliminada),
        ...variantesGeneradas.map(v => ({ ...v, esNueva: true }))
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
        const esNueva = v.esNueva;
        const editada = variantesEditadas.has(v.id);
        const imagenSrc = v.imagenBase64 || v.imagen;
        
        const nombreTalla = getNombreTalla(v.talla);
        const nombreColor = getNombreColor(v.color);
        
        return `
            <div class="variant-card" ${!esNueva ? `data-id="${v.id}" data-talla="${v.talla}" data-color="${v.color}" data-stock="${v.stock}" data-imagen="${v.imagen || ''}"` : ''}>
                <div style="display: flex; gap: 16px; align-items: center;">
                    ${imagenSrc ? 
                        `<div style="width: 60px; height: 60px; border-radius: 6px; overflow: hidden; flex-shrink: 0; cursor: pointer;" onclick="expandirImagen('${imagenSrc}')">
                            <img src="${imagenSrc}" alt="${nombreColor}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>` :
                        `<div style="width: 60px; height: 60px; background: #f5f5f5; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px; flex-shrink: 0; text-align: center; padding: 4px;">
                            Sin imagen
                        </div>`
                    }
                    <div style="display: flex; gap: 24px; align-items: center;">
                        <div>
                            <span style="font-size: 12px; color: #999;">Talla</span>
                            <div style="font-size: 14px; font-weight: 600; color: #333;">${nombreTalla}</div>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #999;">Color</span>
                            <div style="font-size: 14px; font-weight: 600; color: #333;">${nombreColor}</div>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #999;">Stock</span>
                            <div style="font-size: 14px; font-weight: 600; color: #ff4081;">${v.stock} unidades</div>
                        </div>
                    </div>
                    ${esNueva ? '<span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">NUEVA</span>' : ''}
                    ${editada ? '<span style="background: #fff3e0; color: #f57c00; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">EDITADA</span>' : ''}
                </div>
                <div style="display: flex; gap: 8px;">
                    ${isEditMode ? `
                        <button 
                            type="button"
                            onclick="${esNueva ? `eliminarVarianteNueva(${i - variantesExistentes.filter(v => !v.eliminada).length})` : `editarVarianteExistente('${v.id}')`}"
                            class="btn-action-variant"
                        >
                            ${esNueva ? '🗑️ Eliminar' : '✏️ Editar'}
                        </button>
                        ${!esNueva ? `<button type="button" onclick="marcarComoEliminada('${v.id}')" class="btn-delete-variant">🗑️ Eliminar</button>` : ''}
                    ` : `
                        <button 
                            type="button"
                            onclick="editarVariante(${i})"
                            class="btn-action-variant"
                        >
                            ✏️ Editar
                        </button>
                        <button 
                            type="button"
                            onclick="eliminarVariante(${i})"
                            class="btn-delete-variant"
                        >
                            🗑️ Eliminar
                        </button>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

// ===== FUNCIONES PARA MODO AGREGAR =====

function editarVariante(i) {
    const v = variantesGeneradas[i];
    editIndex = i;

    limpiarModal();
    
    if (modal) modal.classList.remove("hidden");

    document.getElementById("tallaSelect").value = v.talla;
    selectedColors = [v.color];
    stockData[v.color] = v.stock;
    if (v.imagenBase64) {
        imageData[v.color] = v.imagenBase64;
    }

    actualizarColorTags();
    generarStockInputs();
    generarPreview();
}

function eliminarVariante(i) {
    if (confirm('¿Estás seguro de eliminar esta variante?')) {
        variantesGeneradas.splice(i, 1);
        if (!isEditMode) {
            guardarEnStorage();
        }
        renderVariantes();
        actualizarContadorVariantes();
        inyectarInputsHidden();
    }
}

// ===== FUNCIONES PARA MODO EDITAR =====

function editarVarianteExistente(id) {
    const variante = variantesExistentes.find(v => v.id === id);
    if (!variante) return;

    const nombreTalla = getNombreTalla(variante.talla);
    const nombreColor = getNombreColor(variante.color);
    
    const nuevoStock = prompt(`Editar stock para ${nombreTalla} - ${nombreColor}:`, variante.stock);
    
    if (nuevoStock === null) return;
    
    if (nuevoStock === '' || isNaN(nuevoStock) || parseInt(nuevoStock) < 0) {
        alert('Por favor ingresa un stock válido');
        return;
    }

    variante.stock = parseInt(nuevoStock);
    variantesEditadas.set(id, { stock: nuevoStock });
    
    renderVariantes();
    inyectarInputsHidden();
}

function marcarComoEliminada(id) {
    if (!confirm('¿Estás seguro de eliminar esta variante?')) return;
    
    const variante = variantesExistentes.find(v => v.id === id);
    if (variante) {
        variante.eliminada = true;
        variantesEliminadas.push(id);
    }
    
    renderVariantes();
    actualizarContadorVariantes();
    inyectarInputsHidden();
}

function eliminarVarianteNueva(index) {
    if (confirm('¿Estás seguro de eliminar esta variante?')) {
        variantesGeneradas.splice(index, 1);
        renderVariantes();
        actualizarContadorVariantes();
        inyectarInputsHidden();
    }
}

// ===== FUNCIONES DE PRECIO =====

function formatPrice(input) {
    let value = input.value.replace(/[^\d]/g, '');
    
    if (value.length > 0) {
        value = parseInt(value).toLocaleString('es-CO');
    }
    
    input.value = value;
}

function preparePriceForSubmit() {
    const priceInput = document.querySelector('input[name="precio"]');
    if (priceInput) {
        priceInput.value = priceInput.value.replace(/\./g, '');
    }
}

// ===== UTILIDADES =====

function actualizarContadorVariantes() {
    const footerInfo = document.querySelector(".footer-info");
    if (footerInfo) {
        let total;
        if (isEditMode) {
            total = variantesExistentes.filter(v => !v.eliminada).length + variantesGeneradas.length;
        } else {
            total = variantesGeneradas.length;
        }
        footerInfo.textContent = `${total} Variante${total !== 1 ? 's' : ''}`;
    }
}

function inyectarInputsHidden() {
    const form = document.querySelector("form");
    if (!form) return;

    const old = document.getElementById("hiddenVariantes");
    if (old) old.remove();

    const container = document.createElement("div");
    container.id = "hiddenVariantes";

    if (isEditMode) {
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
        variantesGeneradas.forEach((v, i) => {
            container.innerHTML += `
                <input type="hidden" name="variantes_nuevas[${i}][talla]" value="${v.talla}">
                <input type="hidden" name="variantes_nuevas[${i}][color]" value="${v.color}">
                <input type="hidden" name="variantes_nuevas[${i}][stock]" value="${v.stock}">
                ${v.imagenBase64 ? `<input type="hidden" name="variantes_nuevas[${i}][imagen]" value="${v.imagenBase64}">` : ''}
            `;
        });
    } else {
        // Modo agregar
        variantesGeneradas.forEach((v, i) => {
            container.innerHTML += `
                <input type="hidden" name="variantes[${i}][talla]" value="${v.talla}">
                <input type="hidden" name="variantes[${i}][color]" value="${v.color}">
                <input type="hidden" name="variantes[${i}][stock]" value="${v.stock}">
                ${v.imagenBase64 ? `<input type="hidden" name="variantes[${i}][imagen]" value="${v.imagenBase64}">` : ''}
            `;
        });
    }

    form.appendChild(container);
}

// ===== EXPANSIÓN DE IMÁGENES =====

function expandirImagen(imagenSrc) {
    const modal = document.createElement('div');
    modal.className = 'modal-image-expanded';
    modal.innerHTML = `
        <div class="modal-image-content">
            <button class="btn-close-image" onclick="cerrarImagenExpandida()">×</button>
            <img src="${imagenSrc}" alt="Imagen expandida">
        </div>
    `;
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            cerrarImagenExpandida();
        }
    });
    
    document.addEventListener('keydown', function manejarTecla(e) {
        if (e.key === 'Escape') {
            cerrarImagenExpandida();
        }
    });
    
    document.body.appendChild(modal);
    modal._keydownHandler = manejarTecla;
}

function cerrarImagenExpandida() {
    const modal = document.querySelector('.modal-image-expanded');
    if (modal) {
        document.removeEventListener('keydown', modal._keydownHandler);
        modal.remove();
    }
}

console.log(`✅ Inventario JS cargado correctamente (Modo: ${isEditMode ? 'Editar' : 'Agregar'})`);
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
let varianteEditando = null;
let imagenCargadaVariante = null;
let stockActualOriginal = 0;

// Mapeos para convertir IDs a nombres
let nombresTallas = {};
let nombresColores = {};

// Elementos del DOM
const modal = document.getElementById("modalVariante");
const modalEditar = document.getElementById("modalEditarVariante");
const stockGrid = document.getElementById("stockGrid");
const previewGrid = document.getElementById("previewGrid");

// Detectar modo (agregar o editar)
const isEditMode = document.querySelector('form[action*="editar"]') !== null;

// ===== DEBUG FUNCTIONS =====
function debugVariantes() {
    console.log('=== DEBUG VARIANTES ===');
    console.log('isEditMode:', isEditMode);
    console.log('variantesEditadas:', Array.from(variantesEditadas.entries()));
    console.log('variantesEliminadas:', variantesEliminadas);
    console.log('variantesGeneradas:', variantesGeneradas);
    console.log('variantesExistentes:', variantesExistentes);
    
    // Verificar inputs hidden
    const hiddenContainer = document.getElementById('hiddenVariantes');
    if (hiddenContainer) {
        console.log('Inputs hidden:', hiddenContainer.innerHTML);
    } else {
        console.log('❌ NO hay container de inputs hidden');
    }
}

function debugVariantesExistentes() {
    console.log('=== DEBUG VARIANTES EXISTENTES ===');
    const cards = document.querySelectorAll('.variant-card[data-id]');
    cards.forEach((card, i) => {
        console.log(`Card ${i}:`, {
            id: card.dataset.id,
            talla: card.dataset.talla,
            color: card.dataset.color,
            stock: card.dataset.stock,
            imagen: card.dataset.imagen
        });
    });
}

function verificarEstadoAntesDeEnviar() {
    console.log('🔍 VERIFICANDO ESTADO ANTES DE ENVIAR:');
    console.log('variantesEditadas size:', variantesEditadas.size);
    console.log('variantesEditadas entries:', Array.from(variantesEditadas.entries()));
    console.log('variantesEliminadas:', variantesEliminadas);
    
    // Verificar si los inputs hidden están presentes
    const hiddenInputs = document.querySelectorAll('input[name*="variantes_editadas"]');
    console.log('Inputs hidden de variantes editadas encontrados:', hiddenInputs.length);
    hiddenInputs.forEach(input => {
        console.log(`Input: ${input.name} = ${input.value}`);
    });
}

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
    
    // DEBUG: Agregar listener para el submit
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('🚀 FORMULARIO ENVIÁNDOSE');
            verificarEstadoAntesDeEnviar();
            debugVariantes();
            
            // Forzar inyección de inputs
            inyectarInputsHidden();
            
            // Pequeño delay para asegurar que se inyecten los inputs
            setTimeout(() => {
                console.log('📤 Enviando formulario con datos:');
                const formData = new FormData(this);
                for (let [key, value] of formData.entries()) {
                    if (key.includes('variantes')) {
                        console.log(`${key}: ${value}`);
                    }
                }
            }, 100);
        });
    }
});

// ===== FUNCIONES DEL MODAL DE EDICIÓN DE VARIANTES =====

function abrirModalEdicionVariante(varianteData) {
    varianteEditando = varianteData;
    
    console.log('🔍 Abriendo modal de edición para:', varianteData);
    console.log('Tipo de variante:', varianteData.esNueva ? 'NUEVA' : 'EXISTENTE');
    console.log('ID de variante:', varianteData.id);
    
    // Cargar datos en el modal
    document.getElementById('variantColor').textContent = getNombreColor(varianteData.color) || 'Color no disponible';
    document.getElementById('variantSize').textContent = `Talla: ${getNombreTalla(varianteData.talla) || 'Talla no disponible'}`;
    document.getElementById('stockActual').textContent = `${varianteData.stock || 0} unidades`;
    
    // Guardar valores originales
    stockActualOriginal = parseInt(varianteData.stock) || 0;
    
    // Resetear stock agregado a 0
    document.getElementById('stockAgregado').value = '0';
    
    // Calcular y mostrar el total
    calcularYMostrarTotal();
    
    // Establecer IDs
    document.getElementById('varianteId').value = varianteData.id || '';
    document.getElementById('varianteTallaId').value = varianteData.talla;
    document.getElementById('varianteColorId').value = varianteData.color;
    document.getElementById('esVarianteNueva').value = varianteData.esNueva ? 'true' : 'false';
    
    console.log('📋 Datos cargados en modal:', {
        id: varianteData.id,
        talla: varianteData.talla,
        color: varianteData.color,
        esNueva: varianteData.esNueva,
        stockOriginal: stockActualOriginal
    });
    
    // Cargar imagen
    const img = document.getElementById('variantImage');
    const noImg = document.getElementById('noImageText');
    const imagenSrc = varianteData.imagenBase64 || varianteData.imagen;
    
    if (imagenSrc) {
        img.src = imagenSrc;
        img.style.display = 'block';
        noImg.style.display = 'none';
    } else {
        img.style.display = 'none';
        noImg.style.display = 'block';
    }
    
    // Resetear imagen cargada
    imagenCargadaVariante = null;
    document.getElementById('fileInputVariante').value = '';
    
    // Mostrar modal
    if (modalEditar) {
        modalEditar.classList.remove('hidden');
    }
}

function calcularYMostrarTotal() {
    const stockAgregado = parseInt(document.getElementById('stockAgregado').value) || 0;
    const total = stockActualOriginal + stockAgregado;
    document.getElementById('stockTotal').textContent = total;
}

function incrementarStock() {
    const input = document.getElementById('stockAgregado');
    input.value = parseInt(input.value || 0) + 1;
    calcularYMostrarTotal();
}

function decrementarStock() {
    const input = document.getElementById('stockAgregado');
    const nuevoValor = parseInt(input.value || 0) - 1;
    if (nuevoValor >= 0) {
        input.value = nuevoValor;
        calcularYMostrarTotal();
    }
}

function validarStock() {
    const input = document.getElementById('stockAgregado');
    if (input.value < 0) {
        input.value = 0;
    }
    calcularYMostrarTotal();
}

function handleImageUploadVariante(event) {
    const file = event.target.files[0];
    
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('Por favor selecciona un archivo de imagen válido (JPG, PNG o GIF)');
        event.target.value = '';
        return;
    }
    
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        alert('La imagen no debe superar los 5MB. Tamaño actual: ' + (file.size / (1024 * 1024)).toFixed(2) + 'MB');
        event.target.value = '';
        return;
    }
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        imagenCargadaVariante = e.target.result;
        const img = document.getElementById('variantImage');
        const noImg = document.getElementById('noImageText');
        
        img.src = e.target.result;
        img.style.display = 'block';
        noImg.style.display = 'none';
        
        // Mostrar mensaje de éxito
        mostrarMensajeTemporal('Imagen cargada correctamente', 'success');
    };
    
    reader.onerror = function() {
        alert('Error al cargar la imagen. Por favor intenta de nuevo.');
        event.target.value = '';
    };
    
    reader.readAsDataURL(file);
}

function guardarCambiosVariante() {
    const stockAgregado = parseInt(document.getElementById('stockAgregado').value) || 0;
    const varianteId = document.getElementById('varianteId').value;
    const tallaId = document.getElementById('varianteTallaId').value;
    const colorId = document.getElementById('varianteColorId').value;
    const esVarianteNueva = document.getElementById('esVarianteNueva').value === 'true';
    
    if (isNaN(stockAgregado) || stockAgregado < 0) {
        alert('Por favor ingresa una cantidad válida a agregar');
        return;
    }
    
    // Calcular el nuevo stock total
    const nuevoStockTotal = stockActualOriginal + stockAgregado;
    
    console.log('💾 Guardando cambios para variante:', {
        varianteId,
        tallaId,
        colorId,
        esVarianteNueva,
        stockActualOriginal,
        stockAgregado,
        nuevoStockTotal,
        tieneImagen: !!imagenCargadaVariante
    });
    
    // Validación adicional para evitar guardar sin cambios
    if (stockAgregado === 0 && !imagenCargadaVariante) {
        if (!confirm('No has realizado cambios. ¿Deseas guardar de todas formas?')) {
            return;
        }
    }
    
    // Actualizar la variante según el tipo
    if (esVarianteNueva) {
        // Buscar y actualizar variante nueva
        const index = variantesGeneradas.findIndex(v => 
            v.talla === tallaId && v.color === colorId
        );
        
        if (index !== -1) {
            variantesGeneradas[index].stock = nuevoStockTotal;
            if (imagenCargadaVariante) {
                variantesGeneradas[index].imagenBase64 = imagenCargadaVariante;
            }
            console.log(`✅ Variante nueva actualizada en índice ${index}`);
        }
    } else {
        // Para variantes existentes, guardar datos completos
        variantesEditadas.set(varianteId, { 
            stock: nuevoStockTotal,
            talla: tallaId,
            color: colorId,
            imagen: imagenCargadaVariante 
        });
        
        console.log('📝 Variante editada guardada en mapa:', {
            id: varianteId,
            datos: variantesEditadas.get(varianteId)
        });
        
        // Actualizar también en el array de existentes para mostrar cambios inmediatos
        const variante = variantesExistentes.find(v => v.id === varianteId);
        if (variante) {
            variante.stock = nuevoStockTotal;
            if (imagenCargadaVariante) {
                variante.imagen = imagenCargadaVariante;
            }
        }
    }
    
    // Guardar en storage si es modo agregar
    if (!isEditMode) {
        guardarEnStorage();
    }
    
    // Actualizar la interfaz
    renderVariantes();
    actualizarContadorVariantes();
    inyectarInputsHidden();
    
    // Debug para verificar que todo se guardó
    debugVariantes();
    
    // Mostrar mensaje de éxito
    if (stockAgregado > 0) {
        mostrarMensajeTemporal(`Stock actualizado: ${stockActualOriginal} + ${stockAgregado} = ${nuevoStockTotal} unidades`, 'success');
    } else if (imagenCargadaVariante) {
        mostrarMensajeTemporal('Imagen actualizada correctamente', 'success');
    } else {
        mostrarMensajeTemporal('Cambios guardados', 'info');
    }
    
    // ✅ CORRECCIÓN: Usar la nueva función para cerrar sin confirmación
    cerrarModalEdicionExitoso();
}

function cerrarModalEdicion() {
    if (confirm('¿Estás seguro de que deseas cerrar sin guardar?')) {
        if (modalEditar) {
            modalEditar.classList.add('hidden');
        }
        limpiarModalEdicion();
    }
}

function cerrarModalEdicionExitoso() {
    if (modalEditar) {
        modalEditar.classList.add('hidden');
    }
    limpiarModalEdicion();
}

function limpiarModalEdicion() {
    varianteEditando = null;
    imagenCargadaVariante = null;
    stockActualOriginal = 0;
    document.getElementById('stockAgregado').value = '0';
    document.getElementById('stockTotal').textContent = '0';
    document.getElementById('fileInputVariante').value = '';
}

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
    
    console.log('🔄 Cargando variantes existentes...');
    console.log('Cards encontradas:', variantCards.length);
    
    variantCards.forEach((card, index) => {
        const id = card.dataset.id;
        const talla = card.dataset.talla;
        const color = card.dataset.color;
        const stock = card.dataset.stock;
        const imagen = card.dataset.imagen || null;
        
        console.log(`Variante ${index}:`, { id, talla, color, stock, imagen });
        
        variantesExistentes.push({
            id: id,
            talla: talla,
            color: color,
            stock: stock,
            imagen: imagen,
            eliminada: false
        });
    });
    
    console.log('✅ Variantes existentes cargadas:', variantesExistentes);
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

// ===== FUNCIONES DEL MODAL DE AGREGAR VARIANTES =====

function initModalVariantes() {
    const btnAbrir = document.getElementById("btnAbrirModal");
    
    if (!btnAbrir) return;
    
    btnAbrir.addEventListener("click", () => {
        if (modal) {
            modal.classList.remove("hidden");
        }
        editIndex = null;
    });
}

function cerrarModal() {
    if (confirm('¿Estás seguro de que deseas cerrar sin guardar?')) {
        if (modal) {
            modal.classList.add("hidden");
        }
        limpiarModal();
    }
}

function cerrarModalExitoso() {
    if (modal) modal.classList.add("hidden");
    limpiarModal();
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

// ===== RENDERIZADO DE VARIANTES =====

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
        ...variantesGeneradas.map((v, index) => ({ 
            ...v, 
            esNueva: true,
            index: index 
        }))
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

    lista.innerHTML = todasVariantes.map((v) => {
        const esNueva = v.esNueva;
        const editada = !esNueva && variantesEditadas.has(v.id);
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
                            onclick="${esNueva ? `editarVarianteNueva(${v.index})` : `editarVarianteExistente('${v.id}')`}"
                            class="btn-action-variant"
                        >
                            ✏️ Editar
                        </button>
                        <button 
                            type="button"
                            onclick="${esNueva ? `eliminarVarianteNueva(${v.index})` : `marcarComoEliminada('${v.id}')`}"
                            class="btn-delete-variant"
                        >
                            🗑️ Eliminar
                        </button>
                    ` : `
                        <button 
                            type="button"
                            onclick="editarVarianteNueva(${v.index})"
                            class="btn-action-variant"
                        >
                            ✏️ Editar
                        </button>
                        <button 
                            type="button"
                            onclick="eliminarVarianteNueva(${v.index})"
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

// ===== FUNCIONES DE EDICIÓN =====

function editarVarianteExistente(id) {
    console.log('✏️ Editando variante existente con ID:', id);
    
    let variante = variantesExistentes.find(v => v.id === id);
    
    // Si no se encuentra en variantesExistentes, buscar en el DOM
    if (!variante) {
        console.log('❌ Variante no encontrada en variantesExistentes, buscando en DOM...');
        const card = document.querySelector(`.variant-card[data-id="${id}"]`);
        if (card) {
            variante = {
                id: card.dataset.id,
                talla: card.dataset.talla,
                color: card.dataset.color,
                stock: card.dataset.stock,
                imagen: card.dataset.imagen || null,
                eliminada: false
            };
            // Agregar a variantesExistentes para futuras referencias
            variantesExistentes.push(variante);
            console.log('✅ Variante cargada desde DOM:', variante);
        }
    }
    
    if (!variante) {
        console.log('❌ Variante no encontrada en ningún lugar');
        alert('No se pudo encontrar la variante para editar');
        return;
    }
    
    console.log('✅ Variante encontrada para editar:', variante);
    
    abrirModalEdicionVariante({
        id: variante.id,
        talla: variante.talla,
        color: variante.color,
        stock: variante.stock,
        imagen: variante.imagen,
        esNueva: false  // ← IMPORTANTE: Esto debe ser false para variantes existentes
    });
}

function editarVarianteNueva(index) {
    const variante = variantesGeneradas[index];
    if (!variante) return;
    
    abrirModalEdicionVariante({
        id: `nueva_${index}`,
        talla: variante.talla,
        color: variante.color,
        stock: variante.stock,
        imagenBase64: variante.imagenBase64,
        esNueva: true
    });
}

function eliminarVarianteNueva(index) {
    if (confirm('¿Estás seguro de eliminar esta variante?')) {
        variantesGeneradas.splice(index, 1);
        renderVariantes();
        actualizarContadorVariantes();
        inyectarInputsHidden();
    }
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

// ===== FUNCIÓN AUXILIAR PARA MENSAJES =====

function mostrarMensajeTemporal(mensaje, tipo = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${tipo === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        border-radius: 6px;
        z-index: 1000;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    alertDiv.textContent = mensaje;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
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

// Función para inyectar inputs hidden
function inyectarInputsHidden() {
    console.log('🔄 Inyectando inputs hidden...');
    
    const container = document.getElementById('hiddenInputsContainer');
    if (!container) {
        console.error('❌ No se encontró el contenedor para inputs hidden');
        return;
    }
    
    // Limpiar contenedor
    container.innerHTML = '';
    
    // Inyectar variantes eliminadas
    variantesEliminadas.forEach(id => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'variantes_eliminadas[]';
        input.value = id;
        container.appendChild(input);
    });
    
    // Inyectar variantes editadas
    let editIndex = 0;
    variantesEditadas.forEach((datos, id) => {
        // Solo procesar variantes existentes (no nuevas)
        if (!datos.esNueva) {
            const prefix = `variantes_editadas[${id}]`;
            
            // Stock
            const inputStock = document.createElement('input');
            inputStock.type = 'hidden';
            inputStock.name = `${prefix}[stock]`;
            inputStock.value = datos.stock || 0;
            container.appendChild(inputStock);
            
            // Imagen (si hay cambios)
            if (datos.imagenBase64) {
                const inputImagen = document.createElement('input');
                inputImagen.type = 'hidden';
                inputImagen.name = `${prefix}[imagen]`;
                inputImagen.value = datos.imagenBase64;
                container.appendChild(inputImagen);
            }
            
            editIndex++;
        }
    });
    
    // Inyectar variantes nuevas
    let newIndex = 0;
    variantesEditadas.forEach((datos, id) => {
        if (datos.esNueva) {
            const prefix = `variantes_nuevas[${newIndex}]`;
            
            // Talla
            const inputTalla = document.createElement('input');
            inputTalla.type = 'hidden';
            inputTalla.name = `${prefix}[talla]`;
            inputTalla.value = datos.tallaId;
            container.appendChild(inputTalla);
            
            // Color
            const inputColor = document.createElement('input');
            inputColor.type = 'hidden';
            inputColor.name = `${prefix}[color]`;
            inputColor.value = datos.colorId;
            container.appendChild(inputColor);
            
            // Stock
            const inputStock = document.createElement('input');
            inputStock.type = 'hidden';
            inputStock.name = `${prefix}[stock]`;
            inputStock.value = datos.stock || 0;
            container.appendChild(inputStock);
            
            // Imagen
            if (datos.imagenBase64) {
                const inputImagen = document.createElement('input');
                inputImagen.type = 'hidden';
                inputImagen.name = `${prefix}[imagen]`;
                inputImagen.value = datos.imagenBase64;
                container.appendChild(inputImagen);
            }
            
            newIndex++;
        }
    });
    
    console.log(`✅ Inputs hidden inyectados: ${container.children.length} elementos`);
    console.log(`📦 Variantes eliminadas: ${variantesEliminadas.length}`);
    console.log(`✏️ Variantes editadas: ${editIndex}`);
    console.log(`🆕 Variantes nuevas: ${newIndex}`);
}

// Función para agregar variante eliminada
function agregarVarianteEliminada(varianteId) {
    if (!variantesEliminadas.includes(varianteId)) {
        variantesEliminadas.push(varianteId);
        console.log(`🗑️ Variante marcada para eliminar: ${varianteId}`);
    }
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


function debugCompleto() {
    console.log('=== DEBUG COMPLETO ===');
    
    // 1. Verificar variantes existentes en el DOM
    console.log('1. VARIANTES EN EL DOM:');
    const cards = document.querySelectorAll('.variant-card[data-id]');
    cards.forEach((card, i) => {
        console.log(`   Variante ${i}:`, {
            id: card.dataset.id,
            talla: card.dataset.talla,
            color: card.dataset.color,
            stock: card.dataset.stock
        });
    });
    
    // 2. Verificar arrays JavaScript
    console.log('2. ARRAYS JAVASCRIPT:');
    console.log('   variantesExistentes:', variantesExistentes);
    console.log('   variantesEditadas:', Array.from(variantesEditadas.entries()));
    console.log('   variantesGeneradas:', variantesGeneradas);
    
    // 3. Verificar inputs hidden
    console.log('3. INPUTS HIDDEN:');
    const hiddenContainer = document.getElementById('hiddenVariantes');
    if (hiddenContainer) {
        console.log('   Contenido:', hiddenContainer.innerHTML);
    } else {
        console.log('   ❌ NO existe hiddenVariantes');
    }
    
    // 4. Verificar formulario
    console.log('4. FORMULARIO:');
    const form = document.querySelector('form');
    if (form) {
        const formData = new FormData(form);
        console.log('   Campos del formulario:');
        for (let [key, value] of formData.entries()) {
            if (key.includes('variantes')) {
                console.log(`   ${key}: ${value}`);
            }
        }
    }
}




//Validaciones 

// Nombre 

document.addEventListener("DOMContentLoaded", function () {

    const inputNombre = document.querySelector('input[name="nombre"]');
    const errorNombre = document.getElementById("errorNombre");

    errorNombre.style.fontSize = "13px";
    errorNombre.style.marginTop = "3px";

    const regexLimpieza = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]/g;
    const regexCompleto = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+( [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$/;

    function validarNombre() {
    let valor = inputNombre.value;

    let limpio = valor
        .replace(regexLimpieza, "")
        .replace(/\s{2,}/g, " ")
        .replace(/^\s+/g, "");

    if (valor !== limpio) {
        inputNombre.value = limpio;
    }

    if (limpio.length === 0) {
        errorNombre.textContent = "Solo letras, tildes y un espacio entre palabras.";
        errorNombre.style.color = "black";
        return false;
    }

    if (limpio.length < 3) {
        errorNombre.textContent = " Mínimo 3 caracteres.";
        errorNombre.style.color = "red";
        return false;
    }

    if (limpio.length > 150) {
        errorNombre.textContent = " Máximo 150 caracteres.";
        errorNombre.style.color = "red";
        return false;
    }

    if (!regexCompleto.test(limpio)) {
        errorNombre.textContent = " Formato inválido.";
        errorNombre.style.color = "red";
        return false;
    }

    // 🚫 REGLA ANTI "ssssss", "aaaaaa", etc.
    let palabras = limpio.split(" ");
    for (let p of palabras) {
        if (/^([A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\1{2,}$/.test(p)) {
            errorNombre.textContent = " El nombre parece ser valido .";
            errorNombre.style.color = "red";
            return false;
        }
    }

    errorNombre.textContent = "✓ Nombre válido.";
    errorNombre.style.color = "green";
    return true;
}

    inputNombre.addEventListener("input", validarNombre);

    // Evitar enviar si no es válido
    document.getElementById("productoForm").addEventListener("submit", function (e) {
        if (!validarNombre()) {
            e.preventDefault();
            errorNombre.style.color = "red";
        }
    });

});




// REFERENCIA
document.addEventListener("DOMContentLoaded", function () {

    const inputReferencia = document.querySelector('input[name="referencia"]');
    const errorRef = document.createElement("div");

    // insertar debajo del input
    inputReferencia.insertAdjacentElement("afterend", errorRef);

    errorRef.style.fontSize = "13px";
    errorRef.style.marginTop = "3px";

    // Limpieza: solo letras y números
    const regexLimpieza = /[^A-Za-z0-9]/g;
    const regexCompleto = /^[A-Za-z0-9]+$/;

    function validarReferencia() {
        let valor = inputReferencia.value;

        // limpiar caracteres no permitidos
        let limpio = valor.replace(regexLimpieza, "");

        // quitar espacios manualmente si vuelan
        limpio = limpio.replace(/\s+/g, "");

        if (valor !== limpio) {
            inputReferencia.value = limpio;
        }

        // Reglas
        if (limpio.length === 0) {
            errorRef.textContent = "Solo letras y números (sin espacios).";
            errorRef.style.color = "black";
            return false;
        }

        if (limpio.length < 3) {
            errorRef.textContent = "Mínimo 3 caracteres.";
            errorRef.style.color = "red";
            return false;
        }

        if (limpio.length > 10) {
            errorRef.textContent = "Máximo 10 caracteres.";
            errorRef.style.color = "red";
            return false;
        }

        if (!regexCompleto.test(limpio)) {
            errorRef.textContent = "Formato inválido.";
            errorRef.style.color = "red";
            return false;
        }

        // ❌ EVITAR “aaaaaa”, “bbbbbb”, “111111”, etc.
        if (/^([A-Za-z0-9])\1{2,}$/.test(limpio)) {
            errorRef.textContent = "La referencia no puede ser una secuencia repetitiva.";
            errorRef.style.color = "red";
            return false;
        }

        // Todo bien
        errorRef.textContent = "✓ Referencia válida.";
        errorRef.style.color = "green";
        return true;
    }

    inputReferencia.addEventListener("input", validarReferencia);

    // Evitar submit si hay error
    document.getElementById("productoForm").addEventListener("submit", function (e) {
        if (!validarReferencia()) {
            e.preventDefault();
            errorRef.style.color = "red";
        }
    });

});


// =====================
// PRECIO con decimal y mensaje de especificación
// =====================
(function () {
  const precioInput = document.querySelector('input[name="precio"]');
  if (!precioInput) return;

  // Crear/usar el mensaje de especificación (gris) y el mensaje de estado debajo
  let spec = precioInput.parentNode.querySelector('.precio-spec');
  if (!spec) {
    spec = document.createElement('div');
    spec.className = 'precio-spec';
    spec.style.color = '#555';
    spec.style.fontSize = '12px';
    spec.style.marginTop = '4px';
    spec.textContent = 'Formato: 3–8 caracteres. Solo números, opcional punto decimal (máx 2 decimales).';
    precioInput.insertAdjacentElement('afterend', spec);
  }

  let estado = document.getElementById('precio-error');
  if (!estado) {
    estado = document.createElement('div');
    estado.id = 'precio-error';
    estado.className = 'validacion-texto';
    estado.style.fontSize = '13px';
    estado.style.marginTop = '3px';
    spec.insertAdjacentElement('afterend', estado);
  }

  // util: limpia y formatea manteniendo un solo punto decimal y max 2 decimales
  function limpiarPrecioConDecimal(v) {
    // eliminar caracteres distintos a dígitos y punto
    v = v.replace(/[^0-9.]/g, '');

    // si hay más de un punto, dejar solo el primero
    const parts = v.split('.');
    if (parts.length > 1) {
      v = parts.shift() + '.' + parts.join(''); // junta el resto sin puntos
    }

    // limitar a 2 decimales
    if (v.indexOf('.') !== -1) {
      const [intPart, decPart] = v.split('.');
      v = intPart + '.' + decPart.slice(0, 2);
    }

    // Limitar longitud total a 8 caracteres (incluyendo el punto)
    if (v.length > 8) {
      v = v.slice(0, 8);
      // si el corte deja un punto final, quitarlo
      if (v.endsWith('.')) v = v.slice(0, -1);
    }

    return v;
  }

  function validarPrecio() {
    let raw = precioInput.value || '';
    const limpio = limpiarPrecioConDecimal(raw);

    // si cambió, reasignar
    if (raw !== limpio) precioInput.value = limpio;

    // validaciones
    if (limpio.length === 0) {
      setError(precioInput, estado, 'El precio es obligatorio.');
      return false;
    }

    // quitar punto para contar solo caracteres mínimos? seguiremos la regla: mínimo 3 caracteres totales
    if (limpio.length < 3) {
      setError(precioInput, estado, 'Mínimo 3 caracteres.');
      return false;
    }

    // si contiene punto, validar decimales
    if (limpio.includes('.')) {
      const parts = limpio.split('.');
      const intPart = parts[0] || '';
      const decPart = parts[1] || '';
      // no permitir enteros vacíos: ".12" -> invalid
      if (intPart.length === 0) {
        setError(precioInput, estado, 'Formato inválido.');
        return false;
      }
      if (decPart.length > 2) {
        setError(precioInput, estado, 'Máx 2 decimales.');
        return false;
      }
    }

    // todo ok
    setSuccess(precioInput, estado, '✓ Precio válido.');
    return true;
  }

  // pegar: limpiar lo pegado
  precioInput.addEventListener('paste', function (e) {
    const texto = (e.clipboardData || window.clipboardData).getData('text') || '';
    const limpio = limpiarPrecioConDecimal(texto);
    e.preventDefault();
    // insertar en cursor
    const before = precioInput.value;
    const start = precioInput.selectionStart || before.length;
    const end = precioInput.selectionEnd || before.length;
    const newValue = (before.slice(0, start) + limpio + before.slice(end)).slice(0, 8);
    precioInput.value = newValue;
    validarPrecio();
  });

  precioInput.addEventListener('input', validarPrecio);

  // validación inicial (si hay valor precargado)
  validarPrecio();
})();

// =====================
// DESCRIPCIÓN (solo letras, 1 espacio entre palabras, 5-500 chars)
// =====================
(function () {
  const descInput = document.querySelector('textarea[name="descripcion"]');
  if (!descInput) return;

  // crear/usar mensaje de especificación y estado (gris + estado)
  let spec = descInput.parentNode.querySelector('.desc-spec');
  if (!spec) {
    spec = document.createElement('div');
    spec.className = 'desc-spec';
    spec.style.color = '#555';
    spec.style.fontSize = '12px';
    spec.style.marginTop = '4px';
    spec.textContent = 'Solo letras y un espacio entre palabras. 5–500 caracteres.';
    descInput.insertAdjacentElement('afterend', spec);
  }

  let estado = document.getElementById('descripcion-error');
  if (!estado) {
    estado = document.createElement('div');
    estado.id = 'descripcion-error';
    estado.className = 'validacion-texto';
    estado.style.fontSize = '13px';
    estado.style.marginTop = '3px';
    spec.insertAdjacentElement('afterend', estado);
  }

  function limpiarDescripcion(v) {
    // mantener solo letras y espacios
    v = v.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]/g, '');
    // dobles espacios -> uno
    v = v.replace(/\s{2,}/g, ' ');
    // quitar espacio al inicio
    v = v.replace(/^\s+/g, '');
    // limitar 500
    return v.slice(0, 500);
  }

  function validarDescripcion() {
    let raw = descInput.value || '';
    let limpio = limpiarDescripcion(raw);

    if (raw !== limpio) descInput.value = limpio;

    const len = limpio.trim().length;

    if (len === 0) {
      setError(descInput, estado, 'La descripción es obligatoria.');
      return false;
    }
    if (len < 5) {
      setError(descInput, estado, 'Mínimo 5 caracteres.');
      return false;
    }
    if (limpio.length > 500) {
      setError(descInput, estado, 'Máximo 500 caracteres.');
      return false;
    }

    const patron = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?: [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$/;
    if (!patron.test(limpio)) {
      setError(descInput, estado, 'Solo letras y un espacio entre palabras.');
      return false;
    }

    // evitar palabras repetitivas
    const palabras = limpio.split(' ');
    for (let p of palabras) {
      if (/^([A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\1{2,}$/.test(p)) {
        setError(descInput, estado, 'La descripción contiene palabras inválidas.');
        return false;
      }
    }

    setSuccess(descInput, estado, '✓ Descripción válida.');
    return true;
  }

  // manejar pegado
  descInput.addEventListener('paste', function (e) {
    const texto = (e.clipboardData || window.clipboardData).getData('text') || '';
    const limpio = limpiarDescripcion(texto);
    e.preventDefault();
    // insertar limpio en cursor
    const before = descInput.value;
    const start = descInput.selectionStart || before.length;
    const end = descInput.selectionEnd || before.length;
    const newValue = (before.slice(0, start) + limpio + before.slice(end)).slice(0, 500);
    descInput.value = newValue;
    validarDescripcion();
  });

  descInput.addEventListener('input', validarDescripcion);
  validarDescripcion();
})();

// ------------------
// helper visual functions (si ya las tienes, no las dupliques)
// ------------------
function setError(input, messageElement, message) {
  if (input) {
    input.classList.add('input-error');
    input.classList.remove('input-success');
  }
  if (messageElement) {
    messageElement.style.color = 'red';
    messageElement.textContent = message;
  }
}

function setSuccess(input, messageElement, message) {
  if (input) {
    input.classList.remove('input-error');
    input.classList.add('input-success');
  }
  if (messageElement) {
    messageElement.style.color = 'green';
    messageElement.textContent = message;
  }
}
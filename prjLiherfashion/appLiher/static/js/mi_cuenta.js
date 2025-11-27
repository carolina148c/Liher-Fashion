// static/js/mi_cuenta.js

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Validación de formularios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showAlert('Por favor, completa todos los campos obligatorios.', 'error');
            }
        });
    });

    // Máscaras de entrada
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) {
                value = value.substring(0, 10);
            }
            e.target.value = value;
        });
    });

    const cardInputs = document.querySelectorAll('input[data-credit-card]');
    cardInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 16) {
                value = value.substring(0, 16);
            }
            // Agregar espacios cada 4 dígitos
            value = value.replace(/(.{4})/g, '$1 ').trim();
            e.target.value = value;
        });
    });

    // Auto-detectar tipo de tarjeta
    const cardNumberInputs = document.querySelectorAll('input[name="numero_tarjeta"]');
    cardNumberInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            const value = e.target.value.replace(/\D/g, '');
            const cardType = detectCardType(value);
            const cardTypeInput = document.querySelector('select[name="tipo_tarjeta"]');
            
            if (cardType && cardTypeInput) {
                cardTypeInput.value = cardType;
            }
        });
    });

    // Mostrar/ocultar contraseña
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const passwordInput = this.previousElementSibling;
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            this.querySelector('i').classList.toggle('bi-eye');
            this.querySelector('i').classList.toggle('bi-eye-slash');
        });
    });
});

function detectCardType(cardNumber) {
    const patterns = {
        'visa': /^4/,
        'mastercard': /^5[1-5]/,
        'american_express': /^3[47]/,
        'dinners_club': /^3(?:0[0-5]|[68])/
    };

    for (const [type, pattern] of Object.entries(patterns)) {
        if (pattern.test(cardNumber)) {
            return type;
        }
    }
    return null;
}

function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div class="alert-content">
            <i class="bi bi-${getAlertIcon(type)}"></i>
            <span>${message}</span>
            <button type="button" class="alert-close" onclick="this.parentElement.remove()">
                <i class="bi bi-x"></i>
            </button>
        </div>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container';
    document.querySelector('.mi-cuenta-content').prepend(container);
    return container;
}

// Funciones para modales (ya incluidas en los templates)
function confirmDelete(id, name, type = 'address') {
    const modal = document.getElementById(`${type}DeleteModal`);
    const form = document.getElementById(`${type}DeleteForm`);
    const nameElement = document.getElementById(`${type}Name`);
    
    if (modal && form && nameElement) {
        nameElement.textContent = name;
        form.action = form.action.replace('0', id);
        modal.style.display = 'block';
    }
}

function closeModal(type = 'address') {
    const modal = document.getElementById(`${type}DeleteModal`);
    if (modal) {
        modal.style.display = 'none';
    }
}
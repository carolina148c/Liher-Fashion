        document.addEventListener('DOMContentLoaded', function() {
            // Configurar sidebar
            setupSidebar();
            
            // Validación en tiempo real
            setupFormValidation();
            
            // Contador de caracteres para textarea
            setupCharacterCounter();
        });

        // Configurar sidebar
        function setupSidebar() {
            const toggleBtn = document.getElementById('toggleSidebar');
            const sidebar = document.getElementById('barraSidebar');
            const overlay = document.getElementById('overlay');

            toggleBtn.addEventListener('click', function() {
                sidebar.classList.toggle('mostrar');
                overlay.classList.toggle('activo');
            });

            overlay.addEventListener('click', function() {
                sidebar.classList.remove('mostrar');
                overlay.classList.remove('activo');
            });

            // Cerrar sidebar al hacer clic en un enlace en móvil
            document.querySelectorAll('.menu-barra a').forEach(link => {
                link.addEventListener('click', function() {
                    if (window.innerWidth <= 768) {
                        sidebar.classList.remove('mostrar');
                        overlay.classList.remove('activo');
                    }
                });
            });
        }

        // Validación del formulario
        function setupFormValidation() {
            const form = document.querySelector('form');
            const nombreInput = document.getElementById('nombre');
            
            form.addEventListener('submit', function(e) {
                let isValid = true;
                
                // Validar nombre requerido
                if (!nombreInput.value.trim()) {
                    showFieldError(nombreInput, 'El nombre del producto es requerido');
                    isValid = false;
                } else {
                    clearFieldError(nombreInput);
                }
                
                if (!isValid) {
                    e.preventDefault();
                }
            });

            // Limpiar errores al escribir
            nombreInput.addEventListener('input', function() {
                if (this.value.trim()) {
                    clearFieldError(this);
                }
            });
        }

        // Mostrar error en campo
        function showFieldError(field, message) {
            clearFieldError(field);
            field.classList.add('is-invalid');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = message;
            field.parentNode.appendChild(errorDiv);
        }

        // Limpiar error de campo
        function clearFieldError(field) {
            field.classList.remove('is-invalid');
            const errorDiv = field.parentNode.querySelector('.invalid-feedback');
            if (errorDiv) {
                errorDiv.remove();
            }
        }

        // Contador de caracteres para textarea
        function setupCharacterCounter() {
            const textarea = document.getElementById('descripcion');
            const maxLength = 500;
            
            // Crear elemento contador
            const counter = document.createElement('div');
            counter.className = 'text-right text-muted mt-1';
            counter.style.fontSize = '0.875rem';
            textarea.parentNode.appendChild(counter);
            
            function updateCounter() {
                const remaining = maxLength - textarea.value.length;
                counter.textContent = `${textarea.value.length}/${maxLength} caracteres`;
                
                if (remaining < 50) {
                    counter.style.color = '#f44336';
                } else {
                    counter.style.color = '#8b92a5';
                }
            }
            
            updateCounter();
            textarea.addEventListener('input', updateCounter);
        }
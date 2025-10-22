        // Animaciones al cargar la página
        document.addEventListener('DOMContentLoaded', function() {
            // Contador animado para las estadísticas
            const statValues = document.querySelectorAll('.stat-value');
            statValues.forEach(stat => {
                const finalValue = parseInt(stat.textContent) || 0;
                if (finalValue > 0 && finalValue < 100) {
                    let currentValue = 0;
                    const increment = Math.ceil(finalValue / 20);
                    const timer = setInterval(() => {
                        currentValue += increment;
                        if (currentValue >= finalValue) {
                            currentValue = finalValue;
                            clearInterval(timer);
                        }
                        if (!isNaN(currentValue)) {
                            stat.textContent = currentValue;
                        }
                    }, 50);
                }
            });

            // Efecto hover mejorado para las filas
            const tableRows = document.querySelectorAll('.table-custom tbody tr');
            tableRows.forEach(row => {
                row.addEventListener('mouseenter', function() {
                    this.style.boxShadow = '0 4px 12px rgba(33, 150, 243, 0.15)';
                    this.style.borderRadius = '8px';
                });
                
                row.addEventListener('mouseleave', function() {
                    this.style.boxShadow = 'none';
                    this.style.borderRadius = '0';
                });
            });

            // Efecto de pulsación para el botón volver
            const volverBtn = document.querySelector('.btn-volver');
            if (volverBtn) {
                volverBtn.addEventListener('click', function(e) {
                    this.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        this.style.transform = 'translateY(-1px)';
                    }, 100);
                });
            }
        });
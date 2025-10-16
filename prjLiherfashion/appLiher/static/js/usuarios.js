document.addEventListener('DOMContentLoaded', () => {
    const createUserModalId = 'createUserModal';
    const userRoleSelect = document.getElementById('userRole');
    const tableBody = document.getElementById('usersTableBody');
    const REGISTRO_URL = window.REGISTRO_URL || '/';
    const csrfToken = document.querySelector('#createUserForm [name=csrfmiddlewaretoken]')?.value;

    // =====================
    // Funciones de modal
    // =====================
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Resetear formulario y campos adicionales
        const form = modal.querySelector('form');
        if (form) form.reset();
        modal.querySelector('#usuarioFields')?.classList.remove('show');
        modal.querySelector('#adminFields')?.classList.remove('show');
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    };

    // =====================
    // Mostrar campos según rol
    // =====================
    userRoleSelect?.addEventListener('change', e => {
        const rol = e.target.value;
        const usuarioFields = document.getElementById('usuarioFields');
        const adminFields = document.getElementById('adminFields');
        usuarioFields?.classList.remove('show');
        adminFields?.classList.remove('show');
        if (rol === 'usuario') usuarioFields?.classList.add('show');
        if (rol === 'administrador') adminFields?.classList.add('show');
    });

    // =====================
    // Crear usuario vía AJAX
    // =====================
    window.createUser = async function() {
        const rol = userRoleSelect?.value;
        if (!rol) return showToast('Por favor, selecciona un rol.');

        // Construir datos según rol
        const data = { rol };
        if (rol === 'usuario') {
            data.email = document.getElementById('userEmail')?.value.trim() || '';
            data.password1 = document.getElementById('userPassword')?.value || '';
            data.password2 = document.getElementById('userPasswordConfirm')?.value || '';
            data.first_name = document.getElementById('userName')?.value.trim() || '';
            data.last_name = document.getElementById('userLastName')?.value.trim() || '';
            data.phone = document.getElementById('userPhone')?.value.trim() || '';
        } else {
            data.email = document.getElementById('adminEmail')?.value.trim() || '';
            data.password1 = document.getElementById('adminPassword')?.value || '';
            data.password2 = document.getElementById('adminPasswordConfirm')?.value || '';
            data.first_name = document.getElementById('adminName')?.value.trim() || '';
            data.last_name = document.getElementById('adminLastName')?.value.trim() || '';
            data.phone = document.getElementById('adminPhone')?.value.trim() || '';
        }

        try {
            const response = await fetch(REGISTRO_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify(data)
            });

            const res = await response.json().catch(() => {
                throw new Error('No se recibió JSON válido del servidor.');
            });

            if (!response.ok || !res.success) {
                return showToast(res.message || `Error al crear el usuario. Código: ${response.status}`);
            }

            showToast(res.message || "Usuario creado correctamente.", () => {
                closeModal(createUserModalId);
                if (res.redirect_url) window.location.href = res.redirect_url;
            });

            // Actualizar tabla automáticamente
            if (res.user && tableBody) {
                const newRow = document.createElement('tr');
                const statusText = res.user.activo ? 'Activo' : 'Inactivo';
                const statusClass = res.user.activo ? 'status-active' : 'status-inactive';
                const roleText = res.user.rol;
                const roleClass = roleText === 'Administrador' ? 'role-admin' : 'role-usuario';
                const nombre = res.user.nombre || res.user.email;

                newRow.setAttribute('data-status', res.user.activo ? 'active' : 'inactive');
                newRow.setAttribute('data-role', roleText);
                newRow.innerHTML = `
                    <td><div class="user-name">${nombre}</div></td>
                    <td><div class="user-email">${res.user.email}</div></td>
                    <td><span class="role-badge ${roleClass}">${roleText}</span></td>
                    <td><div class="status-indicator ${statusClass}"><span class="status-dot"></span>${statusText}</div></td>
                    <td>${new Date().toLocaleDateString('es-ES')}</td>
                    <td>
                        <div class="actions">
                            <a href="#" class="btn-action btn-view">Ver</a>
                            <a href="/admin/usuarios/editar/${res.user.id}/" class="btn-action btn-edit">Editar</a>
                        </div>
                    </td>
                `;
                tableBody.prepend(newRow);

                // Actualizar estadísticas
                if (res.stats) {
                    document.querySelector('.stat-total .stat-number').textContent = res.stats.activos + res.stats.inactivos;
                    document.querySelector('.stat-active .stat-number').textContent = res.stats.activos;
                    document.querySelector('.stat-inactive .stat-number').textContent = res.stats.inactivos;
                }
            }

        } catch (err) {
            console.error("❌ Error en la conexión:", err);
            showToast("Error de conexión con el servidor.");
        }
    };

    // =====================
    // Toast visual
    // =====================
    window.showToast = function(message, callback = null) {
        const existingToast = document.querySelector('.toast-message');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = 'toast-message';
        toast.textContent = message;
        document.body.appendChild(toast);

        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: '#FF4081',
            color: '#fff',
            padding: '14px 24px',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(255, 64, 129, 0.3)',
            opacity: '1',
            transition: 'opacity 0.5s ease',
            zIndex: '9999',
            fontWeight: '500',
            fontSize: '14px'
        });

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                toast.remove();
                if (callback) callback();
            }, 500);
        }, 3000);
    };
});

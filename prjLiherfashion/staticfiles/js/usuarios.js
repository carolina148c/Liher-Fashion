document.addEventListener('DOMContentLoaded', () => {
  const createUserModalId = 'createUserModal';
  const userRoleSelect = document.getElementById('userRole');
  const REGISTRO_URL = window.REGISTRO_URL || '/';
  const csrfToken = document.querySelector('#createUserForm [name=csrfmiddlewaretoken]')?.value;

  // ==========================
  // 🔹 FUNCIONES GLOBALES DE VALIDACIÓN
  // ==========================
  window.validateNameField = function(input, maxLength = 50, fieldType = 'nombre') {
    window.removeMessage(input);
    let val = input.value;

    // 🔹 Solo letras, tildes, ñ y espacios
    val = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, '').replace(/\s{2,}/g, ' ');
    val = val.trim();

    // 🔹 Campo obligatorio
    if (!val) {
      window.showMessage(input, 'Este campo es obligatorio.');
      input.classList.add('error');
      return false;
    }

    // 🔹 Validar longitud mínima
    if (val.length < 3) {
      window.showMessage(input, 'Debe tener al menos 3 caracteres.');
      input.classList.add('error');
      return false;
    }

    // 🔹 Validar longitud máxima
    if (val.length > maxLength) {
      window.showMessage(input, `Máximo ${maxLength} caracteres.`);
      input.value = val.slice(0, maxLength);
      return false;
    }

    // 🔹 Detectar secuencias incoherentes (repeticiones o sin estructura de nombre)
    const incoherente =
      /^([a-záéíóúüñ])\1{2,}$/i.test(val) || // ejemplo: mmmmmm
      /(.)\1{3,}/i.test(val) || // letras repetidas
      /([a-z]{3,})\s\1/i.test(val) || // palabra repetida
      /^[a-z]{2,}$/.test(val.replace(/\s/g, '')) && !/ /.test(val); // una sola palabra sin estructura

    if (incoherente) {
      window.showMessage(input, `El ${fieldType} parece no ser válido.`);
      input.classList.add('error');
      return false;
    }

    // 🔹 Capitalizar correctamente
    val = val.toLowerCase().replace(/\b([a-záéíóúüñ])/g, c => c.toUpperCase());
    input.value = val;

    window.removeMessage(input);
    return true;
  };

  window.validatePhoneField = function(input) {
    window.removeMessage(input);
    let val = input.value.trim().replace(/\D/g, '');
    input.value = val;

    if (!val) {
      window.showMessage(input, 'Este campo es obligatorio.');
      return false;
    }

    if (val.length !== 10) {
      window.showMessage(input, 'Debe tener exactamente 10 dígitos.');
      return false;
    }

    if (/^(\d)\1{9}$/.test(val)) {
      window.showMessage(input, 'No se permiten números repetidos.');
      return false;
    }

    if (val === '1234567890' || val === '0123456789') {
      window.showMessage(input, 'Número no válido.');
      return false;
    }

    return true;
  };

window.validateEmailRealTime = async function(input) {
  window.removeMessage(input);
  const email = input.value.trim().toLowerCase();
  input.value = email;

  if (!email) {
    window.showMessage(input, 'Este campo es obligatorio.');
    return false;
  }

  if (email.length > 320) {
    window.showMessage(input, 'El correo no puede tener más de 320 caracteres.');
    return false;
  }

  const formatError = validateEmailFormat(email);
  if (formatError) {
    window.showMessage(input, formatError);
    return false;
  }

  // 🔹 NO validar existencia de email si estamos en el modal de edición
  // o si el campo está deshabilitado (correo bloqueado)
  const isEditModal = input.closest('#editUserForm');
  const isDisabled = input.disabled || input.readOnly;
  
  if (isEditModal || isDisabled) {
    return true;
  }

  // 🔹 Solo validar existencia para creación de usuarios
  try {
    const resp = await fetch(`/ajax/validar-email/?email=${encodeURIComponent(email)}`);
    if (resp.ok) {
      const data = await resp.json();
      if (data.exists) {
        window.showMessage(input, 'Ya existe una cuenta con ese correo.');
        return false;
      }
    }
  } catch (err) {
    console.error('Error al validar email:', err);
    // No mostrar error al usuario por fallo de validación de email
  }
  return true;
};

  window.showMessage = function(input, msg) {
    if (!input) return;
    const alertDiv = input.parentElement.querySelector('.input-alert');
    if (alertDiv) {
      alertDiv.textContent = msg;
      input.classList.add('error');
    }
  };

  window.removeMessage = function(input) {
    if (!input) return;
    const alertDiv = input.parentElement.querySelector('.input-alert');
    if (alertDiv) alertDiv.textContent = '';
    input.classList.remove('error');
  };

  window.enforceMaxLength = function(input, maxLength) {
    if (input.value.length > maxLength) {
      input.value = input.value.slice(0, maxLength);
      window.showMessage(input, `Máximo ${maxLength} caracteres.`);
    }
  };

  // ==========================
  // 🔹 FUNCIONES DE MODAL
  // ==========================
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    const form = modal.querySelector('form');
    if (form) form.reset();

    modal.querySelector('#usuarioFields')?.classList.remove('show');
    modal.querySelector('#adminFields')?.classList.remove('show');
    resetValidationMessages();
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    resetValidationMessages();
  };

  function resetValidationMessages() {
    document.querySelectorAll('.input-alert').forEach(el => (el.textContent = ''));
    document.querySelectorAll('input, select').forEach(input => input.classList.remove('error'));
    document.querySelectorAll('.password-requisitos li').forEach(li => li.classList.remove('valid', 'invalid'));
  }

  // ==========================
  // 🔹 CAMPOS SEGÚN ROL
  // ==========================
  function mostrarCamposPorRol(rol) {
    const usuarioFields = document.getElementById('usuarioFields');
    const adminFields = document.getElementById('adminFields');

    usuarioFields?.classList.remove('show');
    adminFields?.classList.remove('show');

    if (rol === 'usuario') usuarioFields?.classList.add('show');
    if (rol === 'administrador') adminFields?.classList.add('show');
  }

  userRoleSelect?.addEventListener('change', e => mostrarCamposPorRol(e.target.value));

  // ==========================
  // 🔹 FORMATEO AUTOMÁTICO
  // ==========================
  function toTitleCase(text) {
    return text
      .toLowerCase()
      .replace(/(^|\s)([a-záéíóúüñ])/giu, (m) => m.toUpperCase()) // convierte primera letra de cada palabra
      .replace(/\s{2,}/g, ' ') // reduce espacios múltiples a uno
      .trim(); // elimina espacios al inicio y final
  }

  // ==========================
  // 🔹 VALIDACIÓN EMAIL
  // ==========================
  function validateEmailFormat(email) {
    if ((email.match(/@/g) || []).length !== 1) return "El correo debe contener exactamente un '@'.";
    if (/^\./.test(email) || /\.$/.test(email)) return 'No puede iniciar ni terminar con punto.';
    if (/\.@|@\.|[<>,;]/.test(email)) return 'El correo contiene caracteres inválidos o punto mal ubicado.';
    const domain = email.split('@')[1];
    if (!/\.[A-Za-z]{2,}$/.test(domain)) return 'El dominio debe terminar en una extensión válida.';
    const re = /^(?![.])(?!.*[.]{2})[A-Za-z0-9._%+\-]{1,64}(?<![.])@(?!-)[A-Za-z0-9\-]{1,63}(?<!-)(?:\.[A-Za-z]{2,})+$/;
    if (!re.test(email)) return 'Formato de correo inválido.';
    return null;
  }

  // 🔹 Validación en tiempo real (nombre y apellido coherentes) - CREAR USUARIO
  document.querySelectorAll('#adminName, #adminLastName').forEach(input => {
    input.addEventListener('input', e => {
      let val = e.target.value;

      // ✅ Solo letras y espacios
      val = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, '').replace(/\s{2,}/g, ' ');

      // ✅ Capitalizar al escribir
      val = val
        .toLowerCase()
        .replace(/\b([a-záéíóúüñ])/g, c => c.toUpperCase());

      e.target.value = val;

      // ✅ Mínimo y máximo
      const maxLength = e.target.id === 'adminLastName' ? 100 : 50;
      const fieldType = e.target.id === 'adminLastName' ? 'apellido' : 'nombre';

      if (val.trim().length < 3) {
        window.showMessage(e.target, `El ${fieldType} debe tener al menos 3 caracteres.`);
      } else if (val.length > maxLength) {
        window.showMessage(e.target, `Máximo ${maxLength} caracteres.`);
        e.target.value = val.slice(0, maxLength);
      } else {
        // ✅ Validar coherencia
        const incoherente =
          /^([a-záéíóúüñ])\1{2,}$/i.test(val) ||
          /(.)\1{3,}/i.test(val) ||
          /([a-z]{3,})\s\1/i.test(val) ||
          /^[a-z]{2,}$/.test(val.replace(/\s/g, '')) && !/ /.test(val);

        if (incoherente) {
          window.showMessage(e.target, `El ${fieldType} parece no ser válido.`);
        } else {
          window.removeMessage(e.target);
        }
      }

      // ✅ Comparar nombre y apellido en tiempo real
      const nameVal = document.getElementById('adminName')?.value.trim().toLowerCase();
      const lastVal = document.getElementById('adminLastName')?.value.trim().toLowerCase();
      const lastInput = document.getElementById('adminLastName');

      if (nameVal && lastVal && nameVal === lastVal) {
        window.showMessage(lastInput, 'Nombre y apellido no pueden ser iguales.');
        lastInput.classList.add('error');
      } else if (lastInput) {
        window.removeMessage(lastInput);
      }
    });
  });

  // ==========================
  // 🔹 CONTRASEÑAS
  // ==========================
  function updatePasswordRequirements(input) {
    window.enforceMaxLength(input, 64);
    const ul = input.parentElement.querySelector('.password-requisitos');
    if (!ul) return;

    const val = input.value;
    const checks = {
      length: val.length >= 8,
      uppercase: /[A-Z]/.test(val),
      lowercase: /[a-z]/.test(val),
      number: /[0-9]/.test(val),
      symbol: /[!@#$%^&*]/.test(val),
      space: !/\s/.test(val),
    };

    ul.querySelectorAll('li').forEach(li => {
      const type = li.dataset.req;
      li.classList.toggle('valid', checks[type]);
      li.classList.toggle('invalid', !checks[type]);
    });
  }

  ['userPassword', 'adminPassword'].forEach(id => {
    const input = document.getElementById(id);
    const confirmInput = document.getElementById(id + 'Confirm');
    const ul = input.parentElement.querySelector('.password-requisitos');

    input.addEventListener('focus', () => ul?.classList.add('show'));
    input.addEventListener('blur', () => ul?.classList.remove('show'));
    input.addEventListener('input', () => updatePasswordRequirements(input));
    confirmInput.addEventListener('input', () => validatePasswords(input, confirmInput));
  });

  function validatePasswords(passwordInput, confirmInput) {
    window.removeMessage(passwordInput);
    window.removeMessage(confirmInput);

    const p1 = passwordInput.value;
    const p2 = confirmInput.value;

    if (!p1 || !p2) {
      if (!p1) window.showMessage(passwordInput, 'Este campo es obligatorio.');
      if (!p2) window.showMessage(confirmInput, 'Debes confirmar la contraseña.');
      return false;
    }

    const valid = {
      length: p1.length >= 8,
      uppercase: /[A-Z]/.test(p1),
      lowercase: /[a-z]/.test(p1),
      number: /[0-9]/.test(p1),
      symbol: /[!@#$%^&*]/.test(p1),
      space: !/\s/.test(p1),
    };

    if (!Object.values(valid).every(Boolean)) {
      window.showMessage(passwordInput, 'Contraseña no cumple todos los requisitos.');
      return false;
    }
    if (p1 !== p2) {
      window.showMessage(confirmInput, 'Las contraseñas no coinciden.');
      return false;
    }
    return true;
  }



document.querySelectorAll('.toggle-password').forEach(button => {
  button.addEventListener('click', () => {
    const inputId = button.getAttribute('data-target');
    const input = document.getElementById(inputId);
    const icon = button.querySelector('i');

    if (input.type === 'password') {
      input.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    } else {
      input.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  });
});




  // ==========================
  // 🔹 VALIDACIÓN EN TIEMPO REAL - CREAR USUARIO
  // ==========================
  const phoneInput = document.getElementById('adminPhone');

  if (phoneInput) phoneInput.addEventListener('input', () => {
    window.enforceMaxLength(phoneInput, 10);
    window.validatePhoneField(phoneInput);
  });

  ['userEmail', 'adminEmail'].forEach(id => {
    const input = document.getElementById(id);
    if (input) input.addEventListener('input', e => {
      window.enforceMaxLength(e.target, 320);
      window.validateEmailRealTime(e.target);
    });
  });

  // ==========================
  // 🔹 CREAR USUARIO
  // ==========================
  window.createUser = async function () {
    const rol = userRoleSelect?.value;
    if (!rol) {
      window.showMessage(userRoleSelect, 'Selecciona un rol.');
      return;
    }

    let emailInput, passwordInput, confirmInput, first_name = '', last_name = '', phone = '';

    if (rol === 'usuario') {
      emailInput = document.getElementById('userEmail');
      passwordInput = document.getElementById('userPassword');
      confirmInput = document.getElementById('userPasswordConfirm');
    } else {
      emailInput = document.getElementById('adminEmail');
      passwordInput = document.getElementById('adminPassword');
      confirmInput = document.getElementById('adminPasswordConfirm');
      first_name = toTitleCase(document.getElementById('adminName').value.trim());
      last_name = toTitleCase(document.getElementById('adminLastName').value.trim());
      phone = document.getElementById('adminPhone').value.trim();
    }

    const emailOk = await window.validateEmailRealTime(emailInput);
    const passOk = validatePasswords(passwordInput, confirmInput);
    const nameOk = rol === 'administrador' ? window.validateNameField(document.getElementById('adminName')) : true;
    const lastOk = rol === 'administrador' ? window.validateNameField(document.getElementById('adminLastName')) : true;
    const phoneOk = rol === 'administrador' ? window.validatePhoneField(document.getElementById('adminPhone')) : true;

    if (rol === 'administrador') {
      const nameVal = document.getElementById('adminName').value.trim().toLowerCase();
      const lastVal = document.getElementById('adminLastName').value.trim().toLowerCase();
      if (nameVal && lastVal && nameVal === lastVal) {
        window.showMessage(document.getElementById('adminLastName'), 'Nombre y apellido no pueden ser iguales.');
        return;
      }
    }

    if (!emailOk || !passOk || !nameOk || !lastOk || !phoneOk) return;

    // 🔹 Capturar permisos marcados
    const permisosSeleccionados = Array.from(
      document.querySelectorAll('#adminPermissions input[name="permiso"]:checked')
    ).map(p => p.value);

    const payload = {
      rol,
      email: emailInput.value.trim().toLowerCase(),
      password1: passwordInput.value,
      password2: confirmInput.value,
      first_name,
      last_name,
      phone,
      permisos: permisosSeleccionados, // ✅ Se envía al backend
    };

    try {
      const response = await fetch(REGISTRO_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(payload),
      });

      const res = await response.json().catch(() => {
        throw new Error('Respuesta no válida del servidor.');
      });

      if (!response.ok || !res.success) {
        window.showToast(res.message || `Error al crear usuario. Código: ${response.status}`);
        return;
      }

      window.showToast(res.message || 'Usuario creado correctamente.', () => {
        window.closeModal(createUserModalId);
        if (res.redirect_url) window.location.href = res.redirect_url;
      });
    } catch (err) {
      console.error('❌ Error en la conexión:', err);
      window.showToast('Error de conexión con el servidor.');
    }
  };

  // ==========================
  // 🔹 TOAST
  // ==========================
  window.showToast = function (msg, callback = null) {
    const existing = document.querySelector('.toast-message');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = msg;
    document.body.appendChild(toast);

    Object.assign(toast.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      background: '#ff4081',
      color: '#fff',
      padding: '14px 24px',
      borderRadius: '10px',
      boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
      opacity: '1',
      transition: 'opacity 0.5s ease',
      zIndex: '9999',
      fontWeight: '500',
      fontSize: '14px',
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        toast.remove();
        if (callback) callback();
      }, 500);
    }, 3000);
  };

  // ==========================
  // 🔹 TRIM Y ENTER 
  // ==========================
  const allInputs = document.querySelectorAll('#createUserForm input, #createUserForm select');

  allInputs.forEach((input, index) => {
    input.addEventListener('blur', () => {
      if (input.type === 'email') {
        input.value = input.value.trim().toLowerCase();
      } else if (input.type === 'text') {
        let val = input.value
          .replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, '')
          .replace(/\s{2,}/g, ' ')
          .trim(); // 🔹 elimina espacios inicio/fin

        // Capitaliza correctamente
        val = val.replace(/\b([a-záéíóúüñ])/g, c => c.toUpperCase());

        input.value = val;
      }
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const nextInput = allInputs[index + 1];
        if (nextInput) nextInput.focus();
        else document.querySelector('#createUserForm button[type=button]')?.click();
      }
    });
  });


// ==========================
// 🔹 INICIALIZACIÓN DE VALIDACIONES PARA EDITAR USUARIO
// ==========================
function initializeEditUserValidations() {
  const editForm = document.getElementById('editUserForm');
  if (!editForm) return;

  // Validación en tiempo real para campos de edición
  const editNameInput = document.getElementById('editFirstName');
  const editLastNameInput = document.getElementById('editLastName');
  const editPhoneInput = document.getElementById('editPhone');
  const editEmailInput = document.getElementById('editEmail');

  // 🔹 VALIDACIÓN EN TIEMPO REAL PARA NOMBRE
  if (editNameInput) {
    editNameInput.addEventListener('input', (e) => {
      let val = e.target.value;
      val = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, '').replace(/\s{2,}/g, ' ');
      val = val.toLowerCase().replace(/\b([a-záéíóúüñ])/g, c => c.toUpperCase());
      e.target.value = val;
      window.enforceMaxLength(e.target, 50);
      
      // 🔹 Validar en tiempo real
      if (val.trim().length > 0) {
        window.validateNameField(e.target, 50, "nombre");
      } else {
        window.removeMessage(e.target);
      }
    });

    // Validar también al perder el foco
    editNameInput.addEventListener('blur', () => {
      if (editNameInput.value.trim().length > 0) {
        window.validateNameField(editNameInput, 50, "nombre");
      }
    });
  }

  // 🔹 VALIDACIÓN EN TIEMPO REAL PARA APELLIDO
  if (editLastNameInput) {
    editLastNameInput.addEventListener('input', (e) => {
      let val = e.target.value;
      val = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, '').replace(/\s{2,}/g, ' ');
      val = val.toLowerCase().replace(/\b([a-záéíóúüñ])/g, c => c.toUpperCase());
      e.target.value = val;
      window.enforceMaxLength(e.target, 100);
      
      // 🔹 Validar en tiempo real
      if (val.trim().length > 0) {
        window.validateNameField(e.target, 100, "apellido");
      } else {
        window.removeMessage(e.target);
      }
    });

    editLastNameInput.addEventListener('blur', () => {
      if (editLastNameInput.value.trim().length > 0) {
        window.validateNameField(editLastNameInput, 100, "apellido");
      }
    });
  }

  // 🔹 VALIDACIÓN EN TIEMPO REAL PARA TELÉFONO
  if (editPhoneInput) {
    editPhoneInput.addEventListener('input', (e) => {
      e.target.value = e.target.value.replace(/\D/g, '');
      window.enforceMaxLength(e.target, 10);
      
      // 🔹 Validar en tiempo real
      if (e.target.value.length > 0) {
        window.validatePhoneField(e.target);
      } else {
        window.removeMessage(e.target);
      }
    });

    editPhoneInput.addEventListener('blur', () => {
      if (editPhoneInput.value.length > 0) {
        window.validatePhoneField(editPhoneInput);
      }
    });
  }

  // 🔹 VALIDACIÓN EN TIEMPO REAL PARA EMAIL
  if (editEmailInput) {
    editEmailInput.addEventListener('input', (e) => {
      window.enforceMaxLength(e.target, 320);
      
      // 🔹 Validar en tiempo real solo si no está deshabilitado
      if (!e.target.disabled && e.target.value.length > 0) {
        window.validateEmailRealTime(e.target);
      } else {
        window.removeMessage(e.target);
      }
    });

    editEmailInput.addEventListener('blur', () => {
      if (!editEmailInput.disabled && editEmailInput.value.length > 0) {
        window.validateEmailRealTime(editEmailInput);
      }
    });
  }

  // 🔹 VALIDAR QUE NOMBRE Y APELLIDO NO SEAN IGUALES EN TIEMPO REAL
  if (editNameInput && editLastNameInput) {
    const validateNameEquality = () => {
      const nameVal = editNameInput.value.trim().toLowerCase();
      const lastVal = editLastNameInput.value.trim().toLowerCase();
      
      if (nameVal && lastVal && nameVal === lastVal) {
        window.showMessage(editLastNameInput, 'Nombre y apellido no pueden ser iguales.');
        editLastNameInput.classList.add('error');
      } else {
        // Solo remover el mensaje de igualdad, no otros errores
        const alertDiv = editLastNameInput.parentElement.querySelector('.input-alert');
        if (alertDiv && alertDiv.textContent === 'Nombre y apellido no pueden ser iguales.') {
          window.removeMessage(editLastNameInput);
        }
      }
    };

    editNameInput.addEventListener('input', validateNameEquality);
    editLastNameInput.addEventListener('input', validateNameEquality);
  }
}

  // Inicializar validaciones para editar usuario
  initializeEditUserValidations();
});

// ==========================
// 🔹 TOGGLE ESTADO USUARIO
// ==========================
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".toggle-status").forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      const userId = this.getAttribute("data-id");
      const estadoActual = this.checked;
      const accion = estadoActual ? "activar" : "desactivar";

      if (!confirm(`¿Estás seguro que deseas ${accion} este usuario?`)) {
        this.checked = !estadoActual;
        return;
      }

      fetch(`/usuarios/toggle/${userId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken()
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            const text = this.closest("td").querySelector(".status-text");
            if (data.nuevo_estado) {
                text.textContent = "Activo";
                text.classList.remove("inactive-text");
                text.classList.add("active-text");
            } else {
                text.textContent = "Inactivo";
                text.classList.remove("active-text");
                text.classList.add("inactive-text");
            }
          } else {
            alert("No se pudo actualizar el estado.");
            this.checked = !estadoActual; // revertir
          }
        })
        .catch(() => {
          alert("Error al cambiar el estado del usuario.");
          this.checked = !estadoActual; // revertir
        });
    });
  });
});

function getCSRFToken() {
  let cookieValue = null;
  const name = "csrftoken";
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}


// ==========================
// 🔹 FILTROS DE BÚSQUEDA
// ==========================
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const roleFilter = document.getElementById("roleFilter");
    const tableBody = document.getElementById("usersTableBody");

    function filtrarUsuarios() {
        const texto = searchInput.value.toLowerCase();
        const estado = statusFilter.value;
        const rol = roleFilter.value;

        const filas = tableBody.querySelectorAll("tr");

        filas.forEach(fila => {
            const nombre = fila.querySelector(".user-cell").textContent.toLowerCase();
            const correo = fila.children[1].textContent.toLowerCase();
            const estadoFila = fila.dataset.status;  // active | inactive
            const rolFila = fila.dataset.role;        // Administrador | Usuario

            let coincideBusqueda = nombre.includes(texto) || correo.includes(texto);
            let coincideEstado = estado === "" || estado === estadoFila;
            let coincideRol = rol === "" || rol === rolFila;

            if (coincideBusqueda && coincideEstado && coincideRol) {
                fila.style.display = "";
            } else {
                fila.style.display = "none";
            }
        });
    }

    searchInput.addEventListener("input", filtrarUsuarios);
    statusFilter.addEventListener("change", filtrarUsuarios);
    roleFilter.addEventListener("change", filtrarUsuarios);

    // 🔹 BOTÓN LIMPIAR FILTROS
    const clearBtn = document.getElementById("clearFilters");
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            searchInput.value = "";
            statusFilter.value = "";
            roleFilter.value = "";
            filtrarUsuarios();
        });
    }
});












// ==========================
// 🔹 MODAL EDITAR USUARIO
// ==========================
window.openEditUser = function(id) {
  const modal = document.getElementById("editUserModal");
  modal.style.display = "flex";

  // Limpiar campos previos
  document.querySelectorAll("#editUserForm input, #editUserForm select").forEach(el => {
    el.classList.remove("error");
    const alert = el.parentElement.querySelector(".input-alert");
    if (alert) alert.textContent = "";
  });

  // Mostrar estado de carga
  document.getElementById("editFirstName").value = "Cargando...";

  fetch(`/usuarios/obtener/${id}/`)
    .then(response => {
      if (!response.ok) throw new Error("Error al obtener datos del usuario");
      return response.json();
    })
    .then(data => {
      document.getElementById("editUserId").value = data.id;
      document.getElementById("editFirstName").value = data.first_name || "";
      document.getElementById("editLastName").value = data.last_name || "";
      document.getElementById("editEmail").value = data.email || "";
      document.getElementById("editPhone").value = data.phone || "";
      document.getElementById("editRole").value = data.is_staff ? "Administrador" : "Usuario";
      document.getElementById("editActive").value = data.is_active ? "True" : "False";
      document.getElementById("editLastLogin").value = data.last_login || "";
      document.getElementById("editDateJoined").value = data.date_joined || "";

      const isAdmin = data.is_staff;

      // Mostrar/ocultar campos según tipo
      const adminFields = ["editFirstName", "editLastName", "editPhone"];
      adminFields.forEach(id => {
        const group = document.getElementById(id)?.closest(".form-group");
        if (group) group.style.display = isAdmin ? "block" : "none";
      });

      const commonFields = ["editEmail", "editRole", "editLastLogin", "editDateJoined", "editActive"];
      commonFields.forEach(id => {
        const group = document.getElementById(id)?.closest(".form-group");
        if (group) group.style.display = "block";
      });

      // Habilitar/deshabilitar
      if (isAdmin) {
        ["editFirstName", "editLastName", "editPhone", "editActive"].forEach(id => {
          const el = document.getElementById(id);
          el.disabled = false;
          el.classList.remove("readonly");
        });
        ["editEmail", "editRole", "editLastLogin", "editDateJoined"].forEach(id => {
          const el = document.getElementById(id);
          el.disabled = true;
          el.classList.add("readonly");
        });
      } else {
        document.querySelectorAll("#editUserForm input, #editUserForm select").forEach(el => {
          el.disabled = true;
          el.classList.add("readonly");
        });
        const activeEl = document.getElementById("editActive");
        activeEl.disabled = false;
        activeEl.classList.remove("readonly");
      }

      // 🔹 Cargar permisos si el usuario es administrador
      if (isAdmin) {
        fetch(`/usuarios/ver/${id}/`)
          .then(res => res.json())
          .then(permData => {
            const permisosContainer = document.getElementById("editPermisosContainer");
            const permisosSection = document.getElementById("editPermisosSection");

            permisosContainer.innerHTML = "";

            if (permData.permissions && permData.permissions.length > 0) {
              permisosSection.style.display = "block";
              permisosContainer.style.display = "grid";

              // 🔹 Mostrar todos los permisos (activos e inactivos)
              permData.permissions.forEach(perm => {
                const div = document.createElement("label");
                div.className = "permiso-item";
                div.innerHTML = `
                  <input type="checkbox" name="permiso" value="${perm.nombre}" ${perm.activo ? "checked" : ""}>
                  <span>${perm.nombre}</span>
                `;
                permisosContainer.appendChild(div);
              });
            } else {
              permisosSection.style.display = "block";
              permisosContainer.innerHTML = "<p>No hay permisos registrados para este usuario.</p>";
            }
          })
          .catch(err => {
            console.error("Error cargando permisos:", err);
            document.getElementById("editPermisosContainer").innerHTML = "<p>Error al cargar permisos.</p>";
          });
      } else {
        // 🔹 Si no es admin, ocultar completamente la sección
        document.getElementById("editPermisosSection").style.display = "none";
      }


      setTimeout(() => {
        initializeEditUserValidations();
      }, 100);
    })
    .catch(error => {
      console.error("Error:", error);
      alert("No se pudo cargar la información del usuario.");
    });
};


// ==========================
// 🔹 VALIDAR Y GUARDAR EDICIÓN DE USUARIO
// ==========================
window.saveEditedUser = async function() {
  const id = document.getElementById("editUserId").value;
  const isAdmin = document.getElementById("editRole").value === "Administrador";
  const activeInput = document.getElementById("editActive");

  let valid = true;

  if (isAdmin) {
    const firstName = document.getElementById("editFirstName");
    const lastName = document.getElementById("editLastName");
    const phone = document.getElementById("editPhone");

    const nameOk = window.validateNameField(firstName, 50, "nombre");
    const lastOk = window.validateNameField(lastName, 100, "apellido");
    const phoneOk = window.validatePhoneField(phone);

    if (!nameOk || !lastOk || !phoneOk) valid = false;

    // Validar al menos un permiso activo
    const checkboxes = document.querySelectorAll('#editPermisosContainer input[type="checkbox"]');
    const algunoMarcado = Array.from(checkboxes).some(chk => chk.checked);

    if (!algunoMarcado) {
      window.showToast("Debe haber al menos un permiso activo antes de guardar.");
      valid = false;
    }
  }

  if (!valid) {
    window.showToast("Por favor corrige los errores antes de guardar.");
    return;
  }

  // Preparar datos
  const formData = new FormData();
  formData.append('is_admin', isAdmin);
  formData.append('is_active', activeInput.value === "True");

  if (isAdmin) {
    formData.append('first_name', document.getElementById("editFirstName").value.trim());
    formData.append('last_name', document.getElementById("editLastName").value.trim());
    formData.append('phone', document.getElementById("editPhone").value.trim());
    formData.append('email', document.getElementById("editEmail").value.trim().toLowerCase());

    // Agregar permisos seleccionados
    const permisos = Array.from(document.querySelectorAll('#editPermisosContainer input[type="checkbox"]')).map(chk => ({
      nombre: chk.value,
      activo: chk.checked
    }));
    formData.append('permisos', JSON.stringify(permisos));
  }

  try {
    const response = await fetch(`/usuarios-editar/${id}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCSRFToken(),
      },
      body: formData
    });

    if (response.ok) {
      window.showToast("Usuario actualizado correctamente.", () => {
        window.closeModal("editUserModal");
        window.location.reload();
      });
    } else {
      const errorText = await response.text();
      console.error("Error:", errorText);
      window.showToast("Error al guardar los cambios. Código: " + response.status);
    }
  } catch (error) {
    console.error("❌ Error al actualizar usuario:", error);
    window.showToast("Error de conexión con el servidor.");
  }
};







// ==========================
// 🔹 MODAL VER USUARIO
// ==========================
window.verUsuario = function(userId) {
  fetch(`/usuarios/ver/${userId}/`)
    .then(response => response.json())
    .then(data => {
      document.getElementById('usuarioIniciales').innerText = data.initials || '?';
      document.getElementById('usuarioNombre').innerText = data.full_name || 'Sin nombre';
      document.getElementById('usuarioRol').innerText = data.role;

      const estadoEl = document.getElementById('usuarioEstado');
      estadoEl.innerText = data.status;
      estadoEl.className = `status-badge ${data.status === 'Activo' ? 'active' : 'inactive'}`;

      document.getElementById('usuarioFullName').innerText = data.full_name;
      document.getElementById('usuarioEmail').innerText = data.email;
      document.getElementById('usuarioDateJoined').innerText = data.date_joined;
      document.getElementById('usuarioLastLogin').innerText = data.last_login;

      const telefonoItem = document.getElementById('telefonoItem');
      if (data.phone) {
        telefonoItem.style.display = 'block';
        document.getElementById('usuarioPhone').innerText = data.phone;
      } else {
        telefonoItem.style.display = 'none';
      }

      // 🔹 Permisos (mostrar todos)
      const permisosSection = document.getElementById('permisosSection');
      const permisosContainer = document.getElementById('usuarioPermisos');
      if (data.permissions && data.permissions.length > 0) {
        permisosSection.style.display = 'block';
        permisosContainer.innerHTML = '';
        data.permissions.forEach(permiso => {
          const div = document.createElement('div');
          div.className = `permission-badge ${permiso.activo ? 'granted' : 'denied'}`;
          div.innerHTML = `
            <i class="fas ${permiso.activo ? 'fa-check-circle' : 'fa-lock'}"></i>
            <span>${permiso.nombre}</span>
          `;
          permisosContainer.appendChild(div);
        });
      } else {
        permisosSection.style.display = 'none';
        permisosContainer.innerHTML = '';
      }

      document.getElementById('btnEditarUsuario').onclick = () => {
        window.closeModal('verUsuarioModal');
        setTimeout(() => window.openEditUser(userId), 300);
      };

      window.openModal('verUsuarioModal');
    })
    .catch(err => {
      console.error('Error al cargar usuario:', err);
      alert('Error al cargar los datos del usuario');
    });
};


window.openModal = function(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
};

window.closeModal = function(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.style.display = 'none';
  document.body.style.overflow = 'auto';
};


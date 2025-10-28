document.addEventListener('DOMContentLoaded', () => {
  const createUserModalId = 'createUserModal';
  const userRoleSelect = document.getElementById('userRole');
  const REGISTRO_URL = window.REGISTRO_URL || '/';
  const csrfToken = document.querySelector('#createUserForm [name=csrfmiddlewaretoken]')?.value;

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

  function enforceMaxLength(input, maxLength) {
    if (input.value.length > maxLength) {
      input.value = input.value.slice(0, maxLength);
      showMessage(input, `Máximo ${maxLength} caracteres.`);
    }
  }

  // ==========================
  // 🔹 VALIDACIÓN EMAIL
  // ==========================
  async function validateEmailRealTime(input) {
    removeMessage(input);
    const email = input.value.trim().toLowerCase();
    input.value = email;

    if (!email) {
      showMessage(input, 'Este campo es obligatorio.');
      return false;
    }

    if (email.length > 320) {
      showMessage(input, 'El correo no puede tener más de 320 caracteres.');
      return false;
    }

    const formatError = validateEmailFormat(email);
    if (formatError) {
      showMessage(input, formatError);
      return false;
    }

    try {
      const resp = await fetch(`/ajax/validar-email/?email=${encodeURIComponent(email)}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.exists) {
          showMessage(input, 'Ya existe una cuenta con ese correo.');
          return false;
        }
      }
    } catch (err) {
      console.error('Error al validar email:', err);
    }
    return true;
  }

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



// ==========================
// 🔹 VALIDACIÓN NOMBRES Y APELLIDOS 
// ==========================
function validateNameField(input, maxLength = 50, fieldType = 'nombre') {
  removeMessage(input);
  let val = input.value;

  // 🔹 Solo letras, tildes, ñ y espacios
  val = val.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, '').replace(/\s{2,}/g, ' ');
  val = val.trim();

  // 🔹 Campo obligatorio
  if (!val) {
    showMessage(input, 'Este campo es obligatorio.');
    input.classList.add('error');
    return false;
  }

  // 🔹 Validar longitud mínima
  if (val.length < 3) {
    showMessage(input, 'Debe tener al menos 3 caracteres.');
    input.classList.add('error');
    return false;
  }

  // 🔹 Validar longitud máxima
  if (val.length > maxLength) {
    showMessage(input, `Máximo ${maxLength} caracteres.`);
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
    showMessage(input, `El ${fieldType} parece no ser válido.`);
    input.classList.add('error');
    return false;
  }

  // 🔹 Capitalizar correctamente
  val = val.toLowerCase().replace(/\b([a-záéíóúüñ])/g, c => c.toUpperCase());
  input.value = val;

  removeMessage(input);
  return true;
}

// 🔹 Validación en tiempo real (nombre y apellido coherentes)
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
      showMessage(e.target, `El ${fieldType} debe tener al menos 3 caracteres.`);
    } else if (val.length > maxLength) {
      showMessage(e.target, `Máximo ${maxLength} caracteres.`);
      e.target.value = val.slice(0, maxLength);
    } else {
      // ✅ Validar coherencia
      const incoherente =
        /^([a-záéíóúüñ])\1{2,}$/i.test(val) ||
        /(.)\1{3,}/i.test(val) ||
        /([a-z]{3,})\s\1/i.test(val) ||
        /^[a-z]{2,}$/.test(val.replace(/\s/g, '')) && !/ /.test(val);

      if (incoherente) {
        showMessage(e.target, `El ${fieldType} parece no ser válido.`);
      } else {
        removeMessage(e.target);
      }
    }

    // ✅ Comparar nombre y apellido en tiempo real
    const nameVal = document.getElementById('adminName')?.value.trim().toLowerCase();
    const lastVal = document.getElementById('adminLastName')?.value.trim().toLowerCase();
    const lastInput = document.getElementById('adminLastName');

    if (nameVal && lastVal && nameVal === lastVal) {
      showMessage(lastInput, 'Nombre y apellido no pueden ser iguales.');
      lastInput.classList.add('error');
    } else if (lastInput) {
      removeMessage(lastInput);
    }
  });
});




  // ==========================
  // 🔹 VALIDACIÓN TELÉFONO
  // ==========================
  function validatePhoneField(input) {
    removeMessage(input);
    let val = input.value.trim().replace(/\D/g, '');
    input.value = val;

    if (!val) {
      showMessage(input, 'Este campo es obligatorio.');
      return false;
    }

    if (val.length !== 10) {
      showMessage(input, 'Debe tener exactamente 10 dígitos.');
      return false;
    }

    if (/^(\d)\1{9}$/.test(val)) {
      showMessage(input, 'No se permiten números repetidos.');
      return false;
    }

    if (val === '1234567890' || val === '0123456789') {
      showMessage(input, 'Número no válido.');
      return false;
    }

    return true;
  }

  // ==========================
  // 🔹 MENSAJES DE ERROR
  // ==========================
  function showMessage(input, msg) {
    if (!input) return;
    const alertDiv = input.parentElement.querySelector('.input-alert');
    if (alertDiv) {
      alertDiv.textContent = msg;
      input.classList.add('error');
    }
  }

  function removeMessage(input) {
    if (!input) return;
    const alertDiv = input.parentElement.querySelector('.input-alert');
    if (alertDiv) alertDiv.textContent = '';
    input.classList.remove('error');
  }

  // ==========================
  // 🔹 CONTRASEÑAS
  // ==========================
  function updatePasswordRequirements(input) {
    enforceMaxLength(input, 64);
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
    removeMessage(passwordInput);
    removeMessage(confirmInput);

    const p1 = passwordInput.value;
    const p2 = confirmInput.value;

    if (!p1 || !p2) {
      if (!p1) showMessage(passwordInput, 'Este campo es obligatorio.');
      if (!p2) showMessage(confirmInput, 'Debes confirmar la contraseña.');
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
      showMessage(passwordInput, 'Contraseña no cumple todos los requisitos.');
      return false;
    }
    if (p1 !== p2) {
      showMessage(confirmInput, 'Las contraseñas no coinciden.');
      return false;
    }
    return true;
  }

  // ==========================
  // 🔹 VALIDACIÓN EN TIEMPO REAL
  // ==========================
  const phoneInput = document.getElementById('adminPhone');

  if (phoneInput) phoneInput.addEventListener('input', () => {
    enforceMaxLength(phoneInput, 10);
    validatePhoneField(phoneInput);
  });

  ['userEmail', 'adminEmail'].forEach(id => {
    const input = document.getElementById(id);
    if (input) input.addEventListener('input', e => {
      enforceMaxLength(e.target, 320);
      validateEmailRealTime(e.target);
    });
  });

  // ==========================
  // 🔹 CREAR USUARIO
  // ==========================
window.createUser = async function () {
  const rol = userRoleSelect?.value;
  if (!rol) {
    showMessage(userRoleSelect, 'Selecciona un rol.');
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

  const emailOk = await validateEmailRealTime(emailInput);
  const passOk = validatePasswords(passwordInput, confirmInput);
  const nameOk = rol === 'administrador' ? validateNameField(document.getElementById('adminName')) : true;
  const lastOk = rol === 'administrador' ? validateNameField(document.getElementById('adminLastName')) : true;
  const phoneOk = rol === 'administrador' ? validatePhoneField(document.getElementById('adminPhone')) : true;

  if (rol === 'administrador') {
    const nameVal = document.getElementById('adminName').value.trim().toLowerCase();
    const lastVal = document.getElementById('adminLastName').value.trim().toLowerCase();
    if (nameVal && lastVal && nameVal === lastVal) {
      showMessage(document.getElementById('adminLastName'), 'Nombre y apellido no pueden ser iguales.');
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
      showToast(res.message || `Error al crear usuario. Código: ${response.status}`);
      return;
    }

    showToast(res.message || 'Usuario creado correctamente.', () => {
      closeModal(createUserModalId);
      if (res.redirect_url) window.location.href = res.redirect_url;
    });
  } catch (err) {
    console.error('❌ Error en la conexión:', err);
    showToast('Error de conexión con el servidor.');
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
});

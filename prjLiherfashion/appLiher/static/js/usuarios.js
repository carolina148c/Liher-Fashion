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
      .replace(/(^|\s)([a-záéíóúüñ])/giu, (m) => m.toUpperCase()) // conserva tildes y ñ
      .replace(/\s+/g, ' ')
      .trim();
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
  function validateNameField(input, maxLength = 50) {
    removeMessage(input);
    let val = input.value.replace(/\s+/g, ' ').trim();

    if (!val) {
      showMessage(input, 'Este campo es obligatorio.');
      return false;
    }

    enforceMaxLength(input, maxLength);

    const regex = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$/;
    if (!regex.test(val)) {
      showMessage(input, 'Solo se permiten letras, tildes, ñ y espacios.');
      return false;
    }

    input.value = toTitleCase(val);
    return true;
  }

  // Bloquear caracteres inválidos en tiempo real (nombre y apellido)
  document.addEventListener('input', e => {
    if (e.target.id === 'adminName' || e.target.id === 'adminLastName') {
      e.target.value = e.target.value
        .replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, '') // solo letras, ñ, tildes y espacios
        .replace(/\s{2,}/g, ' ');
    }
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
  const nameInput = document.getElementById('adminName');
  const lastNameInput = document.getElementById('adminLastName');
  const phoneInput = document.getElementById('adminPhone');

  if (nameInput) nameInput.addEventListener('input', () => validateNameField(nameInput, 50));
  if (lastNameInput) lastNameInput.addEventListener('input', () => validateNameField(lastNameInput, 100));
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

    if (!emailOk || !passOk || !nameOk || !lastOk || !phoneOk) return;

    const payload = {
      rol,
      email: emailInput.value.trim().toLowerCase(),
      password1: passwordInput.value,
      password2: confirmInput.value,
      first_name,
      last_name,
      phone,
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
        // ✅ Permitir espacios entre nombres y apellidos
        let val = input.value
          .replace(/\s+/g, ' ') // reemplaza espacios múltiples por uno
          .trim();
        input.value = toTitleCase(val);
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

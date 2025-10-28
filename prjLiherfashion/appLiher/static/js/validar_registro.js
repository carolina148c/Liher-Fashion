// static/js/validar_registro.js
document.addEventListener("DOMContentLoaded", function () {
  console.debug("validar_registro.js cargado");

  const form = document.getElementById('form-register');
  if (!form) return;

  const emailInput = document.getElementById('email');
  const pass1 = document.getElementById('password1');
  const pass2 = document.getElementById('password2');
  const alertaError = form.querySelector('.alerta-error');
  const alertaExito = form.querySelector('.alerta-exito');

  function showMessage(input, msg) {
    if (!input) return;
    removeMessage(input);
    const div = document.createElement('div');
    div.className = 'input-alert';
    div.textContent = msg;
    input.insertAdjacentElement('afterend', div);
    input.classList.add('error');
  }

  function removeMessage(input) {
    if (!input) return;
    const next = input.nextElementSibling;
    if (next && next.classList.contains('input-alert')) next.remove();
    input.classList.remove('error');
  }

  // ------------------ Validación correo ------------------
  function validateEmailFormat(email) {
    if ((email.match(/@/g) || []).length > 1) return "El correo no puede contener más de un '@'.";
    if (/^\./.test(email) || /\.$/.test(email)) return "El correo no puede iniciar ni terminar con punto.";
    if (/\.@/.test(email) || /@\./.test(email)) return "El correo no puede tener un punto pegado al '@'.";
    if (/[<>,;]/.test(email)) return "El correo contiene caracteres no permitidos.";
    const parts = email.split("@");
    if (parts.length === 2) {
      const domain = parts[1];
      if (/^-/.test(domain)) return "El dominio no puede iniciar con guion.";
      if (!/\.[A-Za-z]{2,}$/.test(domain)) return "El dominio debe terminar en una extensión válida (ej: .com).";
    }
    const re = /^(?![.])(?!.*[.]{2})[A-Za-z0-9._%+\-]{1,64}(?<![.])@(?!-)[A-Za-z0-9\-]{1,63}(?<!-)(?:\.[A-Za-z]{2,})+$/;
    if (!re.test(email)) return "Formato de correo inválido. Ej: nombre@dominio.com";
    return null;
  }

  async function checkEmail() {
    if (!emailInput) return false;
    const raw = emailInput.value;
    removeMessage(emailInput);

    if (!raw || raw.trim() === "") {
      showMessage(emailInput, "El correo es obligatorio.");
      return false;
    }
    if (/\s/.test(raw)) {
      showMessage(emailInput, "El correo no puede contener espacios.");
      return false;
    }

    const email = raw.trim();
    const formatError = validateEmailFormat(email);
    if (formatError) {
      showMessage(emailInput, formatError);
      return false;
    }
    if (email.length > 320) {
      showMessage(emailInput, "El correo es demasiado largo (máx. 320 caracteres).");
      return false;
    }

    // Validación en tiempo real si el correo ya está registrado
    try {
      const resp = await fetch(`/ajax/validar-email/?email=${encodeURIComponent(email)}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.exists) {
          showMessage(emailInput, "Ya existe una cuenta con ese correo. Ve a iniciar sesión.");
          return false;
        } else {
          removeMessage(emailInput);
          return true;
        }
      }
    } catch (err) {
      console.error("Error fetch validate-email:", err);
      return true; // No bloquear si falla la consulta
    }
    return true;
  }



  // Validación en tiempo real mientras escribe
  if (emailInput) {
    emailInput.addEventListener('input', async () => { await checkEmail(); });
    emailInput.addEventListener('blur', async () => { 
      emailInput.value = emailInput.value.trim();
      await checkEmail();
      pass1.focus();
    });
  }

  // ------------------ Validación contraseñas ------------------
  const requisitos = {
    length: document.getElementById('req-length'),
    uppercase: document.getElementById('req-uppercase'),
    lowercase: document.getElementById('req-lowercase'),
    number: document.getElementById('req-number'),
    symbol: document.getElementById('req-symbol'),
    space: document.getElementById('req-space')
  };
  const listaRequisitos = document.getElementById('password-requisitos');

  function validatePasswords() {
    let ok = true;
    if (!pass1 || !pass2) return false;

    removeMessage(pass1);
    removeMessage(pass2);

    const p1 = pass1.value;
    const p2 = pass2.value;

    const lengthOk = p1.length >= 8;
    const upperOk = /[A-Z]/.test(p1);
    const lowerOk = /[a-z]/.test(p1);
    const numberOk = /[0-9]/.test(p1);
    const symbolOk = /[!@#$%^&*]/.test(p1);
    const spaceOk = !/\s/.test(p1);

    requisitos.length.className = lengthOk ? 'valid' : 'invalid';
    requisitos.uppercase.className = upperOk ? 'valid' : 'invalid';
    requisitos.lowercase.className = lowerOk ? 'valid' : 'invalid';
    requisitos.number.className = numberOk ? 'valid' : 'invalid';
    requisitos.symbol.className = symbolOk ? 'valid' : 'invalid';
    requisitos.space.className = spaceOk ? 'valid' : 'invalid';

    const allValid = lengthOk && upperOk && lowerOk && numberOk && symbolOk && spaceOk;
    listaRequisitos.classList.toggle('show', !allValid);

    if (!p1 || p1.trim() === "") {
      showMessage(pass1, "La contraseña es obligatoria.");
      ok = false;
    } else if (!allValid) {
      showMessage(pass1, "La contraseña no cumple todos los requisitos.");
      ok = false;
    }

    if (!p2 || p2.trim() === "") {
      showMessage(pass2, "Debes repetir la contraseña.");
      ok = false;
    } else if (p1 !== p2) {
      showMessage(pass2, "Las contraseñas no coinciden.");
      ok = false;
    }

    return ok;
  }

  pass1.addEventListener('input', validatePasswords);
  pass2.addEventListener('input', validatePasswords);


  // Mostrar/ocultar contraseña
function togglePasswordVisibility(inputId, toggleId) {
    const input = document.getElementById(inputId);
    const toggle = document.getElementById(toggleId);
    if (!input || !toggle) return;

    toggle.addEventListener('click', () => {
        if (input.type === "password") {
            input.type = "text";
            toggle.classList.replace('bx-show', 'bx-hide'); // cambia icono
        } else {
            input.type = "password";
            toggle.classList.replace('bx-hide', 'bx-show');
        }
    });
}

// Aplica a ambas contraseñas
togglePasswordVisibility("password1", "toggle-password1");
togglePasswordVisibility("password2", "toggle-password2");



  // ------------------ Envío del formulario ------------------
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const emailOk = await checkEmail();
    const passOk = validatePasswords();

    if (!emailOk || !passOk) {
      if (alertaError) {
        alertaError.classList.add('alertaError');
        setTimeout(() => alertaError.classList.remove('alertaError'), 3000);
      }
      return;
    }

    form.submit(); // Solo se envía si todo es válido
  });

  // ------------------ Enter Key ------------------
  form.addEventListener('keydown', async function(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      if (document.activeElement === emailInput) {
        pass1.focus();
        return;
      }
      const emailOk = await checkEmail();
      const passOk = validatePasswords();
      if (emailOk && passOk) form.submit();
      else if (alertaError) {
        alertaError.classList.add('alertaError');
        setTimeout(()=> alertaError.classList.remove('alertaError'), 3000);
      }
    }
  });

});



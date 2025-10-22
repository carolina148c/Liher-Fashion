document.addEventListener("DOMContentLoaded", function () {
  console.debug("validar_reset.js cargado");

  const form = document.getElementById("form-reset");
  if (!form) return;

  const emailInput = document.getElementById("reset-email");
  const alertaError = form.querySelector(".alerta-error");
  const alertaExito = form.querySelector(".alerta-exito");

  // ------------------ Mostrar / Ocultar errores ------------------
function showMessage(input, msg) {
  if (!input) return;
  removeMessage(input);

  const errorSpan = form.querySelector("#error-reset-email");
  if (errorSpan) {
    errorSpan.innerHTML = msg;  // <-- cambiar textContent por innerHTML
    errorSpan.style.display = "block";
  }

  input.classList.add("error");

  if (alertaError) alertaError.style.display = "block";
  if (alertaExito) alertaExito.style.display = "none";
}


  function removeMessage(input) {
    if (!input) return;

    const errorSpan = form.querySelector("#error-reset-email");
    if (errorSpan) {
      errorSpan.textContent = "";
      errorSpan.style.display = "none";
    }

    input.classList.remove("error");
    if (alertaError) alertaError.style.display = "none";
  }

  // ------------------ Validación de formato ------------------
  function validateEmailFormat(email) {
    if ((email.match(/@/g) || []).length > 1) return "No puede tener más de un '@'.";
    if (/^\./.test(email) || /\.$/.test(email)) return "No puede iniciar ni terminar con punto.";
    if (/\.@/.test(email) || /@\./.test(email)) return "No puede tener un punto junto al '@'.";
    if (/[<>,;]/.test(email)) return "Contiene caracteres no válidos.";

    const parts = email.split("@");
    if (parts.length === 2) {
      const domain = parts[1];
      if (/^-/.test(domain)) return "El dominio no puede iniciar con guion.";
      if (!/\.[A-Za-z]{2,}$/.test(domain)) return "Debe terminar en extensión válida (.com, .es, etc).";
    }

    const re =
      /^(?![.])(?!.*[.]{2})[A-Za-z0-9._%+\-]{1,64}(?<![.])@(?!-)[A-Za-z0-9\-]{1,63}(?<!-)(?:\.[A-Za-z]{2,})+$/;
    if (!re.test(email)) return "Formato de correo inválido.";

    return null;
  }

  // ------------------ Validación completa ------------------
  async function checkEmail() {
    if (!emailInput) return false;
    const raw = emailInput.value.trim();
    removeMessage(emailInput);

    if (!raw) {
      showMessage(emailInput, "El correo es obligatorio.");
      return false;
    }

    if (/\s/.test(raw)) {
      showMessage(emailInput, "No puede contener espacios.");
      return false;
    }

    if (raw.length > 320) {
      showMessage(emailInput, "Muy largo (máx. 320 caracteres).");
      return false;
    }

    const formatError = validateEmailFormat(raw);
    if (formatError) {
      showMessage(emailInput, formatError);
      return false;
    }

    // Validación AJAX en backend
    try {
      const resp = await fetch(`/ajax/validar-email/?email=${encodeURIComponent(raw)}`);
      if (resp.ok) {
        const data = await resp.json();
        if (!data.exists) {
          showMessage(emailInput, "No encontramos una cuenta con este correo. <a href='/registro/'>Regístrate aquí</a>");
          return false;
        } else {
          removeMessage(emailInput);
          if (alertaExito) alertaExito.style.display = "block";
          return true;
        }
      }
    } catch (err) {
      console.error("Error fetch existe-email:", err);
      return true; // no bloquea si falla la API
    }

    return true;
  }

  // ------------------ Eventos ------------------
  if (emailInput) {
    emailInput.addEventListener("input", async () => {
      await checkEmail();
    });

    emailInput.addEventListener("blur", async () => {
      emailInput.value = emailInput.value.trim();
      await checkEmail();
    });
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const emailOk = await checkEmail();
    if (emailOk) form.submit();
  });

  form.addEventListener("keydown", async function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const emailOk = await checkEmail();
      if (emailOk) form.submit();
    }
  });
});

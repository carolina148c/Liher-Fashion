document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById('form-login');
    if (!form) return;

    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');
    const toggleLoginPassword = document.getElementById("toggle-login-password");

    // ------------------ Validación correo ------------------
    function validateEmailFormat(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function validateEmail() {
        const email = emailInput.value.trim();
        const errorDiv = document.getElementById("error-login-email");
        errorDiv.textContent = "";

        if (!email) {
            errorDiv.textContent = "El correo es obligatorio.";
            return false;
        }
        if (!validateEmailFormat(email)) {
            errorDiv.textContent = "Formato de correo inválido.";
            return false;
        }
        return true;
    }

    // ------------------ Validación contraseña ------------------
    function validatePassword() {
        const password = passwordInput.value.trim();
        const errorDiv = document.getElementById("error-login-password");
        errorDiv.textContent = "";

        if (!password) {
            errorDiv.textContent = "La contraseña es obligatoria.";
            return false;
        }
        return true;
    }

    // ------------------ Eventos ------------------
    emailInput.addEventListener("blur", validateEmail);
    passwordInput.addEventListener("blur", validatePassword);

    form.addEventListener("submit", function (e) {
        if (!validateEmail() || !validatePassword()) {
            e.preventDefault(); // no envía el form si está incompleto
        }
    });

    // ------------------ Ojito mostrar/ocultar contraseña ------------------
    if (toggleLoginPassword && passwordInput) {
        toggleLoginPassword.addEventListener("click", () => {
            const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
            passwordInput.setAttribute("type", type);

            toggleLoginPassword.classList.toggle("bx-show");
            toggleLoginPassword.classList.toggle("bx-hide");
        });
    }
});

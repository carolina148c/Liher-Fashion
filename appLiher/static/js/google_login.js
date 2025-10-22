// Función para manejar la respuesta de Google
function handleCredentialResponse(response) {
    fetch("/google-login/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie('csrftoken')
        },
        body: JSON.stringify({ token: response.credential })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.href = "/paginaprincipal/"; // Redirige a página principal
        } else {
            alert("Error al iniciar sesión con Google");
        }
    })
    .catch(error => console.error("Error fetch Google login:", error));
}

// Función para obtener CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Inicializa solo el botón clásico de Google
window.onload = function () {
    google.accounts.id.initialize({
        client_id: '774700488191-s7qnbaao16ku9mjka78h858cqioqkf0p.apps.googleusercontent.com',
        callback: handleCredentialResponse
    });

    const loginBtn = document.getElementById("google-signin-button-login");
    if (loginBtn) {
        google.accounts.id.renderButton(loginBtn, {
            theme: "outline",
            size: "large",
            width: "240"
        });
    }

    const registerBtn = document.getElementById("google-signin-button-register");
    if (registerBtn) {
        google.accounts.id.renderButton(registerBtn, {
            theme: "filled_blue",
            size: "large",
            width: "240"
        });
    }

//    google.accounts.id.prompt();
};

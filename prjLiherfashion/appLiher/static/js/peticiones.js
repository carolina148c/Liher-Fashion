function viewPetition(id) {
    fetch(`/peticiones/${id}/detalle/`)
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;

            const p = data.data;

            document.getElementById('modal-details').style.display = 'flex';
            document.getElementById('modal-body').innerHTML = `
                <p><strong>ID:</strong> #PET-${p.id}</p>
                <p><strong>Producto:</strong> ${p.producto}</p>
                <p><strong>Usuario:</strong> ${p.usuario}</p>
                <p><strong>Email:</strong> ${p.email}</p>
                <p><strong>Cantidad:</strong> ${p.cantidad}</p>
                <p><strong>Fecha:</strong> ${p.fecha}</p>
                <p><strong>Estado:</strong> ${p.estado}</p>
            `;
        });
}

function approvePetition(id) {
    fetch(`/peticiones/${id}/aprobar/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrftoken }
    })
    .then(res => res.json())
    .then(() => location.reload());
}

function rejectPetition(id) {
    fetch(`/peticiones/${id}/rechazar/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrftoken }
    })
    .then(res => res.json())
    .then(() => location.reload());
}

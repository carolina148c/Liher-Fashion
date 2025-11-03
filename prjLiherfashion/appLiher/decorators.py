from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            # Si no es admin → lo mandamos a la tienda
            return redirect("pagina_principal")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permiso_requerido(nombre_permiso):
    def decorador(vista_funcion):
        @wraps(vista_funcion)
        def funcion_envuelta(request, *args, **kwargs):
            # Solo aplica a usuarios autenticados con objeto de permisos
            if hasattr(request.user, "permisos"):
                permisos = request.user.permisos
                if hasattr(permisos, nombre_permiso):
                    if not getattr(permisos, nombre_permiso):
                        messages.error(request, "No tienes permiso para acceder a esta sección.")
                        return redirect("panel_admin")
            # Si no tiene permisos definidos, también lo saca
            else:
                return redirect("panel_admin")

            return vista_funcion(request, *args, **kwargs)
        return funcion_envuelta
    return decorador

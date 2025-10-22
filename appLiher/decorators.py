from django.shortcuts import redirect

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            # Si no es admin → lo mandamos a la tienda
            return redirect("pagina_principal")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

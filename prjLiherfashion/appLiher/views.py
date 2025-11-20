# ==========================================================
#                   IMPORTS ESTÁNDAR
# ==========================================================
import json




# ==========================================================
#                   IMPORTS DJANGO
# ==========================================================
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout, views as auth_views
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F, Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal, InvalidOperation

# ==========================================================
#                   IMPORTACIONES LOCALES
# ==========================================================
from .decorators import admin_required, permiso_requerido
from .forms import (
    CustomPasswordResetForm, UsuarioRegistroForm, CategoriaForm, ColorForm, TallaForm
)
from .models import (
    Carrito, Producto, VarianteProducto,
    Categoria, Color, ItemCarrito, Permiso, PeticionProducto, Producto,VarianteProducto, Talla, Usuarios
)










# ==========================================================
#                   PÁGINA PRINCIPAL
# ==========================================================

def pagina_principal(request):
    return render(request, 'tienda/principal/pagina_principal.html')










# ==========================================================
#                   USUARIO / TIENDA
# ==========================================================

def carrito(request):
    """
    Vista para mostrar el contenido del carrito.
    """
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related('producto')
    subtotal = sum(item.total_precio for item in items_carrito) 
    contexto = {
        'carrito': carrito,
        'items_carrito': items_carrito,
        'subtotal': subtotal,
    }
    return render(request, 'tienda/carrito/carrito.html', contexto)



def obtener_o_crear_carrito(request):
    if request.user.is_authenticated:
        carrito, creado = Carrito.objects.get_or_create(usuario=request.user, completado=False)
        return carrito
    else:
        carrito_id = request.session.get('carrito_id')
        if carrito_id:
            try:
                carrito = Carrito.objects.get(id=carrito_id, completado=False)
                return carrito
            except Carrito.DoesNotExist:
                pass
        carrito = Carrito.objects.create()
        request.session['carrito_id'] = carrito.id
        return carrito



def envio(request):
    return render(request, 'tienda/carrito/datos_envio.html')



def pago(request):
    return render(request, 'tienda/carrito/pago.html')



def identificacion(request):
    return render(request, 'tienda/carrito/identificacion.html')



def vista_productos(request):
    productos = VarianteProducto.objects.select_related(
        'producto', 'talla', 'color'
    ).all().order_by('producto__categoria__categoria')

    categorias = Categoria.objects.all().order_by('categoria')
    colores = Color.objects.all().order_by('color')
    tallas = Talla.objects.all().order_by('talla')

    # Obtener filtros
    categoria_filtrar = request.GET.get('categoria', '').strip()
    color_filtrar = request.GET.get('color', '').strip()
    talla_filtrar = request.GET.get('talla', '').strip()

    # Aplicar filtros
    if categoria_filtrar:
        productos = productos.filter(producto__categoria__categoria=categoria_filtrar)

    if color_filtrar:
        productos = productos.filter(color__color=color_filtrar)

    if talla_filtrar:
        productos = productos.filter(talla__talla=talla_filtrar)

    context = {
        'productos': productos,
        'categorias': categorias,
        'colores': colores,
        'tallas': tallas,
        'selected_categoria': categoria_filtrar,
        'selected_color': color_filtrar,
        'selected_talla': talla_filtrar,
    }

    return render(request, 'tienda/principal/productos.html', context)










# ==========================================================
#                   LOGIN Y REGISTRO
# ==========================================================

@csrf_protect
def acceso(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user_obj = Usuarios.objects.get(email=email)
        except Usuarios.DoesNotExist:
            user_obj = None
        if user_obj is not None:
            if not user_obj.is_active:
                # Usuario existe pero no está activado → enviar correo automáticamente
                try:
                    uid = urlsafe_base64_encode(force_bytes(user_obj.pk))
                    token = default_token_generator.make_token(user_obj)
                    activar_url = request.build_absolute_uri(
                        reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token})
                    )
                    subject = 'Activa tu cuenta en Liher Fashion'
                    text_content = render_to_string(
                        'usuarios/autenticacion/activacion_email.txt',
                        {'user': user_obj, 'activar_url': activar_url}
                    )
                    html_content = render_to_string(
                        'usuarios/autenticacion/activacion_email.html',
                        {'user': user_obj, 'activar_url': activar_url}
                    )
                    email_obj = EmailMultiAlternatives(
                        subject, text_content, settings.DEFAULT_FROM_EMAIL, [user_obj.email]
                    )
                    email_obj.attach_alternative(html_content, "text/html")
                    email_obj.send()
                    messages.warning(request, "Tu cuenta no ha sido activada. Revisa tu correo. Se ha enviado un enlace de activación.")
                except Exception as e:
                    messages.error(request, "No se pudo enviar el correo de activación. Intenta reenviarlo manualmente.")
                return redirect('registro_revisar_email', email=email)
            # Usuario activo → verificamos contraseña
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)  # Inicia sesión
                # Redirección según rol
                if user.is_superuser or user.is_staff:
                    messages.success(request, f"Bienvenido administrador {user.email}")
                    return redirect("panel_admin")
                else:
                    messages.success(request, f"Bienvenido {user.email}")
                    return redirect("pagina_principal")
            else:
                messages.error(request, "Correo o contraseña incorrectos.")
                return render(request, "usuarios/autenticacion/acceso.html")
        else:
            messages.error(request, "Correo o contraseña incorrectos.")
            return render(request, "usuarios/autenticacion/acceso.html")
    return render(request, "usuarios/autenticacion/acceso.html")



@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('pagina_principal')



def login_ajax(request):
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Datos inválidos."})
    if not email or not password:
        return JsonResponse({"success": False, "message": "Correo y contraseña son obligatorios."})
    user = authenticate(request, email=email, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "message": "Correo o contraseña incorrectos."})



@csrf_exempt
@require_POST
def registro_ajax(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Datos inválidos."}, status=400)

    rol = data.get("rol")
    email = data.get("email", "").strip()
    password1 = data.get("password1", "")
    password2 = data.get("password2", "")
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    phone = data.get("phone", "").strip()
    permisos_seleccionados = data.get("permisos", [])

    form = UsuarioRegistroForm({
        "email": email,
        "password1": password1,
        "password2": password2,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "rol": rol,
    })

    if not form.is_valid():
        first_error = list(form.errors.values())[0][0] if form.errors else "Error en el registro."
        return JsonResponse({"success": False, "message": first_error}, status=400)

    user = form.save(commit=False)

    if rol == "usuario":
        user.is_staff = False
        user.is_superuser = False
    elif rol == "administrador":
        user.is_staff = True
        user.is_superuser = False
    else:
        return JsonResponse({"success": False, "message": "Rol inválido."}, status=400)

    user.is_active = False
    user.first_name = first_name
    user.last_name = last_name
    user.phone = phone
    user.save()

    # ✅ Guardar permisos solo si el rol es administrador
    if rol == "administrador":
        from .models import Permiso
        permisos, _ = Permiso.objects.get_or_create(usuario=user)
        campos_validos = [f.name for f in Permiso._meta.fields if f.name not in ["id", "usuario"]]
        for p in permisos_seleccionados:
            if p in campos_validos:
                setattr(permisos, p, True)
        permisos.save()


    # Generar enlace de activación
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activar_url = request.build_absolute_uri(
        reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token})
    )

    try:
        subject = 'Activa tu cuenta en Liher Fashion'
        text_content = render_to_string('usuarios/autenticacion/activacion_email.txt', {'user': user, 'activar_url': activar_url})
        html_content = render_to_string('usuarios/autenticacion/activacion_email.html', {'user': user, 'activar_url': activar_url})
        email_obj = EmailMultiAlternatives(subject, text_content, None, [user.email])
        email_obj.attach_alternative(html_content, "text/html")
        email_obj.send()
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return JsonResponse({"success": False, "message": "Error enviando correo de activación."}, status=500)

    usuarios_activos = Usuarios.objects.filter(is_active=True).count()
    usuarios_inactivos = Usuarios.objects.filter(is_active=False).count()
    redirect_url = request.build_absolute_uri(
        reverse('registro_revisar_email', kwargs={'email': user.email})
    ) + "?admin=true"

    return JsonResponse({
        "success": True,
        "message": "Registro exitoso. Revisa tu correo para activar la cuenta.",
        "redirect_url": redirect_url,
        "user": {
            "id": user.id,
            "email": user.email,
            "nombre": f"{user.first_name} {user.last_name}".strip(),
            "rol": "Administrador" if user.is_staff else "Usuario",
            "activo": user.is_active,
        },
        "stats": {
            "activos": usuarios_activos,
            "inactivos": usuarios_inactivos,
        }
    })










# ==========================================================
#                   REGISTRO Y ACTIVACIÓN
# ==========================================================

def registro_usuario(request):
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activar_url = request.build_absolute_uri(
                reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token})
            )
            subject = 'Activa tu cuenta en Liher Fashion'
            text_content = render_to_string('usuarios/autenticacion/activacion_email.txt', {'user': user, 'activar_url': activar_url})
            html_content = render_to_string('usuarios/autenticacion/activacion_email.html', {'user': user, 'activar_url': activar_url})
            email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            return render(request, 'usuarios/autenticacion/registro_revisar_email.html', {'email': user.email})
    else:
        form = UsuarioRegistroForm()
    return render(request, 'usuarios/autenticacion/acceso.html', {'form_registro': form})



def registro_revisar_email(request, email):
    try:
        user = Usuarios.objects.get(email=email)
        es_admin = user.is_staff
    except Usuarios.DoesNotExist:
        messages.error(request, "El usuario no existe.")
        return redirect('acceso')
    viene_de_admin = request.GET.get('admin', 'false').lower() == 'true'
    return render(request, 'usuarios/autenticacion/registro_revisar_email.html', {
        'email': email,
        'es_admin': es_admin,
        'resend_seconds': 30,
        'viene_de_admin': viene_de_admin,
    })





def reenviar_activacion(request, email):
    try:
        usuario = Usuarios.objects.get(email=email, is_active=False)  
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        activar_url = request.build_absolute_uri(reverse('activar_cuenta', kwargs={'uidb64': uid, 'token': token}))
        subject = 'Reenvío: Activa tu cuenta en Liher Fashion'
        text_content = render_to_string('usuarios/autenticacion/activacion_email.txt', {'user': usuario, 'activar_url': activar_url})
        html_content = render_to_string('usuarios/autenticacion/activacion_email.html', {'user': usuario, 'activar_url': activar_url})
        email_obj = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [usuario.email])
        email_obj.attach_alternative(html_content, "text/html")
        email_obj.send()
        messages.success(request, "El correo de activación ha sido reenviado.")
    except Usuarios.DoesNotExist:  
        messages.error(request, "No encontramos un usuario pendiente de activar con ese correo.")
    return redirect('registro_revisar_email', email=email)


def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuarios.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuarios.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Bienvenido, {user.first_name or user.email}!')
        if user.is_staff:
            return redirect('panel_admin')  # admin → panel-admin/
        else:
            return redirect('pagina_principal')  # usuario → home normal
    else:
        return render(request, 'usuarios/autenticacion/activacion_invalida.html')



def validar_email_ajax(request):
    email = request.GET.get('email', '').strip()
    exists = Usuarios.objects.filter(email__iexact=email).exists()
    return JsonResponse({'exists': exists})









# ==========================================================
#                   CONTRASEÑA
# ==========================================================

class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = "usuarios/contrasena/restablecer_contrasena.html"
    email_template_name = "usuarios/contrasena/correo_reset.html"
    subject_template_name = "usuarios/contrasena/asunto_reset.txt"
    success_url = reverse_lazy("correo_enviado")
    form_class = CustomPasswordResetForm 
    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        user = Usuarios.objects.get(email=email)
        enviar_correo_reset(user, self.request)
        self.request.session["reset_email"] = email
        return redirect(self.success_url)



def enviar_correo_reset(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = request.build_absolute_uri(
        reverse('nueva_contrasena', kwargs={'uidb64': uid, 'token': token})
    )

    subject = "Restablece tu contraseña en Liher Fashion"
    text_content = f"Hola {user.email}, usa este enlace para restablecer tu contraseña: {reset_url}"
    html_content = render_to_string(
        "usuarios/contrasena/correo_reset.html",
        {"user": user, "reset_url": reset_url}
    )
    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.attach_alternative(html_content, "text/html")
    email.send()



class CorreoEnviadoView(auth_views.PasswordResetDoneView):
    template_name = "usuarios/contrasena/correo_enviado.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get("reset_email")
        context["resend_seconds"] = 360
        return context



def reenviar_reset(request):
    email = request.session.get("reset_email")
    if not email:
        messages.warning(
            request,
            "Tu sesión ha expirado. Ingresa nuevamente tu correo para reenviar el enlace."
        )
        return redirect("restablecer_contrasena")
    form = PasswordResetForm(request.POST)
    if form.is_valid():
        form.save(
            request=request,
            email_template_name="usuarios/contrasena/correo_reset.html",
            subject_template_name="usuarios/contrasena/asunto_reset.txt",
            use_https=request.is_secure(),
    )
        messages.success(request, "El correo de restablecimiento se ha reenviado exitosamente.")
    else:
        messages.error(request, "No se pudo reenviar el correo. Verifica la dirección.")
    return redirect("correo_enviado")



class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "usuarios/contrasena/nueva_contrasena.html"
    success_url = reverse_lazy("contrasena_actualizada")
    def form_valid(self, form):
        user = form.user  # el usuario al que se le está cambiando la contraseña
        new_password = form.cleaned_data.get("new_password1")
        # Validar contraseña
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            form.add_error('new_password1', e)
            return self.form_invalid(form)
        if user.check_password(new_password):
            form.add_error('new_password1', "La nueva contraseña no puede ser igual a la anterior.")
            return self.form_invalid(form)
        # Activar usuario si estaba inactivo
        if not user.is_active:
            user.is_active = True
            user.save()
        return super().form_valid(form)


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "usuarios/contrasena/contrasena_actualizada.html"









# ==========================================================
#                   CARRITO
# ==========================================================

@require_POST
def anadir_al_carrito(request, producto_id):
    try:
        variante = get_object_or_404(VarianteProducto, pk=producto_id)

        import json
        try:
            data = json.loads(request.body)
            cantidad = int(data.get('cantidad', 1))
        except (json.JSONDecodeError, ValueError):
            cantidad = 1

        if cantidad <= 0:
            return JsonResponse({'success': False, 'message': 'Cantidad inválida.'})

        if cantidad > variante.stock:
            return JsonResponse({'success': False, 'message': f'Solo hay {variante.stock} unidades.'})

        carrito = obtener_o_crear_carrito(request)

        item_existente = ItemCarrito.objects.filter(
            carrito=carrito,
            producto=variante
        ).first()

        if item_existente:
            item_existente.cantidad += cantidad
            item_existente.save()
            mensaje = f'Se añadieron {cantidad} unidades más de "{variante.producto.nombre}".'
        else:
            ItemCarrito.objects.create(
                carrito=carrito,
                producto=variante,
                cantidad=cantidad,
                precio_unitario=variante.producto.precio,
            )
            mensaje = f'El producto "{variante.producto.nombre}" se añadió al carrito.'

        return JsonResponse({
            'success': True,
            'message': mensaje,
            'total_items': carrito.total_items_carrito
        })

    except VarianteProducto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Variante no existente.'}, status=404)


    

@require_POST
def actualizar_carrito(request, item_id):
    """
    Actualiza la cantidad de un producto en el carrito y devuelve JSON.
    """
    try:
        item = get_object_or_404(ItemCarrito, pk=item_id)
        nueva_cantidad = int(request.POST.get('cantidad', 0))
        if nueva_cantidad > 0:
            item.cantidad = nueva_cantidad
            item.save()
            mensaje = 'La cantidad del producto ha sido actualizada.'
            success = True
        else:
            item.delete()
            mensaje = 'El producto ha sido eliminado del carrito.'
            success = True
        carrito = obtener_o_crear_carrito(request)
        total_items_carrito = carrito.total_items_carrito
        total_precio_carrito = carrito.total_precio_carrito
        return JsonResponse({
            'success': success,
            'message': mensaje,
            'total_items': total_items_carrito,
            'total_precio': total_precio_carrito,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ocurrió un error: {str(e)}'}, status=500)



@require_POST
def eliminar_del_carrito(request, item_id):
    """
    Elimina un producto del carrito y devuelve JSON.
    """
    try:
        item = get_object_or_404(ItemCarrito, pk=item_id)
        item.delete()
        mensaje = 'El producto ha sido eliminado del carrito.'
        carrito = obtener_o_crear_carrito(request)
        total_items_carrito = carrito.total_items_carrito
        total_precio_carrito = carrito.total_precio_carrito
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'total_items': total_items_carrito,
            'total_precio': total_precio_carrito,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ocurrió un error: {str(e)}'}, status=500)
    








# ==========================================================
#                   ADMIN
# ==========================================================

@login_required
@admin_required
def panel_admin(request):
    permisos = {"vista_usuario": True}  # Siempre visible
    if hasattr(request.user, 'permisos'):
        permisos.update({
            "inicio": request.user.permisos.inicio,
            "inventario": request.user.permisos.inventario,
            "pedidos": request.user.permisos.pedidos,
            "usuarios": request.user.permisos.usuarios,
            "devoluciones": request.user.permisos.devoluciones,
            "peticiones": request.user.permisos.peticiones,
        })

    return render(request, "admin/panel_admin.html", {
        "permisos_json": json.dumps(permisos)
    })









# ==========================================================
#                   INVENTARIO
# ==========================================================

def configuracion_inventario(request):
    return render(request, 'admin/inventario/configuracion_inventario.html')



def agregar_categoria(request):
    form = CategoriaForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('agregar_categoria')

    elementos = Categoria.objects.all()
    return render(request, 'admin/inventario/agregar_form.html', {
        'form': form,
        'titulo': 'Agregar Categoría',
        'elementos': elementos,
        'editar_url_name': 'editar_categoria',
        'eliminar_url_name': 'eliminar_categoria'
    })



def editar_categoria(request, pk):
    categoria = Categoria.objects.get(pk=pk)
    form = CategoriaForm(request.POST or None, instance=categoria)
    if form.is_valid():
        form.save()
        return redirect('agregar_categoria')
    return render(request, 'admin/inventario/agregar_form.html', {
        'form': form,
        'titulo': 'Editar Categoría',
        'elementos': Categoria.objects.all(),
        'editar_url_name': 'editar_categoria',
        'eliminar_url_name': 'eliminar_categoria'
    })


def eliminar_categoria(request, pk):
    categoria = Categoria.objects.get(pk=pk)
    categoria.delete()
    return redirect('agregar_categoria')



def agregar_color(request):
    form = ColorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('agregar_color')

    elementos = Color.objects.all()
    return render(request, 'admin/inventario/agregar_form.html', {
        'form': form,
        'titulo': 'Agregar Color',
        'elementos': elementos,
        'editar_url_name': 'editar_color',
        'eliminar_url_name': 'eliminar_color'
    })



def editar_color(request, pk):
    color = Color.objects.get(pk=pk)
    form = ColorForm(request.POST or None, instance=color)
    if form.is_valid():
        form.save()
        return redirect('agregar_color')
    return render(request, 'admin/inventario/agregar_form.html', {
        'form': form,
        'titulo': 'Editar Color',
        'elementos': Color.objects.all(),
        'editar_url_name': 'editar_color',
        'eliminar_url_name': 'eliminar_color'
    })



def eliminar_color(request, pk):
    color = Color.objects.get(pk=pk)
    color.delete()
    return redirect('agregar_color')



def agregar_talla(request):
    form = TallaForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('agregar_talla')

    elementos = Talla.objects.all()
    return render(request, 'admin/inventario/agregar_form.html', {
        'form': form,
        'titulo': 'Agregar Talla',
        'elementos': elementos,
        'editar_url_name': 'editar_talla',
        'eliminar_url_name': 'eliminar_talla'
    })



def editar_talla(request, pk):
    talla = Talla.objects.get(pk=pk)
    form = TallaForm(request.POST or None, instance=talla)
    if form.is_valid():
        form.save()
        return redirect('agregar_talla')
    return render(request, 'admin/inventario/agregar_form.html', {
        'form': form,
        'titulo': 'Editar Talla',
        'elementos': Talla.objects.all(),
        'editar_url_name': 'editar_talla',
        'eliminar_url_name': 'eliminar_talla'
    })



def eliminar_talla(request, pk):
    talla = Talla.objects.get(pk=pk)
    talla.delete()
    return redirect('agregar_talla')




@login_required
@permiso_requerido('inventario')
def listar_productos_inventario(request):
    productos = Producto.objects.annotate(
        n_variantes=Count('variantes', distinct=True),
        total_stock=Sum('variantes__stock')
    ).order_by('nombre')

    total_productos = productos.count()
    total_variantes = VarianteProducto.objects.count()
    productos_activos = productos.filter(total_stock__gt=0).count()
    productos_inactivos = total_productos - productos_activos

    context = {
        'productos': productos,
        'total_productos': total_productos,
        'total_variantes': total_variantes,
        'productos_activos': productos_activos,
        'productos_inactivos': productos_inactivos,
        'active': 'inventario',
    }

    return render(request, 'admin/inventario/vista_inventario.html', context)




@login_required
def agregar_producto(request):
    categorias = Categoria.objects.all()
    tallas = Talla.objects.all()
    colores = Color.objects.all()
    
    context = {
        "categorias": categorias,
        "tallas": tallas,
        "colores": colores,
    }

    if request.method == 'POST':
        # CAMPOS GENERALES
        nombre = request.POST.get('nombre', '').strip()
        referencia = request.POST.get('referencia', '').strip()
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '')
        estado = request.POST.get('estado', 'Activo')
        precio_str = request.POST.get('precio', '0')
        imagen = request.FILES.get('imagen')

        # Mantener los datos en el contexto para rellenar el formulario
        context.update({
            "nombre": nombre,
            "referencia": referencia,
            "categoria_id": categoria_id,
            "descripcion": descripcion,
            "precio": precio_str,
        })

        # VALIDAR NOMBRE
        if not nombre:
            messages.error(request, "El nombre del producto es obligatorio.")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # VALIDAR VARIANTES
        if "variantes[0][talla]" not in request.POST:
            messages.error(request, "Debe agregar mínimo una variante antes de guardar.")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Buscar categoría
        try:
            categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            messages.error(request, "La categoría seleccionada no existe.")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Procesar precio
        try:
            # Remover puntos y convertir a decimal
            precio_limpio = precio_str.replace('.', '')
            precio_decimal = Decimal(precio_limpio) if precio_limpio else Decimal('0.00')
        except (ValueError, TypeError, InvalidOperation) as e:
            messages.error(request, f"El precio debe ser un número válido. Error: {str(e)}")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Crear producto
        try:
            producto = Producto.objects.create(
                nombre=nombre,
                referencia=referencia,
                categoria=categoria,
                descripcion=descripcion,
                imagen=imagen,
                estado=estado,
                precio=precio_decimal
            )
        except Exception as e:
            messages.error(request, f"Error al crear el producto: {str(e)}")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Guardar variantes dinámicas
        index = 0
        variantes_guardadas = 0
        while True:
            talla_id = request.POST.get(f"variantes[{index}][talla]")
            color_id = request.POST.get(f"variantes[{index}][color]")
            stock = request.POST.get(f"variantes[{index}][stock]")
            
            if talla_id is None:
                break
                
            try:
                talla_obj = Talla.objects.get(pk=talla_id)
                color_obj = Color.objects.get(pk=color_id)
                
                VarianteProducto.objects.create(
                    producto=producto,
                    talla=talla_obj,
                    color=color_obj,
                    stock=int(stock) if stock else 0,
                )
                variantes_guardadas += 1
            except (Talla.DoesNotExist, Color.DoesNotExist, ValueError) as e:
                messages.warning(request, f"Error al guardar variante {index+1}: {str(e)}")
            
            index += 1

        if variantes_guardadas > 0:
            messages.success(request, f"Producto agregado correctamente con {variantes_guardadas} variante(s).")
            return redirect('listar_productos_inventario')
        else:
            messages.error(request, "No se pudieron guardar las variantes del producto.")
            producto.delete()  # Eliminar el producto si no hay variantes

    return render(request, 'admin/inventario/agregar_producto.html', context)



@login_required
def editar_producto(request, idproducto):
    producto = get_object_or_404(Producto, idproducto=idproducto)
    variantes = VarianteProducto.objects.filter(producto=producto)

    context = {
        "producto": producto,
        "categorias": Categoria.objects.all(),
        "tallas": Talla.objects.all(),
        "colores": Color.objects.all(),
        "variantes": variantes
    }

    if request.method == 'POST':
        # Obtener los datos del formulario
        producto.nombre = request.POST.get("nombre", "").strip()
        producto.referencia = request.POST.get("referencia", "").strip()
        
        # CORRECCIÓN: Obtener la categoría por ID
        categoria_id = request.POST.get("categoria")
        try:
            if categoria_id:
                producto.categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            messages.error(request, "La categoría seleccionada no existe.")
            return render(request, "admin/inventario/editar_producto.html", context)
        
        # MEJORA: Manejo del precio con formato de puntos
        precio_str = request.POST.get("precio", "0").strip()
        try:
            # Remover puntos y convertir a decimal
            precio_limpio = precio_str.replace('.', '')
            producto.precio = Decimal(precio_limpio) if precio_limpio else Decimal('0.00')
        except (ValueError, TypeError, InvalidOperation) as e:
            messages.error(request, f"El precio debe ser un número válido. Error: {str(e)}")
            return render(request, "admin/inventario/editar_producto.html", context)
        
        producto.descripcion = request.POST.get("descripcion", "")
        producto.estado = request.POST.get("estado", "Activo")

        # Manejar la imagen
        imagen = request.FILES.get("imagen")
        if imagen:
            # Validar que sea una imagen
            if not imagen.content_type.startswith('image/'):
                messages.error(request, "El archivo debe ser una imagen válida.")
                return render(request, "admin/inventario/editar_producto.html", context)
            
            # Validar tamaño (opcional, máximo 5MB)
            if imagen.size > 5 * 1024 * 1024:
                messages.error(request, "La imagen no debe superar los 5MB.")
                return render(request, "admin/inventario/editar_producto.html", context)
            
            producto.imagen = imagen

        try:
            producto.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("editar_producto", idproducto=idproducto)
        except Exception as e:
            messages.error(request, f"Error al actualizar el producto: {str(e)}")
            return render(request, "admin/inventario/editar_producto.html", context)

    return render(request, "admin/inventario/editar_producto.html", context)




@login_required
def guardar_variantes(request, idproducto):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")

    producto = get_object_or_404(Producto, idproducto=idproducto)

    talla = request.POST.get("talla")
    colores = request.POST.getlist("colores[]")
    stocks = request.POST.getlist("stocks[]")

    imagenes = request.FILES.getlist("imagenes[]")

    if not talla:
        return JsonResponse({"error": "Debes seleccionar una talla"}, status=400)

    if not colores:
        return JsonResponse({"error": "Debes seleccionar al menos un color"}, status=400)

    for i, color in enumerate(colores):
        talla_obj = Talla.objects.get(talla=talla)
        color_obj = Color.objects.get(color=color)

        VarianteProducto.objects.create(
            producto=producto,
            talla=talla_obj,
            color=color_obj,
            stock=int(stocks[i]),
            imagen=imagenes[i] if i < len(imagenes) else None
        )

    return JsonResponse({"success": True, "message": "Variantes guardadas correctamente"})









# ==========================================================
#                   PEDIDOS
# ==========================================================

def pedidos(request):
    pedidos = []
    return render(request, 'admin/pedidos/pedidos.html', {'pedidos': pedidos, 'active': 'pedidos'})










# ==========================================================
#                   USUARIOS
# ==========================================================

@staff_member_required
def mostrar_usuarios(request):
    usuarios = Usuarios.objects.all().select_related('permisos')
    usuarios_activos = usuarios.filter(is_active=True).count()
    usuarios_inactivos = usuarios.filter(is_active=False).count()

    return render(request, 'admin/usuarios/mostrar_usuarios.html', {
        'usuarios': usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_inactivos': usuarios_inactivos,
        'active': 'usuarios'
    })



@csrf_exempt
@login_required
@staff_member_required
def editar_usuario(request, id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)
    try:
        usuario = get_object_or_404(Usuarios, id=id)
        def to_bool(value):
            return str(value).lower() in ["true", "1", "on"]
        is_admin = to_bool(request.POST.get("is_admin"))
        is_active = to_bool(request.POST.get("is_active"))
        usuario.is_active = is_active
        if is_admin:
            usuario.first_name = request.POST.get("first_name", usuario.first_name).strip()
            usuario.last_name = request.POST.get("last_name", usuario.last_name).strip()
            usuario.phone = request.POST.get("phone", usuario.phone).strip()
            permisos_json = request.POST.get("permisos")
            if permisos_json:
                import json
                permisos = json.loads(permisos_json)
                permisos_usuario, _ = Permiso.objects.get_or_create(usuario=usuario)
                mapa_permisos = {
                    "inicio": "inicio",
                    "inventario": "inventario",
                    "pedidos": "pedidos",
                    "usuarios": "usuarios",
                    "devoluciones": "devoluciones",
                    "peticiones": "peticiones",
                }
                for p in permisos:
                    nombre_raw = p.get("nombre", "").strip().lower()
                    activo = p.get("activo", False)
                    campo = mapa_permisos.get(nombre_raw)
                    if campo and hasattr(permisos_usuario, campo):
                        setattr(permisos_usuario, campo, activo)

                permisos_usuario.save()
        usuario.save()
        return JsonResponse({
            "success": True,
            "message": "Usuario actualizado correctamente."
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error al actualizar usuario: {str(e)}"
        }, status=400)




@login_required
def ver_usuario(request, user_id):
    usuario = get_object_or_404(Usuarios, id=user_id)
    first_initial = usuario.first_name[0] if usuario.first_name else "?"
    last_initial = usuario.last_name[0] if usuario.last_name else "?"
    last_login = usuario.last_login.strftime('%d/%m/%Y %H:%M') if usuario.last_login else "Nunca"
    permisos_data = []
    if hasattr(usuario, 'permisos'):
        permisos = usuario.permisos
        permisos_dict = {
            "Inicio": permisos.inicio,
            "Inventario": permisos.inventario,
            "Pedidos": permisos.pedidos,
            "Usuarios": permisos.usuarios,
            "Devoluciones": permisos.devoluciones,
            "Peticiones": permisos.peticiones,
        }
        permisos_data = [{"nombre": k, "activo": v} for k, v in permisos_dict.items()]
    data = {
        "full_name": f"{usuario.first_name} {usuario.last_name}".strip() or "Sin nombre",
        "initials": f"{first_initial}{last_initial}".upper(),
        "email": usuario.email or "-",
        "phone": getattr(usuario, 'phone', '-') if request.user.is_staff else None,
        "role": "Administrador" if usuario.is_staff else "Usuario",
        "status": "Activo" if usuario.is_active else "Inactivo",
        "date_joined": usuario.date_joined.strftime('%d/%m/%Y'),
        "last_login": last_login,
        "permissions": permisos_data,
    }

    return JsonResponse(data)



@csrf_exempt
@require_POST
@login_required
def toggle_usuario_activo(request, id):
    usuario = get_object_or_404(Usuarios, id=id)
    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=["is_active"])

    return JsonResponse({
        "success": True,
        "nuevo_estado": usuario.is_active,
        "mensaje": f"Usuario {'activado' if usuario.is_active else 'desactivado'} correctamente."
    })



@login_required
@staff_member_required
def obtener_usuario(request, id):
    usuario = get_object_or_404(Usuarios, id=id)
    return JsonResponse({
        "id": usuario.id,
        "first_name": usuario.first_name or "",
        "last_name": usuario.last_name or "",
        "email": usuario.email or "",
        "phone": usuario.phone or "",
        "is_staff": usuario.is_staff,
        "is_active": usuario.is_active,
        "last_login": usuario.last_login.strftime("%d/%m/%Y %H:%M") if usuario.last_login else "Nunca",
        "date_joined": usuario.date_joined.strftime("%d/%m/%Y %H:%M"),
    })









# ==========================================================
#                   DEVOLUCIONES
# ==========================================================

@permiso_requerido('devoluciones')
def devoluciones(request):
    return render(request, 'admin/devoluciones/devoluciones.html', {
        'active': 'devoluciones'
    })










# ==========================================================
#                   PETICIONES
# ==========================================================

def peticiones(request):
    return render(request, 'admin/peticiones/peticiones.html', {
        'active': 'peticiones'
    })



@login_required
@admin_required
@permiso_requerido('peticiones')
def listar_peticiones(request):
    peticiones = PeticionProducto.objects.select_related(
        'usuario', 'producto'
    ).order_by('-fecha_peticion')

    # Contadores
    stats = {
        'pendientes': peticiones.filter(atendida=False).count(),
        'revision': peticiones.filter(atendida=False).count(),  
        'aceptadas': peticiones.filter(atendida=True).count(),
        'rechazadas': peticiones.filter(atendida=False).count(),  
        'total': peticiones.count(),
    }

    return render(request, 'admin/peticiones/peticiones.html', {
        'active': 'peticiones',
        'peticiones': peticiones,
        'stats': stats
    })



@login_required
@require_POST
def crear_peticion(request, producto_id):
    try:
        variante = VarianteProducto.objects.get(pk=producto_id)
    except VarianteProducto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Variante no existe.'}, status=404)

    import json
    try:
        data = json.loads(request.body)
        cantidad = int(data.get('cantidad', 1))
    except:
        cantidad = 1

    if cantidad <= 0:
        return JsonResponse({'success': False, 'message': 'Cantidad inválida.'})

    peticion = PeticionProducto.objects.create(
        usuario=request.user,
        producto=variante,
        cantidad_solicitada=cantidad
    )

    return JsonResponse({
        'success': True,
        'message': f'Petición creada para {variante.producto.nombre}, cantidad {cantidad}.'
    })




@login_required
@require_POST
def aprobar_peticion(request, id):
    try:
        peticion = PeticionProducto.objects.get(id=id)
        peticion.atendida = True
        peticion.save()
        return JsonResponse({'success': True})
    except PeticionProducto.DoesNotExist:
        return JsonResponse({'success': False}, status=404)



@login_required
@require_POST
def rechazar_peticion(request, id):
    try:
        peticion = PeticionProducto.objects.get(id=id)
        peticion.delete()  # o marcar campo "rechazada"
        return JsonResponse({'success': True})
    except PeticionProducto.DoesNotExist:
        return JsonResponse({'success': False}, status=404)



def detalle_peticion(request, id):
    try:
        p = PeticionProducto.objects.select_related('usuario', 'producto').get(pk=id)
        data = {
            'id': p.id,
            'producto': p.producto.inventario.nombre,
            'usuario': f"{p.usuario.nombre} {p.usuario.apellido}",
            'email': p.usuario.email,
            'cantidad': p.cantidad_solicitada,
            'fecha': p.fecha_peticion.strftime("%d/%m/%Y"),
            'estado': "Aceptada" if p.atendida else "Pendiente"
        }
        return JsonResponse({'success': True, 'data': data})
    except PeticionProducto.DoesNotExist:
        return JsonResponse({'success': False}, status=404)

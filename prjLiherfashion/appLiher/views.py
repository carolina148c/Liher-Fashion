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
from django.http import JsonResponse
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


# ==========================================================
#                   IMPORTS LOCALES
# ==========================================================
from .decorators import admin_required, permiso_requerido
from .forms import (
    CustomPasswordResetForm, InventarioForm, UsuarioRegistroForm,
    UsuarioUpdateForm
)
from .models import (
    Carrito, Catalogo, EntradaInventario, Inventario,
    Categoria, Color, ItemCarrito, PeticionProducto, Talla, Usuarios
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
    productos = Inventario.objects.select_related('categoria', 'color', 'talla').all().order_by('categoria__categoria')
    categorias = Categoria.objects.all().order_by('categoria')
    colores = Color.objects.all().order_by('color')
    tallas = Talla.objects.all().order_by('talla')
    # Obtener filtros
    categoria_filtrar = request.GET.get('categoria', '').strip()
    color_filtrar = request.GET.get('color', '').strip()
    talla_filtrar = request.GET.get('talla', '').strip()
    # Aplicar filtros
    if categoria_filtrar:
        productos = productos.filter(categoria__categoria=categoria_filtrar)
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
    )

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

    return render(request, 'usuarios/autenticacion/registro_revisar_email.html', {
        'email': email,
        'es_admin': es_admin,
        'resend_seconds': 30, 
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
        # Obtener el producto del inventario
        producto = get_object_or_404(Inventario, pk=producto_id)
        # Leer la cantidad enviada desde el frontend
        import json
        try:
            data = json.loads(request.body)
            cantidad = int(data.get('cantidad', 1))
        except (json.JSONDecodeError, ValueError):
            cantidad = 1
        if cantidad <= 0:
            return JsonResponse({'success': False, 'message': 'La cantidad debe ser un número positivo.'})
        if cantidad > producto.stock:
            return JsonResponse({'success': False, 'message': f'Solo hay {producto.stock} unidades disponibles en stock.'})
        # Obtener o crear carrito
        carrito = obtener_o_crear_carrito(request)
        # Verificar si el producto ya existe en el carrito
        item_existente = ItemCarrito.objects.filter(carrito=carrito, producto=producto).first()
        if item_existente:
            item_existente.cantidad += cantidad
            item_existente.save()
            mensaje = f'Se han añadido {cantidad} unidades más de "{producto.catalogo.nombre}" al carrito.'
        else:
            ItemCarrito.objects.create(
                carrito=carrito,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )
            mensaje = f'El producto "{producto.catalogo.nombre}" se ha añadido al carrito.'
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'total_items': carrito.total_items_carrito
        })
    except Inventario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'El producto no existe o está agotado.'}, status=404)
    except Exception as e:
        print(f"Error al añadir al carrito: {e}")
        return JsonResponse({'success': False, 'message': f'Ocurrió un error interno: {str(e)}'}, status=500)

    

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
            "catalogo": request.user.permisos.catalogo,
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

@login_required
@permiso_requerido('inventario')
def listar_productos_tabla(request):
    productos = Inventario.objects.select_related('categoria', 'color', 'talla', 'catalogo').all().order_by('catalogo__nombre')
    total_productos = productos.count()
    valor_inventario = productos.aggregate(total=Sum(F('precio') * F('stock')))['total'] or 0
    productos_stock_bajo = productos.filter(stock__lt=10).count()
    productos_agotados = productos.filter(stock=0).count()
    stock_total_unidades = productos.aggregate(Sum('stock'))['stock__sum'] or 0
    context = {
        'productos': productos,
        'total_productos': total_productos,
        'valor_inventario': valor_inventario,
        'productos_stock_bajo': productos_stock_bajo,
        'productos_agotados': productos_agotados,
        'stock_total_unidades': stock_total_unidades,
        'active': 'inventario',
    }
    return render(request, 'admin/inventario/vista_inventario.html', context)



@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST, request.FILES)  #
        if form.is_valid():
            form.save()
            messages.success(request, "Producto añadido exitosamente al inventario.")
            return redirect('listar_productos_tabla')
        else:
            messages.error(request, "Error al añadir el producto. Por favor, verifica los datos.")
            return render(request, 'admin/inventario/crear_producto.html', {'form': form})
    else:
        form = InventarioForm()
    return render(request, 'admin/inventario/crear_producto.html', {'form': form})



@login_required
def editar_producto(request, id):
    producto = get_object_or_404(Inventario, idinventario=id)
    
    if request.method == 'POST':
        form = InventarioForm(request.POST, request.FILES, instance=producto)
        # Ocultamos stock antes de validar
        form.fields.pop('stock', None)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado exitosamente.")
            return redirect('listar_productos_tabla')
        else:
            messages.error(request, "Error al actualizar el producto. Por favor, verifica los datos.")
    else:
        form = InventarioForm(instance=producto)
        form.fields.pop('stock', None)

    return render(request, 'admin/inventario/editar_producto.html', {'form': form, 'producto': producto})



@login_required
def eliminar_producto(request, id):
    producto = get_object_or_404(Inventario, idinventario=id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, "Producto eliminado exitosamente.")
        return redirect('listar_productos_tabla')
    else:
        return render(request, 'admin/inventario/eliminar_producto.html', {'producto': producto})
    

def mostrar_formulario_stock(request, id_catalogo):
    # Obtener el producto principal del catálogo
    producto_principal = get_object_or_404(Catalogo, idcatalogo=id_catalogo)
    # Obtener todas las variantes (Inventario) relacionadas a este producto
    variantes = Inventario.objects.filter(catalogo=producto_principal).order_by('color', 'talla')
    if not variantes.exists():
        messages.error(request, f"El producto '{producto_principal.nombre}' no tiene variantes de inventario.")
        return redirect('listar_productos_catalogo')
    context = {
        'producto': producto_principal,
        'variantes': variantes,
    }
    return render(request, 'admin/catalogo/formulario_stock.html', context)



def procesar_entrada_stock(request):
    if request.method == 'POST':
        try:
            id_variante = request.POST.get('id_variante') 
            cantidad = int(request.POST.get('cantidad_ingreso'))
        except (ValueError, TypeError):
            messages.error(request, "Error: La cantidad de ingreso debe ser un número entero.")
            return redirect('listar_productos_catalogo')
        if cantidad <= 0:
            messages.error(request, "Error: La cantidad debe ser mayor que cero.")
            return redirect('listar_productos_catalogo')
        variante_a_surtir = get_object_or_404(Inventario, idinventario=id_variante)
        try:
            with transaction.atomic():
                EntradaInventario.objects.create(
                    idinventario_fk=variante_a_surtir,
                    cantidad_ingreso=cantidad,
                )
            messages.success(request, f"¡Entrada registrada! Se añadieron {cantidad} unidades a la variante {variante_a_surtir.color}/{variante_a_surtir.talla}. (Verifique el stock, el Trigger debe haberlo actualizado).")
            return redirect('listar_movimientos_producto', id_catalogo=variante_a_surtir.producto.idcatalogo)
        except Exception as e:
            messages.error(request, f"Error al procesar la entrada: {e}")
            return redirect('listar_productos_catalogo')
    return redirect('listar_productos_catalogo')









# ==========================================================
#                   CATÁLOGO
# ==========================================================

@login_required
@permiso_requerido('catalogo')
def listar_productos_catalogo(request):
    productos = Catalogo.objects.annotate(
        n_variantes=Count('inventarios', distinct=True),
        total_stock=Sum('inventarios__stock')
    ).order_by('nombre')

    total_productos = productos.count()
    total_variantes = Inventario.objects.count()
    productos_activos = productos.filter(total_stock__gt=0).count()
    productos_inactivos = total_productos - productos_activos

    context = {
        'productos': productos,
        'total_productos': total_productos,
        'total_variantes': total_variantes,
        'productos_activos': productos_activos,
        'productos_inactivos': productos_inactivos,
        'active': 'catalogo', 
    }
    return render(request, 'admin/catalogo/vista_catalogo.html', context)



@login_required
def agregar_producto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        # Validación: nombre obligatorio
        if not nombre:
            messages.error(request, "Error: El nombre del catálogo es obligatorio.")
            return render(request, 'admin/catalogo/formulario_catalogo.html', {
                'nombre': nombre,
                'descripcion': descripcion
            })
        try:
            nuevo_catalogo = Catalogo.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            messages.success(request, f"Catálogo '{nuevo_catalogo.nombre}' agregado con éxito.")
            return redirect('listar_productos_catalogo')
        except Exception as e:
            messages.error(request, f"Error al guardar el catálogo: {e}")
            return render(request, 'admin/catalogo/formulario_catalogo.html', {
                'nombre': nombre,
                'descripcion': descripcion
            })
    return render(request, 'admin/catalogo/formulario_catalogo.html', {})



@login_required
def listar_movimientos_producto(request, id_catalogo):
    producto_principal = get_object_or_404(Catalogo, idcatalogo=id_catalogo)
    ids_variantes = Inventario.objects.filter(catalogo=producto_principal).values_list('idinventario', flat=True)
    movimientos = EntradaInventario.objects.filter(
        idinventario_fk__in=ids_variantes
    ).select_related('idinventario_fk').order_by('-fecha_entrada')
    context = {
        'producto_principal': producto_principal,
        'movimientos': movimientos,
        'total_movimientos': movimientos.count()
    }
    return render(request, 'admin/catalogo/vista_movimientos.html', context)









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



@login_required
@staff_member_required
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuarios, id=id)
    if request.method == 'POST':
        try:
            if usuario.is_staff:
                campos_editables = ['first_name', 'last_name', 'email', 'phone', 'is_active']
            else:
                campos_editables = ['is_active']
            
            for campo in campos_editables:
                nuevo_valor = request.POST.get(campo)
                if nuevo_valor is not None:
                    if campo == 'is_active':
                        # Convertir a booleano
                        setattr(usuario, campo, nuevo_valor.lower() == 'true')
                    else:
                        setattr(usuario, campo, nuevo_valor)
            
            usuario.save()
            messages.success(request, "Usuario actualizado correctamente.")
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Usuario actualizado correctamente.'})
            else:
                return redirect('mostrar_usuarios')
                
        except Exception as e:
            error_msg = f"Error al actualizar usuario: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            else:
                messages.error(request, error_msg)
                return redirect('mostrar_usuarios')
    
    # GET request - mostrar formulario
    return render(request, 'admin/usuarios/editar_usuario.html', {'usuario': usuario})



@login_required
def ver_usuario(request, user_id):
    usuario = Usuarios.objects.get(id=user_id)
    first_initial = usuario.first_name[0] if usuario.first_name else "?"
    last_initial = usuario.last_name[0] if usuario.last_name else "?"
    last_login = usuario.last_login.strftime('%d/%m/%Y %H:%M') if usuario.last_login else "Nunca"
    permisos = list(usuario.get_all_permissions()) if request.user.is_staff else []
    data = {
        "full_name": f"{usuario.first_name} {usuario.last_name}".strip() or "Sin nombre",
        "initials": f"{first_initial}{last_initial}".upper(),
        "email": usuario.email or "-",
        "phone": getattr(usuario, 'phone', '-') if request.user.is_staff else None,
        "role": "Administrador" if usuario.is_staff else "Usuario",
        "status": "Activo" if usuario.is_active else "Inactivo",
        "date_joined": usuario.date_joined.strftime('%d/%m/%Y'),
        "last_login": last_login,
        "permissions": permisos
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



@csrf_exempt
@login_required
@staff_member_required
def actualizar_usuario(request, id):
    if request.method == "POST":
        usuario = get_object_or_404(Usuarios, id=id)
        data = request.POST
        if usuario.is_staff:
            usuario.first_name = data.get("first_name", usuario.first_name)
            usuario.last_name = data.get("last_name", usuario.last_name)
            usuario.email = data.get("email", usuario.email)
            usuario.phone = data.get("phone", usuario.phone)
            usuario.is_active = data.get("is_active") == "True"
        else:
            usuario.is_active = data.get("is_active") == "True"
        usuario.save()
        return JsonResponse({"success": True, "message": "Usuario actualizado correctamente."})
    return JsonResponse({"success": False, "message": "Método no permitido."})









# ==========================================================
#                   DECOLUCIONES
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
    peticiones = PeticionProducto.objects.select_related('usuario', 'producto').order_by('-fecha_peticion')
    return render(request, 'admin/peticiones/peticiones.html', {'active': 'peticiones', 'peticiones': peticiones})



@login_required
@require_POST
def crear_peticion(request, producto_id):
    try:
        producto = Inventario.objects.get(pk=producto_id)
    except Inventario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Producto no existe.'}, status=404)

    try:
        data = json.loads(request.body)
        cantidad = int(data.get('cantidad', 1))
    except (ValueError, json.JSONDecodeError):
        cantidad = 1

    if cantidad <= 0:
        return JsonResponse({'success': False, 'message': 'Cantidad inválida.'})

    # 🔹 Aseguramos que se guarde correctamente el usuario autenticado
    from django.contrib.auth import get_user_model
    Usuario = get_user_model()

    try:
        usuario = Usuario.objects.get(pk=request.user.pk)
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no válido.'}, status=400)

    peticion = PeticionProducto.objects.create(
        usuario=usuario,
        producto=producto,
        cantidad_solicitada=cantidad
    )

    return JsonResponse({
        'success': True,
        'message': f'Petición creada para {producto.catalogo.nombre}, cantidad {cantidad}.'
    })



@login_required
@require_POST
def crear_peticion(request, producto_id):
    try:
        producto = Inventario.objects.get(pk=producto_id)
    except Inventario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Producto no existe.'}, status=404)

    try:
        data = json.loads(request.body)
        cantidad = int(data.get('cantidad', 1))
    except (ValueError, json.JSONDecodeError):
        cantidad = 1

    if cantidad <= 0:
        return JsonResponse({'success': False, 'message': 'Cantidad inválida.'})

    peticion = PeticionProducto.objects.create(
        usuario=request.user,
        producto=producto,
        cantidad_solicitada=cantidad
    )

    return JsonResponse({
        'success': True,
        'message': f'Petición creada para {producto.catalogo.nombre}, cantidad {cantidad}.'
    })
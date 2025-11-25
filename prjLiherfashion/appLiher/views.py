# ==========================================================
#                   IMPORTS ESTÁNDAR
# ==========================================================


import json
import re
import mercadopago


# ==========================================================
#                   IMPORTS DJANGO
# ==========================================================

from django.http import HttpResponse
from decimal import Decimal
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


# ==========================================================
#                   IMPORTS LOCALES
# ==========================================================


from .decorators import admin_required, permiso_requerido
from .forms import (
    CustomPasswordResetForm, InventarioForm, UsuarioRegistroForm,
    UsuarioUpdateForm, IdentificacionForm, EnvioForm
)
from .models import (
    Carrito, Catalogo, EntradaInventario, Identificacion, Inventario,
    Categoria, Color, ItemCarrito, Permiso, PeticionProducto, Talla, Usuarios, Envio
)



# ==========================================================
#                   FUNCIÓN AUXILIAR (Agregar al inicio)
# ==========================================================

def decimal_from_session(request, key, default='0'):
    """
    Obtiene un valor Decimal de la sesión de forma segura.
    Maneja conversión desde float, string o Decimal.
    """
    from decimal import Decimal, InvalidOperation
    
    valor = request.session.get(key, default)
    
    try:
        # Si ya es Decimal, retornarlo
        if isinstance(valor, Decimal):
            return valor
        
        # Si es None, retornar default
        if valor is None:
            return Decimal(str(default))
        
        # Convertir a string primero para evitar problemas de precisión
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(str(default))


# ========== CONFIGURACIÓN MERCADOPAGO ==========
# Agregar después de los imports existentes

def obtener_sdk_mercadopago():
    """
    Obtiene el SDK de MercadoPago con las credenciales de prueba.
    Reemplaza con tus credenciales reales en producción.
    """
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    return sdk



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
#                   IDENTIFICACIÓN
# ==========================================================


@login_required
def identificacion(request):
    """
    Vista para gestionar los datos de identificación del cliente.
    """
    # ✅ VERIFICAR que el carrito no esté vacío
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(
        'producto__catalogo',
        'producto__categoria',
        'producto__color',
        'producto__talla'
    )
    
    if not items_carrito.exists():
        messages.warning(request, 'Tu carrito está vacío. Agrega productos antes de continuar.')
        return redirect('vista_productos')
    
    # ✅ BUSCAR identificación existente
    identificacion_existente = None
    if request.user.is_authenticated:
        try:
            identificacion_existente = Identificacion.objects.get(usuario=request.user)
        except Identificacion.DoesNotExist:
            try:
                identificacion_existente = Identificacion.objects.get(email=request.user.email)
                identificacion_existente.usuario = request.user
                identificacion_existente.save(update_fields=['usuario'])
            except Identificacion.DoesNotExist:
                pass

    # ✅ PROCESAR formulario
    if request.method == 'POST':
        form = IdentificacionForm(request.POST, instance=identificacion_existente)
        
        if form.is_valid():
            identificacion = form.save(commit=False)
            
            if request.user.is_authenticated:
                identificacion.usuario = request.user
                identificacion.email = request.user.email
            
            try:
                identificacion.save()
                messages.success(request, 'Tus datos de identificación han sido guardados correctamente.')
                
                # ✅ Guardar en sesión
                request.session['identificacion_id'] = identificacion.id
                
                # ✅ CALCULAR Y GUARDAR SUBTOTAL COMO STRING
                subtotal = sum(item.total_precio for item in items_carrito)
                request.session['subtotal'] = str(subtotal)
                
                return redirect('envio')
                
            except Exception as e:
                messages.error(request, f'Error al guardar los datos: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
    else:
        # ✅ PRE-LLENAR con datos del usuario
        initial_data = {}
        if request.user.is_authenticated and not identificacion_existente:
            initial_data = {
                'email': request.user.email,
                'nombre': request.user.first_name,
                'apellido': request.user.last_name,
                'celular': request.user.phone if hasattr(request.user, 'phone') else ''
            }
        
        form = IdentificacionForm(
            instance=identificacion_existente,
            initial=initial_data if initial_data else None
        )

    # ✅ CALCULAR subtotal
    subtotal = sum(item.total_precio for item in items_carrito)
    
    contexto = {
        'form': form,
        'identificacion_existente': identificacion_existente,
        'carrito': carrito,
        'items_carrito': items_carrito,
        'subtotal': subtotal,
    }
    
    return render(request, 'tienda/carrito/identificacion.html', contexto)




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
    """
    Procesa la entrada de stock para una variante específica del inventario.
    """
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
            
            messages.success(
                request, 
                f"¡Entrada registrada! Se añadieron {cantidad} unidades a la variante "
                f"{variante_a_surtir.color}/{variante_a_surtir.talla}. "
                f"(Verifique el stock actualizado)."
            )
            
            # ✅ CORRECCIÓN: Usar catalogo en lugar de producto
            return redirect(
                'listar_movimientos_producto', 
                id_catalogo=variante_a_surtir.catalogo.idcatalogo
            )
            
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
                    "catálogo": "catalogo", 
                    "catalogo": "catalogo",
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
            "Catálogo": permisos.catalogo,
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
    peticiones = PeticionProducto.objects.select_related('usuario', 'producto').order_by('-fecha_peticion')
    return render(request, 'admin/peticiones/peticiones.html', {'active': 'peticiones', 'peticiones': peticiones})



@login_required
@require_POST
def crear_peticion(request, producto_id):
    """
    Crea una petición de producto cuando no hay stock disponible.
    """
    try:
        producto = Inventario.objects.get(pk=producto_id)
    except Inventario.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Producto no existe.'
        }, status=404)

    try:
        data = json.loads(request.body)
        cantidad = int(data.get('cantidad', 1))
    except (ValueError, json.JSONDecodeError):
        cantidad = 1

    if cantidad <= 0:
        return JsonResponse({
            'success': False, 
            'message': 'Cantidad inválida.'
        })

    # Crear la petición
    try:
        peticion = PeticionProducto.objects.create(
            usuario=request.user,
            producto=producto,
            cantidad_solicitada=cantidad
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Petición creada para {producto.catalogo.nombre}, cantidad {cantidad}.',
            'peticion_id': peticion.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al crear la petición: {str(e)}'
        }, status=500)


    # ==========================================================
    #                   ENVÍO
    # ==========================================================

@login_required
def envio(request):
    """
    Vista para gestionar la información de envío del pedido.
    """
    # PASO 1: Verificar que el usuario tenga identificación
    identificacion_existente = None
    if request.user.is_authenticated:
        try:
            identificacion_existente = Identificacion.objects.get(usuario=request.user)
        except Identificacion.DoesNotExist:
            messages.warning(request, 'Por favor completa tu identificación primero.')
            return redirect('identificacion')
    
    # PASO 2: Verificar que el carrito no esté vacío
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(
        'producto__catalogo'
    )
    
    if not items_carrito.exists():
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('carrito')
    
    # PASO 3: Buscar envío existente o crear uno nuevo
    envio_existente = None
    if request.user.is_authenticated:
        envio_existente = Envio.objects.filter(
            usuario=request.user,
            activo=True
        ).order_by('-fecha_actualizacion').first()
    
    # PASO 4: Calcular subtotal
    subtotal = sum(item.total_precio for item in items_carrito)
    
    # Costos de envío según empresa
    COSTOS_ENVIO = {
        'coordinadora': Decimal('12000'),
        'interrapidisimo': Decimal('15000'),
        'envia': Decimal('15000'),
    }
    
    # PASO 5: Procesar formulario
    if request.method == 'POST':
        form = EnvioForm(request.POST, instance=envio_existente)
        
        if form.is_valid():
            envio_obj = form.save(commit=False)
            
            # Asociar con usuario e identificación
            if request.user.is_authenticated:
                envio_obj.usuario = request.user
                envio_obj.identificacion = identificacion_existente
            
            # Calcular costo de envío según empresa seleccionada
            empresa = envio_obj.empresa_envio
            envio_obj.costo_envio = COSTOS_ENVIO.get(empresa, Decimal('12000'))
            
            # Si el teléfono del receptor no se proporciona, usar el de identificación
            if not envio_obj.telefono_receptor and identificacion_existente:
                envio_obj.telefono_receptor = identificacion_existente.celular
            
            # Marcar como activo
            envio_obj.activo = True
            
            try:
                with transaction.atomic():
                    # Desactivar todos los envíos anteriores del usuario
                    Envio.objects.filter(
                        usuario=request.user,
                        activo=True
                    ).update(activo=False)
                    
                    # Guardar el nuevo envío
                    envio_obj.save()
                    
                    # ✅ GUARDAR EN SESIÓN COMO STRING (NO FLOAT)
                    request.session['envio_id'] = envio_obj.id
                    request.session['costo_envio'] = str(envio_obj.costo_envio)
                    request.session['subtotal'] = str(subtotal)
                    
                    messages.success(request, f'Información de envío guardada correctamente.')
                    return redirect('pago')
                    
            except Exception as e:
                messages.error(request, f'Error al guardar el envío: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
    else:
        # Pre-llenar datos si existen
        initial_data = {}
        if envio_existente:
            form = EnvioForm(instance=envio_existente)
        else:
            if identificacion_existente:
                initial_data['nombre_receptor'] = f"{identificacion_existente.nombre} {identificacion_existente.apellido}"
                initial_data['telefono_receptor'] = identificacion_existente.celular
            form = EnvioForm(initial=initial_data)
    
    # Calcular costo de envío actual
    costo_envio = Decimal('12000')  # Por defecto Coordinadora
    if envio_existente:
        costo_envio = envio_existente.costo_envio
    
    total = subtotal + costo_envio
    
    contexto = {
        'form': form,
        'identificacion': identificacion_existente,
        'envio': envio_existente,
        'carrito': carrito,
        'items_carrito': items_carrito,
        'subtotal': subtotal,
        'costo_envio': costo_envio,
        'total': total,
        'costos_envio': COSTOS_ENVIO,
    }
    
    return render(request, 'tienda/carrito/datos_envio.html', contexto)


# ==========================================================
#                   CONFIGURACIÓN
# ==========================================================

@login_required
def pago(request):
    """
    Vista para procesar el pago del pedido con MercadoPago.
    """
    # PASO 1: Verificar identificación
    try:
        identificacion = Identificacion.objects.get(usuario=request.user)
    except Identificacion.DoesNotExist:
        messages.warning(request, 'Debes completar tu identificación primero.')
        return redirect('identificacion')
    
    # PASO 2: Verificar envío activo
    try:
        envio = Envio.objects.filter(
            usuario=request.user, 
            activo=True
        ).order_by('-fecha_actualizacion').first()
        
        if not envio:
            messages.warning(request, 'Debes completar los datos de envío primero.')
            return redirect('envio')
            
    except Exception as e:
        messages.error(request, f'Error al cargar datos de envío: {str(e)}')
        return redirect('envio')
    
    # PASO 3: Obtener carrito
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(
        'producto__catalogo',
        'producto__categoria',
        'producto__color',
        'producto__talla'
    )
    
    if not items_carrito.exists():
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('carrito')
    
    # PASO 4: Calcular totales usando Decimal
    subtotal = sum(item.total_precio for item in items_carrito)
    costo_envio = envio.costo_envio
    
    # Obtener descuento de sesión de forma segura
    descuento = decimal_from_session(request, 'descuento', '0')
    cupon_aplicado = request.session.get('cupon_aplicado', None)
    
    # Calcular total
    total = subtotal + costo_envio - descuento
    
    # PASO 5: Guardar en sesión como STRING
    request.session['subtotal'] = str(subtotal)
    request.session['costo_envio'] = str(costo_envio)
    request.session['descuento'] = str(descuento)
    request.session['total'] = str(total)
    request.session['identificacion_id'] = identificacion.id
    request.session['envio_id'] = envio.id
    
    # PASO 6: Métodos de pago
    payment_methods = [
        {
            'id': 'mercadopago', 
            'name': 'MercadoPago', 
            'icon': 'fas fa-credit-card', 
            'color': 'text-primary',
            'description': 'Tarjetas, PSE, Efectivo y más'
        }
    ]
    
    # PASO 7: Generar preferencia de MercadoPago
    preference_id = None
    error_message = None
    
    try:
        print("=" * 60)
        print("🔍 DEBUG - Creando preferencia de pago")
        print("=" * 60)
        
        # Verificar credenciales
        if not hasattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN'):
            error_message = "❌ MERCADO_PAGO_ACCESS_TOKEN no configurado"
            print(error_message)
            raise ValueError(error_message)
        
        if not hasattr(settings, 'MERCADO_PAGO_PUBLIC_KEY'):
            error_message = "❌ MERCADO_PAGO_PUBLIC_KEY no configurado"
            print(error_message)
            raise ValueError(error_message)
        
        print(f"✅ ACCESS_TOKEN: {settings.MERCADO_PAGO_ACCESS_TOKEN[:20]}...")
        print(f"✅ PUBLIC_KEY: {settings.MERCADO_PAGO_PUBLIC_KEY[:20]}...")
        
        # Inicializar SDK
        sdk = obtener_sdk_mercadopago()
        print("✅ SDK inicializado")
        
        # Construir items para MercadoPago
        items_mp = []
        for item in items_carrito:
            item_data = {
                "title": f"{item.producto.catalogo.nombre} - {item.producto.color}/{item.producto.talla}",
                "quantity": item.cantidad,
                "unit_price": float(item.precio_unitario),
                "currency_id": "COP"
            }
            items_mp.append(item_data)
            print(f"   📦 Item: {item_data['title']} - ${item_data['unit_price']}")
        
        # Agregar costo de envío
        if costo_envio > 0:
            envio_item = {
                "title": f"Envío - {envio.get_empresa_envio_display()}",
                "quantity": 1,
                "unit_price": float(costo_envio),
                "currency_id": "COP"
            }
            items_mp.append(envio_item)
            print(f"   🚚 Envío: ${envio_item['unit_price']}")
        
        # Agregar descuento si existe
        if descuento > 0:
            descuento_item = {
                "title": f"Descuento cupón - {cupon_aplicado}",
                "quantity": 1,
                "unit_price": -float(descuento),
                "currency_id": "COP"
            }
            items_mp.append(descuento_item)
            print(f"   🎟️ Descuento: -${abs(descuento_item['unit_price'])}")
        
        print(f"💰 Total a pagar: ${float(total)}")
        
        # ✅ CREAR PREFERENCIA SIN notification_url
        preference_data = {
            "items": items_mp,
            "payer": {
                "name": identificacion.nombre,
                "surname": identificacion.apellido,
                "email": identificacion.email,
                "phone": {
                    "number": identificacion.celular
                },
                "identification": {
                    "type": identificacion.tipo_documento,
                    "number": identificacion.numero_documento
                },
                "address": {
                    "street_name": envio.direccion_completa,
                    "city_name": envio.municipio,
                    "state_name": envio.departamento
                }
            },
            "back_urls": {
                "success": request.build_absolute_uri(reverse('pago_exitoso')),
                "failure": request.build_absolute_uri(reverse('pago_fallido')),
                "pending": request.build_absolute_uri(reverse('pago_pendiente'))
            },
            "payment_methods": {
                "excluded_payment_methods": [],
                "excluded_payment_types": [],
                "installments": 12
            },
            "statement_descriptor": "LIHER FASHION",
            "external_reference": f"PEDIDO-{request.user.id}-{timezone.now().timestamp()}",
            "expires": False,
        }
        
        # ⚠️ NO incluir notification_url en desarrollo local
        print("⚠️ Modo DEBUG: notification_url omitida (requiere URL pública)")
        
        print("\n🔄 Enviando preferencia a MercadoPago...")
        preference_response = sdk.preference().create(preference_data)
        
        print(f"📊 Status de respuesta: {preference_response['status']}")
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            preference_id = preference["id"]
            
            # Guardar en sesión
            request.session['preference_id'] = preference_id
            
            print(f"✅ Preferencia creada exitosamente!")
            print(f"   ID: {preference_id}")
            print(f"   Init Point: {preference.get('init_point', 'N/A')}")
            print("=" * 60)
        else:
            error_message = f"Error al crear preferencia - Status: {preference_response['status']}"
            print(f"❌ {error_message}")
            print(f"📄 Respuesta completa: {preference_response}")
            messages.error(request, 'Error al crear preferencia de pago. Intenta nuevamente.')
            
    except Exception as e:
        error_message = str(e)
        print(f"\n❌ EXCEPCIÓN al crear preferencia:")
        print(f"   Error: {error_message}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        messages.error(request, f'Error al inicializar el sistema de pagos: {error_message}')
    
    # PASO 8: Contexto
    contexto = {
        'identificacion': identificacion,
        'envio': envio,
        'carrito': carrito,
        'items_carrito': items_carrito,
        'total_items': carrito.total_items_carrito,
        'subtotal': float(subtotal),
        'costo_envio': float(costo_envio),
        'descuento': float(descuento),
        'total': float(total),
        'cupon_aplicado': cupon_aplicado,
        'payment_methods': payment_methods,
        'mostrar_productos': True,
        'puede_editar': True,
        'preference_id': preference_id,
        'mercado_pago_public_key': getattr(settings, 'MERCADO_PAGO_PUBLIC_KEY', ''),
        'error_message': error_message,
    }
    
    return render(request, 'tienda/carrito/pago.html', contexto)


@login_required
@require_POST
def aplicar_cupon(request):
    """
    Valida y aplica un cupón de descuento.
    """
    try:
        data = json.loads(request.body)
        codigo_cupon = data.get('cupon', '').strip().upper()
        
        if not codigo_cupon:
            return JsonResponse({'success': False, 'message': 'Código de cupón inválido'})
        
        # Cupones válidos
        cupones_validos = {
            'DESCUENTO10': {'porcentaje': Decimal('0.10'), 'nombre': '10% de descuento'},
            'DESCUENTO20': {'porcentaje': Decimal('0.20'), 'nombre': '20% de descuento'},
            'PRIMERACOMPRA': {'porcentaje': Decimal('0.15'), 'nombre': '15% primera compra'},
            'BIENVENIDA': {'porcentaje': Decimal('0.05'), 'nombre': '5% bienvenida'},
            'NAVIDAD2024': {'porcentaje': Decimal('0.25'), 'nombre': '25% Navidad'},
        }
        
        if codigo_cupon in cupones_validos:
            cupon = cupones_validos[codigo_cupon]
            
            # ✅ Usar función auxiliar para obtener valores
            subtotal = decimal_from_session(request, 'subtotal', '0')
            costo_envio = decimal_from_session(request, 'costo_envio', '0')
            
            # Calcular descuento
            descuento = subtotal * cupon['porcentaje']
            nuevo_total = subtotal + costo_envio - descuento
            
            # ✅ Guardar COMO STRING
            request.session['descuento'] = str(descuento)
            request.session['total'] = str(nuevo_total)
            request.session['cupon_aplicado'] = codigo_cupon
            request.session['cupon_nombre'] = cupon['nombre']
            
            return JsonResponse({
                'success': True,
                'descuento': float(descuento),
                'descuento_formatted': f'${float(descuento):,.0f}',
                'nuevo_total': float(nuevo_total),
                'nuevo_total_formatted': f'${float(nuevo_total):,.0f}',
                'message': f'✓ Cupón aplicado: {cupon["nombre"]}',
                'cupon_nombre': cupon['nombre']
            })
        else:
            return JsonResponse({'success': False, 'message': 'Cupón inválido o expirado'})
            
    except Exception as e:
        print(f"❌ Error aplicar_cupon: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


# ==========================================================
#  5. REMOVER CUPÓN (CORREGIDA)
# ==========================================================

@login_required
@require_POST
def remover_cupon(request):
    """
    Elimina el cupón aplicado.
    """
    try:
        # ✅ Usar función auxiliar
        subtotal = decimal_from_session(request, 'subtotal', '0')
        costo_envio = decimal_from_session(request, 'costo_envio', '0')
        
        nuevo_total = subtotal + costo_envio
        
        # Resetear
        request.session['descuento'] = '0'
        request.session['total'] = str(nuevo_total)
        request.session.pop('cupon_aplicado', None)
        request.session.pop('cupon_nombre', None)
        
        return JsonResponse({
            'success': True,
            'message': 'Cupón removido correctamente',
            'nuevo_total': float(nuevo_total),
            'nuevo_total_formatted': f'${float(nuevo_total):,.0f}'
        })
    except Exception as e:
        print(f"❌ Error remover_cupon: {e}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@login_required
def pago_exitoso(request):
    """
    Maneja el retorno exitoso de MercadoPago.
    """
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    external_reference = request.GET.get('external_reference')
    preference_id = request.GET.get('preference_id')
    
    # Verificar el pago con MercadoPago
    try:
        sdk = obtener_sdk_mercadopago()
        payment_info = sdk.payment().get(payment_id)
        
        if payment_info["status"] == 200:
            payment_data = payment_info["response"]
            
            # Validar que el pago esté aprobado
            if payment_data["status"] == "approved":
                # Procesar el pedido
                carrito = obtener_o_crear_carrito(request)
                
                with transaction.atomic():
                    # Reducir stock
                    for item in carrito.items_carrito.all():
                        producto = item.producto
                        if producto.stock >= item.cantidad:
                            producto.stock -= item.cantidad
                            producto.save()
                        else:
                            messages.error(request, f'Stock insuficiente para {producto.catalogo.nombre}')
                            return redirect('carrito')
                    
                    # Marcar carrito como completado
                    carrito.completado = True
                    carrito.save()
                    
                    # Limpiar sesión
                    request.session.pop('carrito_id', None)
                    request.session.pop('preference_id', None)
                    request.session.pop('descuento', None)
                    request.session.pop('cupon_aplicado', None)
                
                contexto = {
                    'payment_id': payment_id,
                    'status': payment_data["status"],
                    'status_detail': payment_data.get("status_detail", ""),
                    'transaction_amount': payment_data.get("transaction_amount", 0),
                    'payment_method': payment_data.get("payment_method_id", ""),
                }
                
                messages.success(request, '¡Pago exitoso! Tu pedido ha sido procesado.')
                return render(request, 'tienda/carrito/pago_exitoso.html', contexto)
            else:
                return redirect('pago_pendiente')
        else:
            messages.error(request, 'No se pudo verificar el pago.')
            return redirect('pago_fallido')
            
    except Exception as e:
        print(f"❌ Error verificando pago: {e}")
        messages.error(request, 'Error al verificar el pago.')
        return redirect('pago_fallido')



@login_required
def pago_fallido(request):
    """
    Maneja el retorno fallido de MercadoPago.
    """
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    
    contexto = {
        'payment_id': payment_id,
        'status': status,
    }
    
    messages.error(request, 'El pago no pudo ser procesado.')
    return render(request, 'tienda/carrito/pago_fallido.html', contexto)


@login_required
def pago_pendiente(request):
    """
    Maneja el retorno pendiente de MercadoPago.
    """
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    
    contexto = {
        'payment_id': payment_id,
        'status': status,
    }
    
    messages.warning(request, 'Tu pago está pendiente de confirmación.')
    return render(request, 'tienda/carrito/pago_pendiente.html', contexto)


# ========== WEBHOOK DE MERCADOPAGO ==========

@csrf_exempt
@require_POST
def webhook_mercadopago(request):
    """
    Recibe notificaciones de MercadoPago sobre cambios en el estado del pago.
    """
    try:
        data = json.loads(request.body)
        
        # MercadoPago envía el tipo de notificación
        topic = data.get('topic') or data.get('type')
        
        if topic == 'payment':
            payment_id = data.get('data', {}).get('id') or data.get('id')
            
            # Consultar información del pago
            sdk = obtener_sdk_mercadopago()
            payment_info = sdk.payment().get(payment_id)
            
            if payment_info["status"] == 200:
                payment_data = payment_info["response"]
                
                # Aquí puedes actualizar el estado del pedido en tu base de datos
                # según el estado del pago: approved, pending, rejected, etc.
                
                print(f"✅ Webhook recibido - Payment ID: {payment_id}, Status: {payment_data['status']}")
                
                # Guardar log del webhook (opcional, puedes crear un modelo para esto)
                
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        return HttpResponse(status=500)

        from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
# Asegúrate de importar todas las dependencias necesarias (settings, obtener_sdk_mercadopago, etc.)

@require_POST
@login_required
def crear_preferencia_mp(request):
    """
    Crea la preferencia de Mercado Pago y devuelve el ID.
    """
    try:
        # Recuperar datos de sesión (o rehacer los cálculos si es más seguro)
        total = request.session.get('total')
        identificacion_id = request.session.get('identificacion_id')
        envio_id = request.session.get('envio_id')
        # ... otros datos de sesión necesarios ...
        
        if not total:
            return JsonResponse({'status': 'error', 'message': 'Total no encontrado en sesión.'}, status=400)
        
        # Recalcular items para la preferencia (lógica idéntica al PASO 7 de tu vista 'pago')
        carrito = obtener_o_crear_carrito(request)
        items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(...)
        identificacion = Identificacion.objects.get(pk=identificacion_id)
        envio = Envio.objects.get(pk=envio_id)
        
        # Lógica de construcción de items (igual a tu PASO 7)
        # ... items_mp, descuento, costo_envio ...

        sdk = obtener_sdk_mercadopago()
        
        preference_data = {
            "items": items_mp,
            "payer": { 
                # ... datos del pagador (identificacion) ... 
                "email": identificacion.email,
                # ...
            },
            "back_urls": {
                "success": request.build_absolute_uri(reverse('pago_exitoso')),
                "failure": request.build_absolute_uri(reverse('pago_fallido')),
                "pending": request.build_absolute_uri(reverse('pago_pendiente'))
            },
            "auto_return": "approved",
            "notification_url": request.build_absolute_uri(reverse('webhook_mercadopago')),
            "external_reference": f"PEDIDO-{request.user.id}-{timezone.now().timestamp()}",
            # ... otros campos ...
        }
        
        preference_response = sdk.preference().create(preference_data)

        if preference_response["status"] == 201:
            preference_id = preference_response["response"]["id"]
            # En lugar de guardar en sesión aquí, la devolvemos al frontend
            return JsonResponse({'status': 'success', 'preference_id': preference_id})
        else:
            return JsonResponse({
                'status': 'error', 
                'message': 'Error de MP al crear preferencia',
                'details': preference_response['response']
            }, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
# ==========================================================
#                   IMPORTS ESTÁNDAR
# ==========================================================
import base64
import json
import uuid
from decimal import Decimal, InvalidOperation
import mercadopago


# ==========================================================
#                   IMPORTS DJANGO
# ==========================================================
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F, Sum, Count, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.db.models import Avg, Sum, Count, Max, Min

# ==========================================================
#                   IMPORTACIONES LOCALES
# ==========================================================
from .decorators import admin_required, permiso_requerido
from .forms import (
    CustomPasswordResetForm,
    DireccionEnvioForm,
    MetodoPagoForm,
    PerfilUsuarioForm,
    UsuarioRegistroForm,
    CategoriaForm,
    ColorForm,
    TallaForm,
)
from .models import (
    Carrito,
    DireccionEnvio,
    MetodoPago,
    Pedidos,
    PedidoItem,
    PerfilUsuario,
    Producto,
    VarianteProducto,
    Categoria,
    Color,
    ItemCarrito,
    Permiso,
    PeticionProducto,
    Talla,
    Usuarios,
)


# ==========================================================
#                   FUNCIONES AUXILIARES
# ==========================================================

def obtener_o_crear_carrito(request):
    """
    Función auxiliar para obtener o crear un carrito para el usuario.
    """
    if request.user.is_authenticated:
        carrito, creado = Carrito.objects.get_or_create(
            usuario=request.user, 
            completado=False
        )
    else:
        carrito_id = request.session.get('carrito_id')
        if carrito_id:
            try:
                carrito = Carrito.objects.get(id=carrito_id, completado=False, usuario__isnull=True)
            except Carrito.DoesNotExist:
                carrito = Carrito.objects.create()
                request.session['carrito_id'] = carrito.id
        else:
            carrito = Carrito.objects.create()
            request.session['carrito_id'] = carrito.id
    
    return carrito


def carrito_context(request):
    """
    Context processor para mostrar el contador del carrito en todas las páginas.
    """
    carrito_count = 0
    if request.user.is_authenticated:
        try:
            carrito = Carrito.objects.get(usuario=request.user, completado=False)
            carrito_count = carrito.total_items_carrito
        except Carrito.DoesNotExist:
            pass
    else:
        carrito_id = request.session.get('carrito_id')
        if carrito_id:
            try:
                carrito = Carrito.objects.get(id=carrito_id, completado=False)
                carrito_count = carrito.total_items_carrito
            except Carrito.DoesNotExist:
                pass
    
    return {
        'carrito_count': carrito_count
    }


def parse_precio(precio_str):
    """
    Convierte un string de precio a Decimal manejando formatos con puntos
    """
    if not precio_str:
        return Decimal('0.00')
    
    try:
        # Limpiar el string
        precio_limpio = precio_str.strip().replace(' ', '')
        
        # Si tiene punto como separador de miles y coma decimal
        if '.' in precio_limpio and ',' in precio_limpio:
            # Formato: 1.000,00 -> 1000.00
            precio_limpio = precio_limpio.replace('.', '').replace(',', '.')
        # Si solo tiene puntos (podría ser separador de miles o decimal)
        elif precio_limpio.count('.') == 1 and len(precio_limpio.split('.')[-1]) != 2:
            # Si la parte decimal no tiene 2 dígitos, probablemente es separador de miles
            precio_limpio = precio_limpio.replace('.', '')
        # Si tiene comas como decimal
        elif ',' in precio_limpio:
            precio_limpio = precio_limpio.replace(',', '.')
        
        return Decimal(precio_limpio)
    except (ValueError, InvalidOperation):
        raise ValueError("Formato de precio inválido")


def procesar_imagen_base64(imagen_base64, prefix="variante"):
    """
    Procesa una imagen en base64 y retorna un ContentFile
    """
    if not imagen_base64 or not imagen_base64.startswith('data:image'):
        return None
    
    try:
        format, imgstr = imagen_base64.split(';base64,')
        ext = format.split('/')[-1]
        
        # Validar extensión
        if ext not in ['jpeg', 'jpg', 'png', 'gif']:
            raise ValueError("Formato de imagen no soportado")
            
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
        image_data = ContentFile(base64.b64decode(imgstr), name=filename)
        return image_data
    except Exception as e:
        raise ValueError(f"Error al procesar imagen: {str(e)}")


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


# ==========================================================
#                   VISTAS PÚBLICAS
# ==========================================================

def pagina_principal(request):
    categorias = Categoria.objects.all()  
    
    return render(request, 'tienda/principal/pagina_principal.html', {
        'categorias': categorias,
    })


def vista_productos(request):
    # Obtener parámetros de filtro
    categoria_filtrar = request.GET.get('categoria', '').strip()
    color_filtrar = request.GET.get('color', '').strip()
    talla_filtrar = request.GET.get('talla', '').strip()
    busqueda = request.GET.get('q', '').strip()

    # Base queryset de productos activos
    productos = Producto.objects.filter(
        estado='Activo'
    ).prefetch_related(
        Prefetch('variantes', 
                queryset=VarianteProducto.objects.filter(activo=True)
                .select_related('talla', 'color')
                .order_by('talla__orden', 'color__color'))
    ).select_related('categoria').order_by('-fecha_creacion')

    # Aplicar filtros
    if categoria_filtrar:
        productos = productos.filter(categoria__categoria=categoria_filtrar)

    if color_filtrar:
        productos = productos.filter(variantes__color__color=color_filtrar)

    if talla_filtrar:
        productos = productos.filter(variantes__talla__talla=talla_filtrar)

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(referencia__icontains=busqueda)
        )

    # Obtener filtros disponibles (solo para productos que tienen stock)
    categorias = Categoria.objects.filter(
        producto__estado='Activo',
        producto__variantes__activo=True,
        producto__variantes__stock__gt=0
    ).distinct().order_by('categoria')
    
    colores = Color.objects.filter(
        varianteproducto__activo=True,
        varianteproducto__producto__estado='Activo',
        varianteproducto__stock__gt=0
    ).distinct().order_by('color')
    
    tallas = Talla.objects.filter(
        varianteproducto__activo=True,
        varianteproducto__producto__estado='Activo',
        varianteproducto__stock__gt=0
    ).distinct().order_by('orden', 'talla')

    # Paginación
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'productos': page_obj,
        'categorias': categorias,
        'colores': colores,
        'tallas': tallas,
        'selected_categoria': categoria_filtrar,
        'selected_color': color_filtrar,
        'selected_talla': talla_filtrar,
        'busqueda': busqueda,
    }

    return render(request, 'tienda/principal/card_productos.html', context)


def detalle_producto(request, idproducto):
    """API endpoint para obtener detalle del producto con variantes"""
    producto = get_object_or_404(Producto, pk=idproducto)
    
    # Serializar variantes
    variantes_data = []
    for variante in producto.variantes.select_related('talla', 'color').filter(activo=True):
        variantes_data.append({
            'id': variante.idvariante,
            'talla': {
                'id': variante.talla.id,
                'talla': variante.talla.talla
            },
            'color': {
                'id': variante.color.id,
                'color': variante.color.color,
                'codigo_hex': variante.color.codigo_hex
            },
            'stock': variante.stock,
            'imagen': variante.imagen.url if variante.imagen else producto.imagen.url if producto.imagen else None
        })
    
    data = {
        'idproducto': producto.idproducto,
        'nombre': producto.nombre,
        'referencia': producto.referencia,
        'precio': str(producto.precio),
        'descripcion': producto.descripcion or '',
        'imagen': producto.imagen.url if producto.imagen else None,
        'categoria': str(producto.categoria) if producto.categoria else None,
        'variantes': variantes_data
    }
    
    return JsonResponse(data)


# ==========================================================
#                   AUTENTICACIÓN Y REGISTRO
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

    # Guardar permisos solo si el rol es administrador
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
            return redirect('panel_admin')  
        else:
            return redirect('pagina_principal')  
    else:
        return render(request, 'usuarios/autenticacion/activacion_invalida.html')


def validar_email_ajax(request):
    email = request.GET.get('email', '').strip()
    exists = Usuarios.objects.filter(email__iexact=email).exists()
    return JsonResponse({'exists': exists})


# ==========================================================
#                   GESTIÓN DE CONTRASEÑAS
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
#                   CARRITO DE COMPRAS
# ==========================================================

def carrito(request):
    """
    Vista para mostrar el contenido del carrito.
    """
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(
        'producto__producto', 
        'producto__talla', 
        'producto__color'
    )
    
    subtotal = sum(item.total_precio for item in items_carrito)
    iva = subtotal * Decimal('0.19')  # 19% IVA
    total = subtotal + iva
    
    contexto = {
        'carrito': carrito,
        'items_carrito': items_carrito,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
    }
    return render(request, 'tienda/carrito/carrito.html', contexto)


def agregar_al_carrito(request, variante_id):
    """
    Vista para agregar un producto al carrito.
    """
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        variante = get_object_or_404(VarianteProducto, idvariante=variante_id)
        
        # Verificar stock
        if variante.stock < cantidad:
            messages.error(request, f'No hay suficiente stock. Stock disponible: {variante.stock}')
            return redirect('vista_productos')
        
        carrito = obtener_o_crear_carrito(request)
        
        # Verificar si el item ya está en el carrito
        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=variante,
            defaults={
                'cantidad': cantidad,
                'precio_unitario': variante.producto.precio
            }
        )
        
        if not creado:
            # Si ya existe, actualizar cantidad
            nueva_cantidad = item.cantidad + cantidad
            if nueva_cantidad > variante.stock:
                messages.error(request, f'No puedes agregar más de {variante.stock} unidades')
                return redirect('carrito')
            
            item.cantidad = nueva_cantidad
            item.save()
            messages.success(request, f'Cantidad actualizada: {item.producto.producto.nombre}')
        else:
            messages.success(request, f'Producto agregado al carrito: {variante.producto.nombre}')
        
        # Actualizar contador en sesión
        if request.user.is_authenticated:
            request.session['carrito_items'] = carrito.total_items_carrito
        else:
            request.session['carrito_items'] = carrito.total_items_carrito
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'carrito_count': carrito.total_items_carrito,
                'message': 'Producto agregado al carrito'
            })
        
        return redirect('carrito')
    
    return redirect('vista_productos')


@require_POST
def agregar_al_carrito(request, variante_id):
    """
    Vista para agregar un producto al carrito.
    """
    try:
        cantidad = int(request.POST.get('cantidad', 1))
        variante = get_object_or_404(VarianteProducto, idvariante=variante_id)
        
        # Verificar stock
        if variante.stock < cantidad:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': f'No hay suficiente stock. Stock disponible: {variante.stock}'
                })
            messages.error(request, f'No hay suficiente stock. Stock disponible: {variante.stock}')
            return redirect('vista_productos')
        
        carrito = obtener_o_crear_carrito(request)
        
        # Verificar si el item ya está en el carrito
        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=variante,
            defaults={
                'cantidad': cantidad,
                'precio_unitario': variante.producto.precio
            }
        )
        
        if not creado:
            # Si ya existe, actualizar cantidad
            nueva_cantidad = item.cantidad + cantidad
            if nueva_cantidad > variante.stock:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'message': f'No puedes agregar más de {variante.stock} unidades'
                    })
                messages.error(request, f'No puedes agregar más de {variante.stock} unidades')
                return redirect('carrito')
            
            item.cantidad = nueva_cantidad
            item.save()
            mensaje = f'Cantidad actualizada: {item.producto.producto.nombre}'
        else:
            mensaje = f'Producto agregado al carrito: {variante.producto.nombre}'
        
        # Actualizar contador en sesión
        request.session['carrito_items'] = carrito.total_items_carrito
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'carrito_count': carrito.total_items_carrito,
                'message': mensaje
            })
        
        messages.success(request, mensaje)
        return redirect('carrito')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error al agregar al carrito: {str(e)}'
            })
        messages.error(request, f'Error al agregar al carrito: {str(e)}')
        return redirect('vista_productos')


@require_POST
def actualizar_carrito(request, item_id):
    """
    Vista para actualizar la cantidad de un item en el carrito.
    """
    try:
        cantidad = int(request.POST.get('cantidad', 1))
        item = get_object_or_404(ItemCarrito, id=item_id)
        
        # Verificar que el item pertenece al carrito del usuario
        carrito_usuario = obtener_o_crear_carrito(request)
        if item.carrito != carrito_usuario:
            return JsonResponse({
                'success': False,
                'message': 'No tienes permiso para modificar este item'
            })
        
        # Verificar stock
        if cantidad > item.producto.stock:
            return JsonResponse({
                'success': False,
                'message': f'No hay suficiente stock. Stock disponible: {item.producto.stock}'
            })
        
        if cantidad > 0:
            item.cantidad = cantidad
            item.save()
            mensaje = 'Cantidad actualizada'
        else:
            item.delete()
            mensaje = 'Producto eliminado del carrito'
        
        # Recalcular totales
        carrito = obtener_o_crear_carrito(request)
        items_carrito = ItemCarrito.objects.filter(carrito=carrito)
        subtotal = sum(item.total_precio for item in items_carrito)
        iva = subtotal * Decimal('0.19')
        total = subtotal + iva
        
        # Actualizar contador en sesión
        request.session['carrito_items'] = carrito.total_items_carrito
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'carrito_count': carrito.total_items_carrito,
            'subtotal': float(subtotal),
            'iva': float(iva),
            'total': float(total),
            'item_subtotal': float(item.total_precio) if cantidad > 0 else 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al actualizar el carrito: {str(e)}'
        })


@require_POST
def eliminar_del_carrito(request, item_id):
    """
    Vista para eliminar un item del carrito.
    """
    try:
        item = get_object_or_404(ItemCarrito, id=item_id)
        
        # Verificar que el item pertenece al carrito del usuario
        carrito_usuario = obtener_o_crear_carrito(request)
        if item.carrito != carrito_usuario:
            return JsonResponse({
                'success': False,
                'message': 'No tienes permiso para eliminar este item'
            })
        
        nombre_producto = item.producto.producto.nombre
        item.delete()
        
        # Recalcular totales
        carrito = obtener_o_crear_carrito(request)
        items_carrito = ItemCarrito.objects.filter(carrito=carrito)
        subtotal = sum(item.total_precio for item in items_carrito)
        iva = subtotal * Decimal('0.19')
        total = subtotal + iva
        
        # Actualizar contador en sesión
        request.session['carrito_items'] = carrito.total_items_carrito
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Producto eliminado: {nombre_producto}',
                'carrito_count': carrito.total_items_carrito,
                'subtotal': float(subtotal),
                'iva': float(iva),
                'total': float(total)
            })
        
        messages.success(request, f'Producto eliminado: {nombre_producto}')
        return redirect('carrito')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar del carrito: {str(e)}'
            })
        messages.error(request, f'Error al eliminar del carrito: {str(e)}')
        return redirect('carrito')


@require_POST
def limpiar_carrito(request):
    """
    Vista para vaciar completamente el carrito.
    """
    try:
        carrito = obtener_o_crear_carrito(request)
        items_count = carrito.items_carrito.count()
        carrito.items_carrito.all().delete()
        
        # Actualizar contador en sesión
        request.session['carrito_items'] = 0
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Carrito vaciado. Se eliminaron {items_count} productos.',
                'carrito_count': 0,
                'subtotal': 0,
                'iva': 0,
                'total': 0
            })
        
        messages.success(request, f'Carrito vaciado. Se eliminaron {items_count} productos.')
        return redirect('carrito')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error al vaciar el carrito: {str(e)}'
            })
        messages.error(request, f'Error al vaciar el carrito: {str(e)}')
        return redirect('carrito')


# ==========================================================
#                   GESTIÓN DE USUARIO
# ==========================================================

@login_required
def mi_cuenta(request):
    """Vista principal de Mi Cuenta"""
    return render(request, 'usuarios/cuenta/inicio.html')


@login_required
def mi_perfil(request):
    """Vista para ver el perfil del usuario"""
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    return render(request, 'usuarios/cuenta/mi_perfil.html', {
        'perfil': perfil
    })


@login_required
def editar_perfil(request):
    """Vista para editar el perfil del usuario"""
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil se ha actualizado correctamente.')
            return redirect('mi_perfil')
    else:
        form = PerfilUsuarioForm(instance=perfil)
    
    return render(request, 'usuarios/cuenta/editar_perfil.html', {
        'form': form,
        'perfil': perfil
    })


@login_required
def lista_direcciones(request):
    """Vista para listar direcciones del usuario"""
    direcciones = DireccionEnvio.objects.filter(usuario=request.user)
    return render(request, 'usuarios/cuenta/direcciones.html', {
        'direcciones': direcciones
    })


@login_required
def agregar_direccion(request):
    """Vista para agregar nueva dirección"""
    if request.method == 'POST':
        form = DireccionEnvioForm(request.POST)
        if form.is_valid():
            direccion = form.save(commit=False)
            direccion.usuario = request.user
            
            # Si es la primera dirección, establecer como principal
            if not DireccionEnvio.objects.filter(usuario=request.user).exists():
                direccion.es_principal = True
            
            direccion.save()
            messages.success(request, 'Dirección agregada correctamente.')
            return redirect('lista_direcciones')
    else:
        form = DireccionEnvioForm()
    
    return render(request, 'usuarios/cuenta/agregar_direccion.html', {
        'form': form
    })


@login_required
def editar_direccion(request, pk):
    """Vista para editar dirección existente"""
    direccion = get_object_or_404(DireccionEnvio, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = DireccionEnvioForm(request.POST, instance=direccion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dirección actualizada correctamente.')
            return redirect('lista_direcciones')
    else:
        form = DireccionEnvioForm(instance=direccion)
    
    return render(request, 'usuarios/cuenta/editar_direccion.html', {
        'form': form,
        'direccion': direccion
    })


@login_required
def eliminar_direccion(request, pk):
    """Vista para eliminar dirección"""
    direccion = get_object_or_404(DireccionEnvio, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        direccion.delete()
        messages.success(request, 'Dirección eliminada correctamente.')
    
    return redirect('lista_direcciones')


@login_required
def establecer_direccion_principal(request, pk):
    """Establecer una dirección como principal"""
    direccion = get_object_or_404(DireccionEnvio, pk=pk, usuario=request.user)
    
    # Quitar principal de todas las direcciones
    DireccionEnvio.objects.filter(usuario=request.user).update(es_principal=False)
    
    # Establecer esta como principal
    direccion.es_principal = True
    direccion.save()
    
    messages.success(request, 'Dirección principal actualizada.')
    return redirect('lista_direcciones')


@login_required
def lista_metodos_pago(request):
    """Vista para listar métodos de pago"""
    metodos_pago = MetodoPago.objects.filter(usuario=request.user)
    return render(request, 'usuarios/cuenta/metodos_pago.html', {
        'metodos_pago': metodos_pago
    })


@login_required
def agregar_metodo_pago(request):
    """Vista para agregar nuevo método de pago"""
    if request.method == 'POST':
        form = MetodoPagoForm(request.POST)
        if form.is_valid():
            metodo_pago = form.save(commit=False)
            metodo_pago.usuario = request.user
            metodo_pago.save()
            messages.success(request, 'Método de pago agregado correctamente.')
            return redirect('lista_metodos_pago')
    else:
        form = MetodoPagoForm()
    
    return render(request, 'usuarios/cuenta/agregar_metodo_pago.html', {
        'form': form
    })


@login_required
def eliminar_metodo_pago(request, pk):
    """Vista para eliminar método de pago"""
    metodo_pago = get_object_or_404(MetodoPago, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        metodo_pago.delete()
        messages.success(request, 'Método de pago eliminado correctamente.')
    
    return redirect('lista_metodos_pago')


@login_required
def establecer_metodo_pago_principal(request, pk):
    """Establecer un método de pago como principal"""
    metodo_pago = get_object_or_404(MetodoPago, pk=pk, usuario=request.user)
    
    # Quitar principal de todos los métodos
    MetodoPago.objects.filter(usuario=request.user).update(es_principal=False)
    
    # Establecer este como principal
    metodo_pago.es_principal = True
    metodo_pago.save()
    
    messages.success(request, 'Método de pago principal actualizado.')
    return redirect('lista_metodos_pago')


@login_required
def mis_pedidos(request):
    """Vista para listar pedidos del usuario"""
    pedidos_list = Pedidos.objects.filter(cliente=request.user.email).order_by('-fecha')
    
    # Paginación
    paginator = Paginator(pedidos_list, 10)  # 10 pedidos por página
    page_number = request.GET.get('page')
    pedidos = paginator.get_page(page_number)
    
    return render(request, 'usuarios/cuenta/mis_pedidos.html', {
        'pedidos': pedidos
    })


@login_required
def detalle_pedido(request, pedido_id):
    """Vista para ver detalle de un pedido"""
    pedido = get_object_or_404(Pedidos, idpedido=pedido_id, cliente=request.user.email)
    
    # Obtener items del pedido si existen
    try:
        items_pedido = pedido.items.all()
    except:
        items_pedido = []
    
    # Obtener seguimiento del pedido si existe
    try:
        seguimientos = pedido.seguimientos.all().order_by('-fecha')
    except:
        seguimientos = []
    
    return render(request, 'usuarios/cuenta/detalle_pedido.html', {
        'pedido': pedido,
        'items_pedido': items_pedido,
        'seguimientos': seguimientos
    })


# ==========================================================
#                   CHECKOUT Y PAGOS
# ==========================================================

@login_required
def envio(request):
    """Vista para el paso de envío"""
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(
        'producto__producto', 'producto__talla', 'producto__color'
    )
    
    if not items_carrito.exists():
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('carrito')
    
    # Verificar que pasó por identificación
    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.warning(request, 'Primero completa tu información personal')
        return redirect('identificacion')
    
    # Obtener direcciones del usuario
    direcciones = DireccionEnvio.objects.filter(usuario=request.user)
    direccion_principal = direcciones.filter(es_principal=True).first()
    
    # Calcular totales
    subtotal = sum(item.total_precio for item in items_carrito)
    descuento = Decimal('0.00')
    costo_envio = Decimal('12000.00')  # Valor por defecto
    
    if request.method == 'POST':
        # VALIDACIONES DE CAMPOS REQUERIDOS
        campos_requeridos = {
            'departamento': 'Departamento',
            'ciudad': 'Ciudad',
            'tipo_direccion': 'Tipo de dirección',
            'calle': 'Calle',
            'numero': 'Número',
            'barrio': 'Barrio',
            'nombre_recibe': 'Nombre de quien recibe',
            'telefono': 'Teléfono',
            'empresa': 'Empresa de envío'
        }
        
        errores = []
        for campo, nombre in campos_requeridos.items():
            if not request.POST.get(campo, '').strip():
                errores.append(f'{nombre} es obligatorio')
        
        if errores:
            for error in errores:
                messages.error(request, error)
            
            total = subtotal - descuento + costo_envio
            context = {
                'direcciones': direcciones,
                'direccion_principal': direccion_principal,
                'subtotal': subtotal,
                'descuento': descuento,
                'costo_envio': costo_envio,
                'total': total,
                'items_carrito': items_carrito,
                'checkout_data': checkout_data,
            }
            return render(request, 'tienda/carrito/datos_envio.html', context)
        
        # Procesar selección de dirección o crear nueva
        direccion_id = request.POST.get('direccion_id')
        
        if direccion_id:
            # Usar dirección existente
            direccion = get_object_or_404(DireccionEnvio, id=direccion_id, usuario=request.user)
        else:
            # Crear nueva dirección
            # Construir dirección completa
            calle = request.POST.get('calle', '').strip()
            letra = request.POST.get('letra', '').strip()
            numero = request.POST.get('numero', '').strip()
            adicional = request.POST.get('adicional', '').strip()
            
            direccion_completa = f"{calle}"
            if letra:
                direccion_completa += f" {letra}"
            direccion_completa += f" {numero}"
            if adicional:
                direccion_completa += f" - {adicional}"
            
            direccion = DireccionEnvio.objects.create(
                usuario=request.user,
                nombre_completo=request.POST.get('nombre_recibe', '').strip(),
                telefono=request.POST.get('telefono', '').strip(),
                departamento=request.POST.get('departamento', '').strip(),
                municipio=request.POST.get('ciudad', '').strip(),
                tipo_direccion=request.POST.get('tipo_direccion', '').strip(),
                direccion=direccion_completa,
                barrio=request.POST.get('barrio', '').strip(),
                piso_apartamento=request.POST.get('apartamento', '').strip(),
            )
        
        # Obtener empresa de envío seleccionada
        empresa_envio = request.POST.get('empresa', 'coordinadora')
        
        # Ajustar costo según empresa
        costos_envio = {
            'coordinadora': Decimal('12000.00'),
            'interrapidisimo': Decimal('15000.00'),
            'envia': Decimal('15000.00'),
        }
        costo_envio = costos_envio.get(empresa_envio, Decimal('12000.00'))
        
        # Actualizar información de envío en sesión
        if 'checkout_data' not in request.session:
            request.session['checkout_data'] = {}
            
        request.session['checkout_data'].update({
            'direccion_id': direccion.id,
            'direccion_completa': direccion.direccion,
            'departamento': direccion.departamento,
            'municipio': direccion.municipio,
            'barrio': direccion.barrio,
            'nombre_recibe': direccion.nombre_completo,
            'telefono_recibe': direccion.telefono,
            'empresa_envio': empresa_envio,
            'costo_envio': str(costo_envio),
        })
        
        # Forzar guardado de sesión
        request.session.modified = True
        
        messages.success(request, 'Información de envío guardada correctamente')
        # CORRECCIÓN: Redirigir explícitamente a pago
        return redirect('pago')
    
    # GET request
    total = subtotal - descuento + costo_envio
    
    context = {
        'direcciones': direcciones,
        'direccion_principal': direccion_principal,
        'subtotal': subtotal,
        'descuento': descuento,
        'costo_envio': costo_envio,
        'total': total,
        'items_carrito': items_carrito,
        'checkout_data': checkout_data,
    }
    
    return render(request, 'tienda/carrito/datos_envio.html', context)

@login_required
def pago(request):
    """Vista para el paso de pago final - SOLO MERCADOPAGO"""
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(
        'producto__producto', 'producto__talla', 'producto__color'
    )
    
    if not items_carrito.exists():
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('carrito')
    
    # Verificar que pasó por los pasos anteriores
    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.warning(request, 'Primero completa los pasos anteriores')
        return redirect('identificacion')
    
    if 'direccion_id' not in checkout_data:
        messages.warning(request, 'Primero completa la información de envío')
        return redirect('envio')
    
    # Obtener dirección de envío
    try:
        direccion = DireccionEnvio.objects.get(
            id=checkout_data['direccion_id'], 
            usuario=request.user
        )
    except DireccionEnvio.DoesNotExist:
        messages.error(request, 'La dirección de envío no es válida')
        return redirect('envio')
    
    # Calcular totales
    subtotal = sum(item.total_precio for item in items_carrito)
    descuento = Decimal('0.00')
    costo_envio = Decimal(checkout_data.get('costo_envio', '12000.00'))
    total = subtotal - descuento + costo_envio
    
    # Inicializar variables
    preference_id = None
    mercadopago_public_key = getattr(settings, 'MERCADOPAGO_PUBLIC_KEY', '')
    init_point = None
    error_message = None
    
    # Intentar crear preferencia de MercadoPago
    if mercadopago_public_key and mercadopago_public_key != '':
        try:
            print("🔄 Intentando crear preferencia de MercadoPago...")
            preferencia_mp = crear_preferencia_mercadopago(items_carrito, checkout_data, total)
            
            if preferencia_mp:
                preference_id = preferencia_mp.get('id')
                init_point = preferencia_mp.get('init_point')  # URL de pago
                print(f"✅ Preferencia creada exitosamente: {preference_id}")
                print(f"✅ URL de pago: {init_point}")
            else:
                error_message = "No se pudo crear la preferencia de pago"
                print("⚠️ No se pudo crear la preferencia")
        except Exception as e:
            error_message = f"Error al inicializar MercadoPago: {str(e)}"
            print(f"❌ Error al crear preferencia: {str(e)}")
    else:
        error_message = "MercadoPago no está configurado"
        print("⚠️ No hay credenciales de MercadoPago configuradas")
    
    context = {
        'items_carrito': items_carrito,
        'direccion': direccion,
        'subtotal': subtotal,
        'descuento': descuento,
        'costo_envio': costo_envio,
        'total': total,
        'checkout_data': checkout_data,
        'mercadopago_public_key': mercadopago_public_key,
        'preference_id': preference_id,
        'init_point': init_point,
        'error_message': error_message,
    }
    
    return render(request, 'tienda/carrito/pago.html', context)

def construir_metodos_pago(mercadopago_disponible, preference_id):
    """Construye la lista de métodos de pago PRIORIZANDO MERCADOPAGO"""
    payment_methods = []
    
    # 1. MERCADOPAGO PRIMERO (si está disponible)
    if mercadopago_disponible and preference_id:
        payment_methods.append({
            'id': 'mercadopago',
            'name': 'Pago con Tarjeta (Recomendado)',
            'icon': 'fas fa-credit-card',
            'color': 'text-primary',
            'description': 'Pago seguro - Visa, Mastercard, American Express',
            'enabled': True,
            'recommended': True,  # Marcar como recomendado
            'badge': 'Más seguro',  # Badge especial
        })
    
    # 2. Efectivo como opción alternativa
    payment_methods.append({
        'id': 'efectivo',
        'name': 'Efectivo contra entrega',
        'icon': 'fas fa-money-bill-wave',
        'color': 'text-warning',
        'description': 'Paga cuando recibas tu pedido',
        'enabled': True,
        'recommended': False,
    })
    
    return payment_methods


@login_required
def identificacion(request):
    """Vista para el paso de identificación"""
    carrito = obtener_o_crear_carrito(request)
    items_carrito = ItemCarrito.objects.filter(carrito=carrito).select_related(
        'producto__producto', 'producto__talla', 'producto__color'
    )
    
    if not items_carrito.exists():
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('carrito')
    
    # Calcular totales
    subtotal = sum(item.total_precio for item in items_carrito)
    descuento = Decimal('0.00')
    total = subtotal - descuento
    
    # Obtener datos del usuario
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        # Validar campos requeridos
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        tipo_documento = request.POST.get('tipo_documento', '')
        numero_documento = request.POST.get('numero_documento', '').strip()
        celular = request.POST.get('celular', '').strip()
        
        # Validaciones
        if not all([nombre, apellido, tipo_documento, numero_documento, celular]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'tienda/carrito/identificacion.html', {
                'perfil': perfil,
                'subtotal': subtotal,
                'descuento': descuento,
                'total': total,
                'items_carrito': items_carrito,
            })
        
        # Guardar/actualizar información del perfil
        perfil.nombre = nombre
        perfil.apellido = apellido
        perfil.tipo_documento = tipo_documento
        perfil.numero_documento = numero_documento
        perfil.telefono = celular
        perfil.save()
        
        # Guardar en sesión para usar en siguientes pasos
        request.session['checkout_data'] = {
            'nombre': perfil.nombre,
            'apellido': perfil.apellido,
            'email': request.user.email,
            'telefono': perfil.telefono,
            'tipo_documento': perfil.tipo_documento,
            'numero_documento': perfil.numero_documento,
        }
        
        messages.success(request, 'Información guardada correctamente')
        # CORRECCIÓN: Redirigir explícitamente a envío
        return redirect('envio')
    
    context = {
        'perfil': perfil,
        'subtotal': subtotal,
        'descuento': descuento,
        'total': total,
        'items_carrito': items_carrito,
    }
    
    return render(request, 'tienda/carrito/identificacion.html', context)

def procesar_pago_efectivo(request, carrito, items_carrito, total, direccion):
    """Procesa el pago en efectivo"""
    try:
        with transaction.atomic():
            # Crear el pedido
            pedido = Pedidos.objects.create(
                cliente=request.user.email,
                fecha=timezone.now(),
                estado_pedido='Pendiente',
                metodo_pago='Efectivo contra entrega',
                total=total,
                estado_pago='Pendiente'
            )
            
            # Crear items del pedido
            for item in items_carrito:
                if item.producto.stock < item.cantidad:
                    raise ValueError(f"Stock insuficiente para {item.producto.producto.nombre}")
                
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=item.producto.producto,
                    variante=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    subtotal=item.total_precio
                )
                
                # Reducir stock
                item.producto.stock -= item.cantidad
                item.producto.save()
            
            # Marcar carrito como completado
            carrito.completado = True
            carrito.save()
            
            # Limpiar sesión
            if 'checkout_data' in request.session:
                del request.session['checkout_data']
            if 'carrito_items' in request.session:
                del request.session['carrito_items']
            
            messages.success(request, f'¡Pedido #{pedido.idpedido} creado exitosamente!')
            return redirect('confirmacion_pedido', pedido_id=pedido.idpedido)
            
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('carrito')
    except Exception as e:
        messages.error(request, f'Error al procesar el pedido: {str(e)}')
        return redirect('pago')

# ==========================================================
#                   PANEL DE ADMINISTRACIÓN
# ==========================================================

@login_required
@admin_required
def panel_admin(request):
    permisos = {"vista_usuario": True}

    if hasattr(request.user, 'permisos'):
        permisos.update({
            "inicio": request.user.permisos.inicio,
            "inventario": request.user.permisos.inventario,
            "pedidos": request.user.permisos.pedidos,
            "usuarios": request.user.permisos.usuarios,
            "devoluciones": request.user.permisos.devoluciones,
            "peticiones": request.user.permisos.peticiones,
        })
    productos = (
        Producto.objects
        .annotate(
            n_variantes=Count("variantes"),
            total_stock=Sum("variantes__stock")
        )
    )

    total_productos = productos.count()
    productos_activos = productos.filter(estado="Activo").count()
    productos_inactivos = productos.filter(estado="Inactivo").count()

    total_variantes = VarianteProducto.objects.count()

    productos_con_variantes = productos.filter(n_variantes__gt=0).count()
    productos_sin_variantes = productos.filter(n_variantes=0).count()

    productos_con_stock = productos.filter(total_stock__gt=0).count()
    productos_sin_stock = productos.filter(total_stock__lte=0).count()


    precio_promedio = productos.aggregate(avg=Avg("precio"))["avg"] or 0
    precio_max = productos.aggregate(m=Max("precio"))["m"] or 0
    precio_min = productos.aggregate(m=Min("precio"))["m"] or 0

    valor_inventario = productos.aggregate(
        total=Sum(F("precio") * F("total_stock"))
    )["total"] or 0


    usuarios = Usuarios.objects.all()
    total_usuarios = usuarios.count()
    usuarios_activos = usuarios.filter(is_active=True).count()
    usuarios_inactivos = usuarios.filter(is_active=False).count()


    context = {
        "permisos_json": json.dumps(permisos),

        # Productos
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "productos_inactivos": productos_inactivos,

        # Variantes
        "total_variantes": total_variantes,
        "productos_con_variantes": productos_con_variantes,
        "productos_sin_variantes": productos_sin_variantes,

        # Stock
        "productos_con_stock": productos_con_stock,
        "productos_sin_stock": productos_sin_stock,

        # Precios
        "precio_promedio": round(precio_promedio, 2),
        "precio_max": precio_max,
        "precio_min": precio_min,
        "valor_inventario": round(valor_inventario, 2),

        # Usuarios
        "total_usuarios": total_usuarios,
        "usuarios_activos": usuarios_activos,
        "usuarios_inactivos": usuarios_inactivos,
    }

    return render(request, "admin/panel_admin.html", context)

@login_required
def confirmacion_pedido(request, pedido_id):
    """Vista de confirmación del pedido"""
    pedido = get_object_or_404(Pedidos, idpedido=pedido_id, cliente=request.user.email)
    
    # Intentar obtener items del pedido
    try:
        items_pedido = PedidoItem.objects.filter(pedido=pedido).select_related(
            'producto', 'variante__talla', 'variante__color'
        )
    except:
        items_pedido = []
    
    context = {
        'pedido': pedido,
        'items_pedido': items_pedido,
    }
    
    return render(request, 'tienda/carrito/confirmacion.html', context)


# ==========================================================
#                   GESTIÓN DE INVENTARIO
# ==========================================================

def inventario(request):
    productos = Producto.objects.all()

    total_productos = productos.count()
    productos_activos = productos.filter(estado="Activo").count()
    productos_inactivos = productos.filter(estado="Inactivo").count()
    total_variantes = VarianteProducto.objects.count()

    context = {
        "productos": productos,
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "productos_inactivos": productos_inactivos,
        "total_variantes": total_variantes,
    }

    return render(request, "admin/inventario.html", context)


def inventario_estadisticas(request):
    productos = Producto.objects.all()

    total_productos = productos.count()
    productos_activos = productos.filter(estado="Activo").count()
    productos_inactivos = productos.filter(estado="Inactivo").count()

    total_variantes = VarianteProducto.objects.count()

    context = {
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "productos_inactivos": productos_inactivos,
        "total_variantes": total_variantes,
    }

    return render(request, "admin/inventario_estadisticas.html", context)


def configuracion_inventario(request):
    return render(request, 'admin/inventario/configuracion_inventario.html')


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
        nombre = request.POST.get('nombre', '').strip()
        referencia = request.POST.get('referencia', '').strip()
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '')
        estado = request.POST.get('estado', 'Activo')
        precio_str = request.POST.get('precio', '0')
        imagen = request.FILES.get('imagen')

        context.update({
            "nombre": nombre,
            "referencia": referencia,
            "categoria_id": categoria_id,
            "descripcion": descripcion,
            "precio": precio_str,
        })

        # Validaciones básicas
        if not nombre:
            messages.error(request, "El nombre del producto es obligatorio.")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        if not referencia:
            messages.error(request, "La referencia del producto es obligatoria.")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Validar que existe al menos una variante
        if "variantes[0][talla]" not in request.POST:
            messages.error(request, "Debe agregar mínimo una variante antes de guardar.")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Validar referencia única
        if Producto.objects.filter(referencia=referencia).exists():
            messages.error(request, "La referencia ya existe. Use una referencia única.")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Procesar categoría
        categoria = None
        if categoria_id:
            try:
                categoria = Categoria.objects.get(id=categoria_id)
            except Categoria.DoesNotExist:
                messages.error(request, "La categoría seleccionada no existe.")
                return render(request, 'admin/inventario/agregar_producto.html', context)

        # Procesar precio
        try:
            precio_decimal = parse_precio(precio_str)
            if precio_decimal < Decimal('0.00'):
                raise ValueError("El precio no puede ser negativo")
        except ValueError as e:
            messages.error(request, f"Error en el precio: {str(e)}")
            return render(request, 'admin/inventario/agregar_producto.html', context)

        # Validar imagen
        if imagen:
            if not imagen.content_type.startswith('image/'):
                messages.error(request, "El archivo debe ser una imagen válida.")
                return render(request, 'admin/inventario/agregar_producto.html', context)
            
            if imagen.size > 5 * 1024 * 1024:  # 5MB
                messages.error(request, "La imagen no debe superar los 5MB.")
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
        variantes_errors = []
        
        while True:
            talla_id = request.POST.get(f"variantes[{index}][talla]")
            color_id = request.POST.get(f"variantes[{index}][color]")
            stock = request.POST.get(f"variantes[{index}][stock]", '0')
            
            if talla_id is None:
                break
                
            try:
                talla_obj = Talla.objects.get(pk=talla_id)
                color_obj = Color.objects.get(pk=color_id)
                
                # Verificar si ya existe esta combinación
                if VarianteProducto.objects.filter(
                    producto=producto, 
                    talla=talla_obj, 
                    color=color_obj
                ).exists():
                    variantes_errors.append(f"La variante {talla_obj.talla} - {color_obj.color} ya existe")
                    index += 1
                    continue
                
                VarianteProducto.objects.create(
                    producto=producto,
                    talla=talla_obj,
                    color=color_obj,
                    stock=int(stock) if stock else 0,
                )
                variantes_guardadas += 1
                
            except (Talla.DoesNotExist, Color.DoesNotExist) as e:
                variantes_errors.append(f"Variante {index+1}: Talla o color no válido")
            except ValueError as e:
                variantes_errors.append(f"Variante {index+1}: Stock inválido")
            except Exception as e:
                variantes_errors.append(f"Variante {index+1}: {str(e)}")
            
            index += 1

        # Mostrar errores de variantes
        for error in variantes_errors:
            messages.warning(request, error)

        if variantes_guardadas > 0:
            messages.success(request, f"Producto agregado correctamente con {variantes_guardadas} variante(s).")
            return redirect('listar_productos_inventario')
        else:
            messages.error(request, "No se pudieron guardar las variantes del producto.")
            try:
                producto.delete()
            except Exception as e:
                messages.error(request, f"Error al eliminar producto sin variantes: {str(e)}")
            return render(request, 'admin/inventario/agregar_producto.html', context)

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
        try:
            # Obtener los datos del formulario
            nombre = request.POST.get("nombre", "").strip()
            referencia = request.POST.get("referencia", "").strip()
            
            # Validar campos obligatorios
            if not nombre:
                messages.error(request, "El nombre del producto es obligatorio.")
                return render(request, "admin/inventario/editar_producto.html", context)

            if not referencia:
                messages.error(request, "La referencia del producto es obligatoria.")
                return render(request, "admin/inventario/editar_producto.html", context)

            # Validar referencia única (excluyendo el producto actual)
            if referencia != producto.referencia:
                if Producto.objects.filter(referencia=referencia).exclude(idproducto=producto.idproducto).exists():
                    messages.error(request, "La referencia ya existe. Use una referencia única.")
                    return render(request, "admin/inventario/editar_producto.html", context)

            producto.nombre = nombre
            producto.referencia = referencia
            
            # Procesar categoría
            categoria_id = request.POST.get("categoria")
            if categoria_id:
                try:
                    producto.categoria = Categoria.objects.get(id=categoria_id)
                except Categoria.DoesNotExist:
                    messages.error(request, "La categoría seleccionada no existe.")
                    return render(request, "admin/inventario/editar_producto.html", context)
            else:
                producto.categoria = None
            
            # Procesar precio
            precio_str = request.POST.get("precio", "0").strip()
            try:
                precio_decimal = parse_precio(precio_str)
                if precio_decimal < Decimal('0.00'):
                    raise ValueError("El precio no puede ser negativo")
                producto.precio = precio_decimal
            except ValueError as e:
                messages.error(request, f"Error en el precio: {str(e)}")
                return render(request, "admin/inventario/editar_producto.html", context)
            
            producto.descripcion = request.POST.get("descripcion", "")
            producto.estado = request.POST.get("estado", "Activo")

            # Manejar la imagen
            imagen = request.FILES.get("imagen")
            if imagen:
                if not imagen.content_type.startswith('image/'):
                    messages.error(request, "El archivo debe ser una imagen válida.")
                    return render(request, "admin/inventario/editar_producto.html", context)
                
                if imagen.size > 5 * 1024 * 1024:
                    messages.error(request, "La imagen no debe superar los 5MB.")
                    return render(request, "admin/inventario/editar_producto.html", context)
                
                producto.imagen = imagen

            producto.save()
            
            # ===== PROCESAR VARIANTES ELIMINADAS =====
            variantes_eliminadas = request.POST.getlist('variantes_eliminadas[]')
            for variante_id in variantes_eliminadas:
                try:
                    variante = VarianteProducto.objects.get(idvariante=variante_id, producto=producto)
                    nombre_variante = f"{variante.talla.talla} - {variante.color.color}"
                    variante.delete()
                    messages.info(request, f"Variante eliminada: {nombre_variante}")
                except VarianteProducto.DoesNotExist:
                    messages.warning(request, f"Variante con ID {variante_id} no encontrada para eliminar.")
                except Exception as e:
                    messages.warning(request, f"Error al eliminar variante {variante_id}: {str(e)}")

            # ===== PROCESAR VARIANTES EDITADAS =====
            variantes_editadas = {}
            for key, value in request.POST.items():
                if key.startswith('variantes_editadas['):
                    parts = key.split('[')
                    if len(parts) >= 3:
                        variante_id = parts[1].replace(']', '')
                        campo = parts[2].replace(']', '')
                        
                        if variante_id not in variantes_editadas:
                            variantes_editadas[variante_id] = {}
                        variantes_editadas[variante_id][campo] = value

            for variante_id, datos in variantes_editadas.items():
                try:
                    variante = VarianteProducto.objects.get(idvariante=variante_id, producto=producto)
                    
                    if 'stock' in datos:
                        try:
                            variante.stock = int(datos['stock'])
                        except ValueError:
                            messages.warning(request, f"Stock inválido para variante {variante_id}")
                    
                    # Manejar imagen base64 si existe
                    if 'imagen' in datos and datos['imagen']:
                        try:
                            image_data = procesar_imagen_base64(datos['imagen'], f"variante_{variante_id}")
                            if image_data:
                                variante.imagen = image_data
                        except ValueError as e:
                            messages.warning(request, f"Error en imagen de variante {variante_id}: {str(e)}")
                    
                    variante.save()
                    
                except VarianteProducto.DoesNotExist:
                    messages.warning(request, f"Variante con ID {variante_id} no encontrada.")
                except Exception as e:
                    messages.warning(request, f"Error al actualizar variante {variante_id}: {str(e)}")

            # ===== PROCESAR NUEVAS VARIANTES =====
            variantes_nuevas = {}
            for key, value in request.POST.items():
                if key.startswith('variantes_nuevas['):
                    parts = key.split('[')
                    if len(parts) >= 3:
                        index = parts[1].replace(']', '')
                        campo = parts[2].replace(']', '')
                        
                        if index not in variantes_nuevas:
                            variantes_nuevas[index] = {}
                        variantes_nuevas[index][campo] = value

            for index, datos in variantes_nuevas.items():
                talla_id = datos.get('talla')
                color_id = datos.get('color')
                stock = datos.get('stock', '0')
                imagen_base64 = datos.get('imagen', '')
                
                if talla_id and color_id:
                    try:
                        talla_obj = Talla.objects.get(id=talla_id)
                        color_obj = Color.objects.get(id=color_id)
                        
                        # Verificar si ya existe esta variante
                        existe = VarianteProducto.objects.filter(
                            producto=producto,
                            talla=talla_obj,
                            color=color_obj
                        ).exists()
                        
                        if not existe:
                            variante_nueva = VarianteProducto(
                                producto=producto,
                                talla=talla_obj,
                                color=color_obj,
                                stock=int(stock) if stock else 0
                            )
                            
                            # Manejar imagen base64 si existe
                            if imagen_base64:
                                try:
                                    image_data = procesar_imagen_base64(imagen_base64, "variante_nueva")
                                    if image_data:
                                        variante_nueva.imagen = image_data
                                except ValueError as e:
                                    messages.warning(request, f"Error en imagen de nueva variante: {str(e)}")
                            
                            variante_nueva.save()
                            messages.info(request, f"Nueva variante agregada: {talla_obj.talla} - {color_obj.color}")
                        else:
                            messages.warning(request, f"La variante {talla_obj.talla} - {color_obj.color} ya existe.")
                            
                    except Talla.DoesNotExist:
                        messages.error(request, f"Talla con ID {talla_id} no encontrada.")
                    except Color.DoesNotExist:
                        messages.error(request, f"Color con ID {color_id} no encontrado.")
                    except Exception as e:
                        messages.error(request, f"Error al crear nueva variante: {str(e)}")

            # Validar que el producto tenga al menos una variante después de las operaciones
            if not VarianteProducto.objects.filter(producto=producto).exists():
                messages.error(request, "El producto debe tener al menos una variante.")
            else:
                messages.success(request, "Producto y variantes actualizados correctamente.")
                
            return redirect("editar_producto", idproducto=idproducto)
            
        except Exception as e:
            error_msg = f"Error al actualizar el producto: {str(e)}"
            messages.error(request, error_msg)
            return render(request, "admin/inventario/editar_producto.html", context)

    return render(request, "admin/inventario/editar_producto.html", context)


@login_required
def guardar_variantes(request, idproducto):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")

    producto = get_object_or_404(Producto, idproducto=idproducto)

    try:
        talla = request.POST.get("talla")
        colores = request.POST.getlist("colores[]")
        stocks = request.POST.getlist("stocks[]")
        imagenes = request.FILES.getlist("imagenes[]")

        if not talla:
            return JsonResponse({"error": "Debes seleccionar una talla"}, status=400)

        if not colores:
            return JsonResponse({"error": "Debes seleccionar al menos un color"}, status=400)

        talla_obj = Talla.objects.get(id=talla)
        variantes_creadas = 0
        errors = []

        for i, color_id in enumerate(colores):
            try:
                color_obj = Color.objects.get(id=color_id)
                stock_val = int(stocks[i]) if i < len(stocks) and stocks[i] else 0
                
                # Verificar si ya existe
                if VarianteProducto.objects.filter(
                    producto=producto,
                    talla=talla_obj,
                    color=color_obj
                ).exists():
                    errors.append(f"La variante {talla_obj.talla} - {color_obj.color} ya existe")
                    continue

                VarianteProducto.objects.create(
                    producto=producto,
                    talla=talla_obj,
                    color=color_obj,
                    stock=stock_val,
                    imagen=imagenes[i] if i < len(imagenes) else None
                )
                variantes_creadas += 1
                
            except Color.DoesNotExist:
                errors.append(f"Color con ID {color_id} no encontrado")
            except ValueError:
                errors.append(f"Stock inválido para color {color_id}")
            except Exception as e:
                errors.append(f"Error al crear variante: {str(e)}")

        if errors:
            return JsonResponse({
                "success": variantes_creadas > 0,
                "message": f"Se crearon {variantes_creadas} variantes, pero hubo {len(errors)} errores",
                "errors": errors
            }, status=207 if variantes_creadas > 0 else 400)
        else:
            return JsonResponse({
                "success": True, 
                "message": f"{variantes_creadas} variante(s) guardadas correctamente"
            })
            
    except Talla.DoesNotExist:
        return JsonResponse({"error": "La talla seleccionada no existe"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Error general: {str(e)}"}, status=500)


# ==========================================================
#                   CONFIGURACIÓN DE INVENTARIO
# ==========================================================

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


# ==========================================================
#                   GESTIÓN DE USUARIOS (ADMIN)
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
#                   GESTIÓN DE PEDIDOS (ADMIN)
# ==========================================================

def pedidos(request):
    pedidos = []
    return render(request, 'admin/pedidos/pedidos.html', {'pedidos': pedidos, 'active': 'pedidos'})


# ==========================================================
#                   GESTIÓN DE DEVOLUCIONES (ADMIN)
# ==========================================================

@permiso_requerido('devoluciones')
def devoluciones(request):
    return render(request, 'admin/devoluciones/devoluciones.html', {
        'active': 'devoluciones'
    })


# ==========================================================
#                   GESTIÓN DE PETICIONES (ADMIN)
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


# ==========================================================
#                   MERCADOPAGO HELPER
# ==========================================================

def crear_preferencia_mercadopago(items_carrito, checkout_data, total):
    """
    Crea una preferencia de pago en MercadoPago
    """
    try:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        # Construir items para MercadoPago
        items = []
        for item in items_carrito:
            items.append({
                "title": f"{item.producto.producto.nombre}",
                "description": f"Talla: {item.producto.talla.talla} - Color: {item.producto.color.color}",
                "quantity": int(item.cantidad),
                "unit_price": float(item.precio_unitario),
                "currency_id": "COP",
            })
        
        # Obtener la URL base del sitio
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
        
        # Configurar preferencia
        preference_data = {
            "items": items,
            "payer": {
                "name": checkout_data.get('nombre', ''),
                "surname": checkout_data.get('apellido', ''),
                "email": checkout_data.get('email', ''),
            },
            "back_urls": {
                "success": f"{site_url}/pago/exito/",
                "failure": f"{site_url}/pago/fallo/",
                "pending": f"{site_url}/pago/pendiente/"
            },
            "statement_descriptor": "LIHER FASHION",
            "external_reference": f"ORDEN-{int(timezone.now().timestamp())}",
        }
        
        # IMPORTANTE: Solo agregar notification_url si NO es localhost
        # En producción, descomenta estas líneas:
        # if not site_url.startswith('http://127.0.0.1') and not site_url.startswith('http://localhost'):
        #     preference_data["notification_url"] = f"{site_url}/webhook/mercadopago/"
        
        # Solo agregar teléfono si existe
        telefono = checkout_data.get('telefono', '').strip()
        if telefono:
            preference_data["payer"]["phone"] = {
                "area_code": "57",
                "number": str(telefono)
            }
        
        # Solo agregar identificación si existe
        numero_doc = checkout_data.get('numero_documento', '').strip()
        if numero_doc:
            preference_data["payer"]["identification"] = {
                "type": str(checkout_data.get('tipo_documento', 'CC')),
                "number": str(numero_doc)
            }
        
        print("=== CREANDO PREFERENCIA ===")
        print(f"Items: {len(items)}")
        print(f"Email: {checkout_data.get('email')}")
        print(f"Total: {total}")
        print(f"URL success: {preference_data['back_urls']['success']}")
        
        preference_response = sdk.preference().create(preference_data)
        
        print(f"Response status: {preference_response.get('status')}")
        
        if preference_response.get("status") == 201:
            preference = preference_response["response"]
            print(f"✅ Preferencia creada: {preference.get('id')}")
            return preference
        else:
            error_msg = preference_response.get('response', {}).get('message', 'Error desconocido')
            print(f"❌ Error en respuesta: {error_msg}")
            print(f"Respuesta completa: {preference_response}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR al crear preferencia: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@login_required
def pago_exito(request):
    """Vista de éxito del pago"""
    payment_id = request.GET.get('payment_id')
    preference_id = request.GET.get('preference_id')
    
    # Si viene de un redirect de MercadoPago, redirigir a mis pedidos
    if payment_id:
        messages.success(request, f'¡Pago exitoso! Tu pedido ha sido confirmado. ID de pago: {payment_id}')
        return redirect('mis_pedidos')
    
    messages.success(request, '¡Pago exitoso! Tu pedido ha sido confirmado.')
    return redirect('mis_pedidos')


@login_required
def pago_fallo(request):
    """Vista de fallo del pago"""
    messages.error(request, 'El pago fue rechazado. Por favor intenta con otro método de pago.')
    return redirect('pago')


@login_required
def pago_pendiente(request):
    """Vista de pago pendiente"""
    messages.info(request, 'Tu pago está pendiente de confirmación. Te notificaremos cuando se complete.')
    return redirect('mis_pedidos')
# ==========================================================
#                   WEBHOOKS MERCADOPAGO
# ==========================================================

@csrf_exempt
@require_POST
def webhook_mercadopago(request):
    """
    Webhook para recibir notificaciones de MercadoPago
    """
    try:
        # Log para debugging
        print("=" * 50)
        print("WEBHOOK MERCADOPAGO RECIBIDO")
        print("=" * 50)
        
        # Obtener datos
        data = json.loads(request.body)
        print(f"Datos recibidos: {data}")
        
        # Verificar tipo de notificación
        notification_type = data.get('type')
        
        if notification_type == 'payment':
            payment_id = data.get('data', {}).get('id')
            
            if not payment_id:
                print("No se recibió payment_id")
                return JsonResponse({'status': 'error', 'message': 'No payment_id'}, status=400)
            
            # Obtener información del pago
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)
            
            if payment_info['status'] == 200:
                payment = payment_info['response']
                external_reference = payment.get('external_reference')
                status = payment.get('status')
                status_detail = payment.get('status_detail')
                
                print(f"Payment ID: {payment_id}")
                print(f"Status: {status}")
                print(f"Status Detail: {status_detail}")
                print(f"External Reference: {external_reference}")
                
                # Aquí puedes actualizar el estado del pedido
                # basándote en el external_reference si lo guardaste
                
                if status == 'approved':
                    print("✅ Pago aprobado")
                    
                elif status == 'rejected':
                    print("❌ Pago rechazado")
                    
                elif status == 'pending':
                    print("⏳ Pago pendiente")
                    
                elif status == 'in_process':
                    print("🔄 Pago en proceso")
                
                return JsonResponse({'status': 'ok'})
            else:
                print(f"Error al obtener info del pago: {payment_info}")
                return JsonResponse({'status': 'error'}, status=400)
        
        print(f"Tipo de notificación no manejada: {notification_type}")
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        print(f"Error en webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@login_required
@require_POST
def procesar_pago_mp(request):
    """
    Procesa el pago de MercadoPago usando el SDK
    """
    try:
        data = json.loads(request.body)
        payment_data = data.get('payment_data')
        
        if not payment_data:
            return JsonResponse({
                'success': False,
                'message': 'Datos de pago no válidos'
            }, status=400)
        
        # Inicializar SDK
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        # Obtener datos de sesión
        checkout_data = request.session.get('checkout_data', {})
        carrito = obtener_o_crear_carrito(request)
        items_carrito = ItemCarrito.objects.filter(carrito=carrito)
        
        # Calcular total
        subtotal = sum(item.total_precio for item in items_carrito)
        descuento = Decimal('0.00')
        costo_envio = Decimal(checkout_data.get('costo_envio', '12000.00'))
        total = subtotal - descuento + costo_envio
        
        # Preparar datos del pago
        payment_request = {
            "transaction_amount": float(total),
            "token": payment_data.get('token'),
            "description": f"Pedido Liher Fashion",
            "installments": int(payment_data.get('installments', 1)),
            "payment_method_id": payment_data.get('payment_method_id'),
            "issuer_id": payment_data.get('issuer_id'),
            "payer": {
                "email": checkout_data.get('email'),
                "identification": {
                    "type": checkout_data.get('tipo_documento', 'CC'),
                    "number": checkout_data.get('numero_documento', '')
                }
            },
            "external_reference": f"ORDEN-{int(timezone.now().timestamp())}",
            "statement_descriptor": "LIHER FASHION",
            "notification_url": f"{settings.SITE_URL}/webhook/mercadopago/"
        }
        
        # Crear pago
        payment_response = sdk.payment().create(payment_request)
        payment = payment_response["response"]
        
        print(f"Respuesta de pago: {payment}")
        
        if payment.get("status") == "approved":
            # Pago aprobado - crear pedido
            with transaction.atomic():
                pedido = Pedidos.objects.create(
                    cliente=request.user.email,
                    fecha=timezone.now(),
                    estado_pedido='Confirmado',
                    metodo_pago='MercadoPago',
                    total=total,
                    estado_pago='Aprobado'
                )
                
                # Crear items y reducir stock
                for item in items_carrito:
                    if item.producto.stock < item.cantidad:
                        raise ValueError(f"Stock insuficiente para {item.producto.producto.nombre}")
                    
                    PedidoItem.objects.create(
                        pedido=pedido,
                        producto=item.producto.producto,
                        variante=item.producto,
                        cantidad=item.cantidad,
                        precio_unitario=item.precio_unitario,
                        subtotal=item.total_precio
                    )
                    
                    item.producto.stock -= item.cantidad
                    item.producto.save()
                
                # Marcar carrito como completado
                carrito.completado = True
                carrito.save()
                
                # Limpiar sesión
                if 'checkout_data' in request.session:
                    del request.session['checkout_data']
                if 'carrito_items' in request.session:
                    del request.session['carrito_items']
            
            return JsonResponse({
                'success': True,
                'message': 'Pago aprobado',
                'redirect_url': reverse('confirmacion_pedido', args=[pedido.idpedido])
            })
            
        elif payment.get("status") == "in_process":
            # Pago pendiente
            return JsonResponse({
                'success': True,
                'message': 'Pago en proceso',
                'redirect_url': reverse('pago_pendiente')
            })
        else:
            # Pago rechazado
            return JsonResponse({
                'success': False,
                'message': payment.get('status_detail', 'Pago rechazado')
            }, status=400)
            
    except Exception as e:
        print(f"Error al procesar pago: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error al procesar el pago: {str(e)}'
        }, status=500)
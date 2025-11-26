#validaciones y formularios.

from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Usuarios, Producto, VarianteProducto, Categoria, Color, Talla
import re

User = get_user_model()

# ==========================
# FORMULARIOS PARA USUARIOS
# ==========================

class UsuarioRegistroForm(UserCreationForm):
    first_name = forms.CharField(required=False, label="Nombre")
    last_name  = forms.CharField(required=False, label="Apellido")
    phone      = forms.CharField(required=False, label="Teléfono")
    
    class Meta:
        model = Usuarios
        fields = ('email', 'password1', 'password2', 'first_name', 'last_name', 'phone')

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        if Usuarios.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def clean_password1(self):
        p = self.cleaned_data.get('password1')
        if p != p.strip():
            raise ValidationError("La contraseña no puede tener espacios al inicio o final.")
        if len(p) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

        comunes = ["12345678", "password", "qwerty", "123456789", "abc123", "111111", "123123"]
        if p.lower() in comunes:
            raise ValidationError("La contraseña es demasiado común.")

        if re.search(r'1234|2345|3456|4567|5678|abcd|bcde|cdef|defg', p, re.I):
            raise ValidationError("La contraseña no puede contener secuencias fáciles.")

        if re.match(r'^(.)\1{5,}$', p):
            raise ValidationError("La contraseña no puede contener caracteres repetidos.")

        if not re.search(r'[A-Z]', p) or not re.search(r'[a-z]', p) or not re.search(r'[0-9]', p) or not re.search(r'[!@#$%^&*]', p):
            raise ValidationError("La contraseña debe incluir mayúscula, minúscula, número y símbolo (!@#$%^&*).")

        return p

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")

        # ⚡ Validar teléfono solo si el rol es administrador
        rol = self.data.get("rol")  # viene del payload de tu fetch
        phone = cleaned_data.get("phone", "").strip()

        if rol == "administrador":
            if not phone:
                self.add_error("phone", "El teléfono es obligatorio para administradores.")
            elif not re.match(r'^\d{7,15}$', phone):
                self.add_error("phone", "El teléfono debe contener solo números y tener entre 7 y 15 dígitos.")




class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Correo electrónico'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}))
    

class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Incluimos usuarios inactivos también"""
        active_users = Usuarios._default_manager.filter(email__iexact=email)
        return (u for u in active_users if u.has_usable_password())

    def save(self, *args, **kwargs):
        """
        Al resetear la contraseña, si el usuario estaba inactivo,
        lo activamos automáticamente.
        """
        result = super().save(*args, **kwargs)
        email = self.cleaned_data["email"]
        users = Usuarios._default_manager.filter(email__iexact=email)

        for user in users:
            if not user.is_active and user.has_usable_password():
                user.is_active = True
                user.save(update_fields=["is_active"])
        return result


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        fields = ['first_name', 'last_name', 'email', 'phone', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Apellido'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Teléfono'}),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'phone': 'Teléfono',
            'is_active': 'Activo',
            'is_staff': 'Es Staff',
            'is_superuser': 'Es Superusuario',
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'referencia',
            'categoria',
            'precio',
            'descripcion',
            'imagen',
            'estado'
        ]
        labels = {
            'nombre': 'Nombre del producto',
            'referencia': 'Referencia',
            'categoria': 'Categoría',
            'precio': 'Precio',
            'descripcion': 'Descripción',
            'imagen': 'Imagen',
            'estado': 'Estado',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

# --------------------------------------
    # VALIDACIÓN NOMBRE
    # --------------------------------------
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()

        # Longitud
        if len(nombre) < 3 or len(nombre) > 150:
            raise forms.ValidationError("El nombre debe tener entre 3 y 150 caracteres.")

        if "  " in nombre:
            raise forms.ValidationError("No se permiten dobles espacios.")

        patron = r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+( [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$'
        if not re.match(patron, nombre):
            raise forms.ValidationError("El nombre solo puede contener letras y un espacio entre palabras.")

        # evitar "aaaaaa", "bbbbbb", etc
        for palabra in nombre.split(" "):
            if re.fullmatch(r'([A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\1{2,}', palabra):
                raise forms.ValidationError("El nombre no puede ser una secuencia repetida.")

        return nombre

    # --------------------------------------
    # VALIDACIÓN REFERENCIA
    # --------------------------------------
    def clean_referencia(self):
        referencia = self.cleaned_data.get('referencia', '').strip()

        if len(referencia) < 3 or len(referencia) > 10:
            raise forms.ValidationError("La referencia debe tener entre 3 y 10 caracteres.")

        if not re.match(r'^[A-Za-z0-9]+$', referencia):
            raise forms.ValidationError("La referencia solo permite letras y números (sin espacios).")

        if " " in referencia:
            raise forms.ValidationError("La referencia no puede contener espacios.")

        # referencia ÚNICA
        qs = Producto.objects.filter(referencia=referencia)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ya existe un producto con esta referencia.")

        return referencia

    # --------------------------------------
    # VALIDACIÓN PRECIO
    # --------------------------------------
def clean_precio(self):
    precio_raw = self.cleaned_data.get('precio')

    if precio_raw in (None, ''):
        raise forms.ValidationError("El precio es obligatorio.")

    # Lo convertimos a string (por si viene como int/Decimal)
    precio_str = str(precio_raw).strip()

    # No permitir espacios internos o externos
    if " " in precio_str:
        raise forms.ValidationError("El precio no puede contener espacios.")

    # Debe ser solo dígitos
    if not re.fullmatch(r'^[0-9]+$', precio_str):
        raise forms.ValidationError("El precio solo puede contener números.")

    # Longitud: 3 a 8 caracteres/dígitos
    if len(precio_str) < 3 or len(precio_str) > 8:
        raise forms.ValidationError("El precio debe tener entre 3 y 8 dígitos.")

    # Si quieres guardar como entero:
    try:
        return int(precio_str)
    except ValueError:
        raise forms.ValidationError("Precio inválido.")


   # --------------------------------------
    # VALIDACIÓN descripcion
    # --------------------------------------

def clean_descripcion(self):
    descripcion = self.cleaned_data.get('descripcion', '')
    descripcion = descripcion.strip()

    if descripcion == '':
        raise forms.ValidationError("La descripción es obligatoria.")

    if len(descripcion) < 5 or len(descripcion) > 500:
        raise forms.ValidationError("La descripción debe tener entre 5 y 500 caracteres.")

    # Solo letras (incluye tildes y ñ) y solo un espacio entre palabras
    patron = r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?: [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$'
    if not re.match(patron, descripcion):
        raise forms.ValidationError("La descripción solo puede contener letras y un solo espacio entre palabras.")

    # (Opcional) evitar palabras formadas por una misma letra repetida
    for palabra in descripcion.split(' '):
        if re.fullmatch(r'([A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\1{2,}', palabra):
            raise forms.ValidationError("La descripción contiene palabras inválidas (letra repetida).")

    return descripcion

    # --------------------------------------
    # VALIDACIÓN IMAGEN
    # --------------------------------------
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')

        if not imagen:
            raise forms.ValidationError("Debe subir una imagen principal.")

        if not imagen.content_type.startswith("image/"):
            raise forms.ValidationError("El archivo debe ser una imagen.")

        if imagen.size > 5 * 1024 * 1024:
            raise forms.ValidationError("La imagen no debe superar los 5MB.")

        return imagen
    



class VarianteProductoForm(forms.ModelForm):
    class Meta:
        model = VarianteProducto
        fields = [
            'producto',
            'talla',
            'color',
            'imagen',
            'stock',
        ]
        labels = {
            'producto': 'Producto',
            'talla': 'Talla',
            'color': 'Color',
            'imagen': 'Imagen de la variante',
            'stock': 'Stock disponible',
        }
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'talla': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }




from django import forms
from .models import Categoria, Color, Talla

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['categoria']

    def clean_categoria(self):
        data = self.cleaned_data['categoria']
        if Categoria.objects.filter(categoria__iexact=data).exists():
            raise forms.ValidationError("Esta categoría ya existe")
        return data

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['color']

    def clean_color(self):
        data = self.cleaned_data['color']
        if Color.objects.filter(color__iexact=data).exists():
            raise forms.ValidationError("Este color ya existe")
        return data

class TallaForm(forms.ModelForm):
    class Meta:
        model = Talla
        fields = ['talla']

    def clean_talla(self):
        data = self.cleaned_data['talla']
        if Talla.objects.filter(talla__iexact=data).exists():
            raise forms.ValidationError("Esta talla ya existe")
        return data


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


#validaciones y formularios.

from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Usuarios, VarianteProducto, Identificacion, Envio, Categoria, Color, Talla
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
        rol = self.data.get("rol", "").strip()  # viene del payload de tu fetch
        phone = cleaned_data.get("phone", "").strip()

        if rol == "administrador":
            if not phone:
                self.add_error("phone", "El teléfono es obligatorio para administradores.")
            elif not re.match(r'^\d{7,15}$', phone):
                self.add_error("phone", "El teléfono debe contener solo números y tener entre 7 y 15 dígitos.")
        return cleaned_data




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


# ==========================
# FORMULARIOS PARA INVENTARIO
# ==========================

class InventarioForm(forms.ModelForm):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('agotado', 'Agotado'),
        ('stock_bajo', 'Stock Bajo'),
        ('inactivo', 'Inactivo'),
    ]
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = VarianteProducto
        fields = ['producto', 'talla', 'color', 'precio', 'stock', 'imagen']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'talla': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'producto': 'Producto',
            'talla': 'Talla',
            'color': 'Color',
            'precio': 'Precio',
            'stock': 'Stock',
            'imagen': 'Imagen de la Variante',
        }


# ==========================
# FORMULARIO DE IDENTIFICACIÓN
# ==========================

class IdentificacionForm(forms.ModelForm):
    class Meta:
        model = Identificacion
        fields = [
            'email', 'nombre', 'apellido', 'tipo_documento', 
            'numero_documento', 'celular', 'acepta_terminos', 
            'autoriza_datos', 'autoriza_publicidad'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico',
                'required': 'required'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre',
                'required': 'required'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido',
                'required': 'required'
            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': 'required'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número documento',
                'required': 'required'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Celular',
                'required': 'required'
            }),
        }
        labels = {
            'email': 'Correo electrónico',
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'tipo_documento': 'Tipo de documento',
            'numero_documento': 'Número de documento',
            'celular': 'Celular',
            'acepta_terminos': 'Acepto términos y condiciones',
            'autoriza_datos': 'Autorizo tratamiento de mis datos personales',
            'autoriza_publicidad': 'Autorizo tratamiento de mis datos para el envío de publicidad',
        }

# ==========================
# FORMULARIO DE ENVÍO       
# ==========================

class EnvioForm(forms.ModelForm):
    # Datos de Colombia
    DEPARTAMENTOS = [
        ('', 'Seleccione una opción'),
        ('Antioquia', 'Antioquia'),
        ('Atlántico', 'Atlántico'),
        ('Bolívar', 'Bolívar'),
        ('Boyacá', 'Boyacá'),
        ('Caldas', 'Caldas'),
        ('Caquetá', 'Caquetá'),
        ('Cauca', 'Cauca'),
        ('Cesar', 'Cesar'),
        ('Chocó', 'Chocó'),
        ('Córdoba', 'Córdoba'),
        ('Cundinamarca', 'Cundinamarca'),
        ('Huila', 'Huila'),
        ('La Guajira', 'La Guajira'),
        ('Magdalena', 'Magdalena'),
        ('Meta', 'Meta'),
        ('Nariño', 'Nariño'),
        ('Norte de Santander', 'Norte de Santander'),
        ('Quindío', 'Quindío'),
        ('Risaralda', 'Risaralda'),
        ('Santander', 'Santander'),
        ('Sucre', 'Sucre'),
        ('Tolima', 'Tolima'),
        ('Valle del Cauca', 'Valle del Cauca'),
    ]
    
    departamento = forms.ChoiceField(
        choices=DEPARTAMENTOS,
        widget=forms.Select(attrs={'class': 'form-control', 'required': True})
    )
    
    municipio = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el municipio',
            'required': True
        })
    )
    
    class Meta:
        model = Envio
        fields = [
            'departamento', 'municipio', 'tipo_direccion', 
            'calle', 'letra', 'numero', 'adicional', 
            'barrio', 'piso_apartamento', 'nombre_receptor',
            'telefono_receptor', 'empresa_envio'
        ]
        widgets = {
            'tipo_direccion': forms.Select(attrs={'class': 'form-control'}),
            'calle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 65'}),
            'letra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: C'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '113'}),
            'adicional': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Laureles'}),
            'piso_apartamento': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Edificio 3 Apto 103'
            }),
            'nombre_receptor': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Juliana'
            }),
            'telefono_receptor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '3001234567'
            }),
            'empresa_envio': forms.RadioSelect(),
        }
        labels = {
            'departamento': 'Departamento',
            'municipio': 'Municipio o ciudad capital',
            'tipo_direccion': 'Tipo de dirección',
            'calle': 'Calle',
            'letra': 'Letra',
            'numero': 'Número',
            'adicional': 'Adicional',
            'barrio': 'Barrio',
            'piso_apartamento': 'Piso/Apartamento/Torre/Edificio',
            'nombre_receptor': 'Nombre de la persona que recibe',
            'telefono_receptor': 'Teléfono del receptor',
            'empresa_envio': 'Empresa de envío',
        }
    
    def clean_calle(self):
        calle = self.cleaned_data.get('calle', '').strip()
        if not calle:
            raise forms.ValidationError('La calle es obligatoria')
        return calle
    
    def clean_numero(self):
        numero = self.cleaned_data.get('numero', '').strip()
        if not numero:
            raise forms.ValidationError('El número es obligatorio')
        return numero
    
    def clean_telefono_receptor(self):
        telefono = self.cleaned_data.get('telefono_receptor', '').strip()
        # Solo números, 10 dígitos para Colombia
        if telefono and not telefono.isdigit():
            raise forms.ValidationError('El teléfono debe contener solo números')
        if telefono and len(telefono) != 10:
            raise forms.ValidationError('El teléfono debe tener 10 dígitos')
        return telefono


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
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuarios, Catalogo, Categoria, Color, Envios, Identificacion, Inventario, Pedidos, Talla

class UsuariosAdmin(BaseUserAdmin):
    model = Usuarios
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permisos', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


admin.site.register(Usuarios, UsuariosAdmin)


admin.site.register(Catalogo)
admin.site.register(Categoria)
admin.site.register(Color)
admin.site.register(Envios)
admin.site.register(Identificacion)
admin.site.register(Inventario)
admin.site.register(Pedidos)
admin.site.register(Talla)

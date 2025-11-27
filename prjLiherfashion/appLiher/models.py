from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# ==========================
# MODELOS DE AUTENTICACIÓN DJANGO (TABLAS BASE)
# ==========================

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Usuarios', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


# ==========================
# MODELOS DE NEGOCIO (TIENDA)
# ==========================

class Categoria(models.Model):
    categoria = models.CharField(max_length=50, unique=True, primary_key=True)

    class Meta:
        managed = True
        db_table = 'categoria'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.categoria


class Color(models.Model):
    color = models.CharField(max_length=100, unique=True, primary_key=True)

    class Meta:
        managed = True
        db_table = 'color'
        verbose_name = 'Color'
        verbose_name_plural = 'Colores'

    def __str__(self):
        return self.color


class Talla(models.Model):
    talla = models.CharField(max_length=50, unique=True, primary_key=True)

    class Meta:
        managed = True
        db_table = 'talla'
        verbose_name = 'Talla'
        verbose_name_plural = 'Tallas'

    def __str__(self):
        return self.talla


class Producto(models.Model):
    idproducto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    referencia = models.CharField(max_length=10, unique=True, null=True, blank=True)
    categoria = models.ForeignKey(
        'Categoria', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True, max_length=255)
    estado = models.CharField(max_length=20, choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], default='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'producto'

    def __str__(self):
        return self.nombre


class VarianteProducto(models.Model):
    idvariante = models.AutoField(primary_key=True)
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='variantes'
    )
    talla = models.ForeignKey('Talla', on_delete=models.PROTECT)
    color = models.ForeignKey('Color', on_delete=models.PROTECT)
    imagen = models.ImageField(upload_to='productos/variantes/', null=True, blank=True, max_length=255)
    stock = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'variante_producto'
        unique_together = ('producto', 'talla', 'color')

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla} - {self.color}"


# ==========================
# USUARIOS Y AUTENTICACIÓN
# ==========================

class UsuariosManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Usuarios(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UsuariosManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        managed = True
        db_table = 'usuarios'

    def __str__(self):
        return self.email


class Permiso(models.Model):
    usuario = models.OneToOneField('Usuarios', on_delete=models.CASCADE, related_name='permisos')
    inicio = models.BooleanField(default=False)
    inventario = models.BooleanField(default=False)
    catalogo = models.BooleanField(default=False)
    pedidos = models.BooleanField(default=False)
    usuarios = models.BooleanField(default=False)
    devoluciones = models.BooleanField(default=False)
    peticiones = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'permisos_usuarios_admin'

    def __str__(self):
        return f"Permisos de {self.usuario.email}"


# ==========================
# CARRITO DE COMPRAS
# ==========================

class Carrito(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuario del Carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'carrito'

    def __str__(self):
        return f"Carrito de {self.usuario.email if self.usuario else 'invitado'} - ID: {self.id}"

    @property
    def total_precio_carrito(self):
        return sum(item.total_precio for item in self.items_carrito.all())

    @property
    def total_items_carrito(self):
        return sum(item.cantidad for item in self.items_carrito.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='items_carrito',
        verbose_name='Carrito de Compras'
    )
    producto = models.ForeignKey(
        VarianteProducto,
        on_delete=models.CASCADE,
        verbose_name='Variante del Producto'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        managed = True
        db_table = 'item_carrito'
        verbose_name = 'Ítem del Carrito'
        verbose_name_plural = 'Ítems del Carrito'
    
    def __str__(self):
        nombre_producto = getattr(self.producto.catalogo, 'nombre', 'Producto sin nombre')
        return f"{self.cantidad} x {nombre_producto}"

    @property
    def total_precio(self):
        return self.cantidad * self.precio_unitario


# ==========================
# INVENTARIO Y ENTRADAS
# ==========================

class EntradaInventario(models.Model):
    identrada = models.AutoField(primary_key=True)
    idinventario_fk = models.ForeignKey(VarianteProducto, on_delete=models.DO_NOTHING, db_column='idInventario_fk', verbose_name='Variante a Surtir')
    cantidad_ingreso = models.PositiveIntegerField(verbose_name='Cantidad a Ingresar')
    fecha_entrada = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Entrada')

    class Meta:
        managed = True
        db_table = 'entradas_inventario'


# ==========================
# PETICIONES DE PRODUCTOS
# ==========================

class PeticionProducto(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    producto = models.ForeignKey(VarianteProducto, on_delete=models.CASCADE)
    cantidad_solicitada = models.PositiveIntegerField(default=1)
    fecha_peticion = models.DateTimeField(auto_now_add=True)
    atendida = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'peticiones_producto'
        verbose_name = 'Petición de Producto'
        verbose_name_plural = 'Peticiones de Productos'

    def __str__(self):
        return f"{self.usuario.email} - {self.producto.catalogo.nombre} - Cant: {self.cantidad_solicitada}"


# ==========================
# IDENTIFICACIÓN DEL CLIENTE
# ==========================

class Identificacion(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('DNI', 'DNI'),
        ('Pasaporte', 'Pasaporte'),
        ('Tarjeta de identidad', 'Tarjeta de identidad'),
        ('Cedula de ciudadania', 'Cédula de ciudadanía'),
        ('Cedula de extranjeria', 'Cédula de extranjería'),
    ]
    
    usuario = models.OneToOneField(Usuarios, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    tipo_documento = models.CharField(max_length=50, choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.CharField(max_length=20, unique=True)
    celular = models.CharField(max_length=15)
    acepta_terminos = models.BooleanField(default=False)
    autoriza_datos = models.BooleanField(default=False)
    autoriza_publicidad = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'identificacion'
        verbose_name = 'Datos de Identificación'
        verbose_name_plural = 'Datos de Identificación'

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.email}"


# ==========================
# PEDIDOS (NO MANAGED)
# ==========================

class Pedidos(models.Model):
    idpedido = models.AutoField(primary_key=True)
    cliente = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    estado_pedido = models.CharField(max_length=50)
    metodo_pago = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado_pago = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'pedidos'


# ==========================
# ENVÍOS (NO MANAGED)
# ==========================

class Envio(models.Model):
    TIPO_DIRECCION_CHOICES = [
        ('Calle', 'Calle'),
        ('Carrera', 'Carrera'),
        ('Avenida', 'Avenida'),
        ('Transversal', 'Transversal'),
        ('Diagonal', 'Diagonal'),
        ('Circular', 'Circular'),
    ]
    
    EMPRESA_ENVIO_CHOICES = [
        ('coordinadora', 'Coordinadora'),
        ('interrapidisimo', 'Interrapidísimo'),
        ('envia', 'Transportadora Envia'),
    ]
    
    # Relaciones
    usuario = models.ForeignKey(
        Usuarios, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='envios'
    )
    identificacion = models.ForeignKey(
        'Identificacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='envios'
    )
    
    # Ubicación
    departamento = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    
    # Dirección
    tipo_direccion = models.CharField(max_length=50, choices=TIPO_DIRECCION_CHOICES)
    calle = models.CharField(max_length=10)  # Ej: 65
    letra = models.CharField(max_length=5, blank=True)  # Ej: C
    numero = models.CharField(max_length=10)  # Ej: 113
    adicional = models.CharField(max_length=10, blank=True)  # Ej: 50
    barrio = models.CharField(max_length=100)
    piso_apartamento = models.CharField(max_length=100, blank=True)
    
    # Dirección completa generada
    direccion_completa = models.CharField(max_length=255, blank=True)
    
    # Receptor
    nombre_receptor = models.CharField(max_length=100)
    telefono_receptor = models.CharField(max_length=20, blank=True)
    
    # Empresa de envío
    empresa_envio = models.CharField(max_length=50, choices=EMPRESA_ENVIO_CHOICES)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        managed = True
        db_table = 'envios_detallados'
        verbose_name = 'Envío'
        verbose_name_plural = 'Envíos'
    
    def save(self, *args, **kwargs):
        # Generar dirección completa automáticamente
        self.direccion_completa = self.generar_direccion_completa()
        super().save(*args, **kwargs)
    
    def generar_direccion_completa(self):
        """Genera la dirección en formato colombiano"""
        partes = [
            self.tipo_direccion,
            self.calle,
            self.letra if self.letra else '',
            '#',
            self.numero,
            f'-{self.adicional}' if self.adicional else '',
            f', {self.barrio}',
            f', {self.piso_apartamento}' if self.piso_apartamento else ''
        ]
        return ' '.join(filter(None, partes))
    
    def __str__(self):
        return f"Envío - {self.direccion_completa}"
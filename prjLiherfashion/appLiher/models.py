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


class Inventario(models.Model):
    idinventario = models.AutoField(primary_key=True)
    categoria = models.ForeignKey('Categoria', on_delete=models.DO_NOTHING)
    color = models.ForeignKey('Color', on_delete=models.DO_NOTHING)
    talla = models.ForeignKey('Talla', on_delete=models.DO_NOTHING)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    catalogo = models.ForeignKey('Catalogo', on_delete=models.CASCADE, related_name='inventarios')

    class Meta:
        managed = True
        db_table = 'inventario'

    def __str__(self):
        return f"{self.categoria} - {self.color} - {self.talla} - ${self.precio}"



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
        db_table = 'permisos_usuarios_admin'

    def __str__(self):
        return f"Permisos de {self.usuario.email}"




class EntradaInventario(models.Model):
    identrada = models.AutoField(primary_key=True)
    idinventario_fk = models.ForeignKey(Inventario, on_delete=models.DO_NOTHING, db_column='idInventario_fk', verbose_name='Variante a Surtir')
    cantidad_ingreso = models.PositiveIntegerField(verbose_name='Cantidad a Ingresar')
    fecha_entrada = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Entrada')

    class Meta:
        managed = True
        db_table = 'entradas_inventario'


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
        Inventario,
        on_delete=models.CASCADE,
        verbose_name='Producto'
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
# MODELOS EXISTENTES (NO MANAGED)
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



class Catalogo(models.Model):
    idcatalogo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'catalogo'

    def __str__(self):
        return self.nombre



class Envios(models.Model):
    idenvios = models.AutoField(primary_key=True)
    departamentos = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    tipo_direccion = models.CharField(max_length=50)
    calle = models.CharField(max_length=50)
    letra = models.CharField(max_length=50)
    numero = models.BigIntegerField()
    barrio = models.CharField(max_length=50)
    piso = models.CharField(max_length=50)
    nombre_receptor = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'envios'


class Identificacion(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=100, unique=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    tipo_documento = models.CharField(max_length=50)
    field_documento = models.BigIntegerField()
    celular = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'identificacion'





    # ==========================
    # PETICIONES A ADMIN
    # ==========================


class PeticionProducto(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    producto = models.ForeignKey(Inventario, on_delete=models.CASCADE)
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

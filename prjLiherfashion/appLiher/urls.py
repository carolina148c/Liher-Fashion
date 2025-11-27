from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    #PÁGINAS PÚBLICAS
    path('', views.pagina_principal, name='pagina_principal'),
    path('productos/', views.vista_productos, name='vista_productos'),
    path('productos/<int:idproducto>/', views.detalle_producto, name='detalle_producto'),


    #AUTENTICACIÓN Y REGISTRO
    path('acceso/', views.acceso, name='acceso'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),
    
    # Registro y activación
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('registro/revisar/<str:email>/', views.registro_revisar_email, name='registro_revisar_email'),
    path('reenviar-activacion/<str:email>/', views.reenviar_activacion, name='reenviar_activacion'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar_cuenta'),
    
    # AJAX para autenticación
    path('login-ajax/', views.login_ajax, name='login_ajax'),
    path('registro-ajax/', views.registro_ajax, name='registro_ajax'),
    path('ajax/validar-email/', views.validar_email_ajax, name='validar_email_ajax'),


    #GESTIÓN DE CONTRASEÑAS
    path('restablecer-contrasena/', views.CustomPasswordResetView.as_view(), name='restablecer_contrasena'),
    path('correo-enviado/', views.CorreoEnviadoView.as_view(), name='correo_enviado'),
    path('reenviar-reset/', views.reenviar_reset, name='reenviar_reset'),
    path('nueva-contrasena/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='nueva_contrasena'),
    path('contrasena-actualizada/', views.CustomPasswordResetCompleteView.as_view(), name='contrasena_actualizada'),


    # CARRITO DE COMPRAS
    path('carrito/', views.carrito, name='carrito'),
    path('carrito/agregar/<int:variante_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/limpiar/', views.limpiar_carrito, name='limpiar_carrito'),


    #CHECKOUT Y PAGOS
    path('envio/', views.envio, name='envio'),
    path('pago/', views.pago, name='pago'),
    path('identificacion/', views.identificacion, name='identificacion'),


    #GESTIÓN DE USUARIO
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('mi-perfil/editar/', views.editar_perfil, name='editar_perfil'),
    
    # Direcciones de envío
    path('direcciones/', views.lista_direcciones, name='lista_direcciones'),
    path('direcciones/agregar/', views.agregar_direccion, name='agregar_direccion'),
    path('direcciones/editar/<int:pk>/', views.editar_direccion, name='editar_direccion'),
    path('direcciones/eliminar/<int:pk>/', views.eliminar_direccion, name='eliminar_direccion'),
    path('direcciones/principal/<int:pk>/', views.establecer_direccion_principal, name='establecer_direccion_principal'),
    
    # Métodos de pago
    path('metodos-pago/', views.lista_metodos_pago, name='lista_metodos_pago'),
    path('metodos-pago/agregar/', views.agregar_metodo_pago, name='agregar_metodo_pago'),
    path('metodos-pago/eliminar/<int:pk>/', views.eliminar_metodo_pago, name='eliminar_metodo_pago'),
    path('metodos-pago/principal/<int:pk>/', views.establecer_metodo_pago_principal, name='establecer_metodo_pago_principal'),
    
    # Pedidos del usuario
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('mis-pedidos/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),


    #PANEL DE ADMINISTRACIÓN
    path('panel-admin/', views.panel_admin, name='panel_admin'),


    #GESTIÓN DE INVENTARIO (ADMIN)
    path('inventario/', views.listar_productos_inventario, name='listar_productos_inventario'),
    path('inventario/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/editar/<int:idproducto>/', views.editar_producto, name='editar_producto'),
    path('catalogo/guardar-variantes/<int:idproducto>/', views.guardar_variantes, name='guardar_variantes'),

    # Configuración de inventario
    path('inventario/configuracion/', views.configuracion_inventario, name='configuracion_inventario'),
    
    # Categorías
    path('inventario/categoria/agregar/', views.agregar_categoria, name='agregar_categoria'),
    path('categoria/editar/<str:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categoria/eliminar/<str:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # Colores
    path('inventario/color/agregar/', views.agregar_color, name='agregar_color'),
    path('color/editar/<str:pk>/', views.editar_color, name='editar_color'),
    path('color/eliminar/<str:pk>/', views.eliminar_color, name='eliminar_color'),
    
    # Tallas
    path('inventario/talla/agregar/', views.agregar_talla, name='agregar_talla'),
    path('talla/editar/<str:pk>/', views.editar_talla, name='editar_talla'),
    path('talla/eliminar/<str:pk>/', views.eliminar_talla, name='eliminar_talla'),


    #GESTIÓN DE USUARIOS (ADMIN)
    path('usuarios/', views.mostrar_usuarios, name='mostrar_usuarios'),
    path('usuarios-editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/ver/<int:user_id>/', views.ver_usuario, name='ver_usuario'),
    path('usuarios/obtener/<int:id>/', views.obtener_usuario, name='obtener_usuario'),
    path('usuarios/toggle/<int:id>/', views.toggle_usuario_activo, name='toggle_usuario_activo'),


    #GESTIÓN DE PEDIDOS (ADMIN)
    path('pedidos/', views.pedidos, name='pedidos'),


    #GESTIÓN DE DEVOLUCIONES (ADMIN)
    path('devoluciones/', views.devoluciones, name='devoluciones'),


    #GESTIÓN DE PETICIONES (ADMIN)
    path('peticiones/', views.peticiones, name='peticiones'),
    path('peticiones/', views.listar_peticiones, name='listar_peticiones'),
]
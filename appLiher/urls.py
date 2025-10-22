from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # PÁGINA PRINCIPAL 
    path('', views.pagina_principal, name='pagina_principal'),

    # USUARIO / TIENDA 
    path('carrito/', views.carrito, name='carrito'),
    path('envio/', views.envio, name='envio'),
    path('pago/', views.pago, name='pago'),
    path('identificacion/', views.identificacion, name='identificacion'),
    path('vista-productos/', views.vista_productos, name='vista_productos'),
    path('devoluciones/', views.devoluciones, name='devoluciones'), 
    path('peticiones/', views.peticiones, name='peticiones'), 
    path('pedidos/', views.pedidos, name='pedidos'), 


    # LOGIN Y REGISTRO 
    path('acceso/', views.acceso, name='acceso'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),
    path('login-ajax/', views.login_ajax, name='login_ajax'),
    path('registro-ajax/', views.registro_ajax, name='registro_ajax'),


    # REGISTRO Y ACTIVACIÓN
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('registro/revisar/<str:email>/', views.registro_revisar_email, name='registro_revisar_email'),
    path('reenviar-activacion/<str:email>/', views.reenviar_activacion, name='reenviar_activacion'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar_cuenta'),
    path('ajax/validar-email/', views.validar_email_ajax, name='validar_email_ajax'),


    # CONTRASEÑA 
    path('restablecer-contrasena/', views.CustomPasswordResetView.as_view(), name='restablecer_contrasena'),
    path('correo-enviado/', views.CorreoEnviadoView.as_view(), name='correo_enviado'),
    path('reenviar-reset/', views.reenviar_reset, name='reenviar_reset'),
    path('nueva-contrasena/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='nueva_contrasena'),
    path('contrasena-actualizada/', views.CustomPasswordResetCompleteView.as_view(), name='contrasena_actualizada'),


    # ADMIN PERSONALIZADO 
    path('panel-admin/', views.panel_admin, name='panel_admin'),

    # CRUD USUARIOS 
    path('usuarios/', views.mostrar_usuarios, name='mostrar_usuarios'),
    path('usuarios-editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios-eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),


    # CRUD INVENTARIO 
    path('inventario/', views.listar_productos_tabla, name='listar_productos_tabla'),
    path('inventario-crear/', views.crear_producto, name='crear_producto'),
    path('inventario-editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('inventario-eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('inventario/variantes/tabla/', views.listar_productos_tabla, name='listar_productos_tabla'),
    path('inventario/stock/add/<int:id_catalogo>/', views.mostrar_formulario_stock, name='mostrar_formulario_stock'),
    path('inventario/stock/process/', views.procesar_entrada_stock, name='procesar_entrada_stock'),


    #CATALOGO
    path('catalogo/', views.listar_productos_catalogo, name='listar_productos_catalogo'),
    path('catalogo/agregar/', views.agregar_producto, name='agregar_producto'),
    path('inventario/movimientos/<int:id_catalogo>/', views.listar_movimientos_producto, name='listar_movimientos_producto'),


    # CARRITO
    path('anadir-al-carrito/<int:producto_id>/', views.anadir_al_carrito, name='anadir_al_carrito'),
    path('carrito/', views.carrito, name='carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),


    # PETICIONES A ADMIN
    path('peticiones/crear/<int:producto_id>/', views.crear_peticion, name='crear_peticion'),
    path('admin/peticiones/', views.listar_peticiones, name='listar_peticiones'),
]

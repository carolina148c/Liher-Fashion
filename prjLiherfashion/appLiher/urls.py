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
       path('api/producto/<int:idproducto>/detalle/', views.detalle_producto_json, name='detalle_producto_json'),



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


    # CARRITO
    path('anadir-al-carrito/<int:producto_id>/', views.anadir_al_carrito, name='anadir_al_carrito'),
    path('carrito/', views.carrito, name='carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),





    # ADMIN PERSONALIZADO 
    path('panel-admin/', views.panel_admin, name='panel_admin'),



    #INVENTARIO
    path('inventario/', views.listar_productos_inventario, name='listar_productos_inventario'),
    path('inventario/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/editar/<int:idproducto>/', views.editar_producto, name='editar_producto'),
    path('inventario/configuracion/', views.configuracion_inventario, name='configuracion_inventario'),
    path('inventario/categoria/agregar/', views.agregar_categoria, name='agregar_categoria'),
    path('inventario/color/agregar/', views.agregar_color, name='agregar_color'),
    path('inventario/talla/agregar/', views.agregar_talla, name='agregar_talla'),
    path('categoria/editar/<str:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categoria/eliminar/<str:pk>/', views.eliminar_categoria, name='eliminar_categoria'),

    path('color/editar/<str:pk>/', views.editar_color, name='editar_color'),
    path('color/eliminar/<str:pk>/', views.eliminar_color, name='eliminar_color'),

    path('talla/editar/<str:pk>/', views.editar_talla, name='editar_talla'),
    path('talla/eliminar/<str:pk>/', views.eliminar_talla, name='eliminar_talla'),




    #PEDIDOS


    # USUARIOS 
    path('usuarios/', views.mostrar_usuarios, name='mostrar_usuarios'),
    path('usuarios-editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/ver/<int:user_id>/', views.ver_usuario, name='ver_usuario'),
    path('usuarios/obtener/<int:id>/', views.obtener_usuario, name='obtener_usuario'),
    path('usuarios/toggle/<int:id>/', views.toggle_usuario_activo, name='toggle_usuario_activo'),


    # DEVOLUCIONES


    # PETICIONES
    path('peticiones/', views.listar_peticiones, name='listar_peticiones'),
    path('catalogo/guardar-variantes/<int:idproducto>/', views.guardar_variantes, name='guardar_variantes'),
]

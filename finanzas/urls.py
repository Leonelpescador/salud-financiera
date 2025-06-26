from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.login, name='login'),
    path('registro/', views.registro_publico, name='registro_publico'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/dashboard-data/', views.api_dashboard_data, name='api_dashboard_data'),
    
    # Transacciones
    path('transacciones/', views.transacciones_lista, name='transacciones_lista'),
    path('transacciones/crear/', views.transaccion_crear, name='transaccion_crear'),
    path('transacciones/<int:pk>/editar/', views.transaccion_editar, name='transaccion_editar'),
    path('transacciones/<int:pk>/eliminar/', views.transaccion_eliminar, name='transaccion_eliminar'),
    
    # Categorías
    path('categorias/', views.categorias_lista, name='categorias_lista'),
    path('categorias/crear/', views.categoria_crear, name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
    
    # Cuentas
    path('cuentas/', views.cuentas_lista, name='cuentas_lista'),
    path('cuentas/crear/', views.cuenta_crear, name='cuenta_crear'),
    path('cuentas/<int:pk>/editar/', views.cuenta_editar, name='cuenta_editar'),
    path('cuentas/<int:pk>/eliminar/', views.cuenta_eliminar, name='cuenta_eliminar'),
    
    # Tags
    path('tags/', views.tags_lista, name='tags_lista'),
    path('tags/crear/', views.tag_crear, name='tag_crear'),
    path('tags/<int:pk>/editar/', views.tag_editar, name='tag_editar'),
    path('tags/<int:pk>/eliminar/', views.tag_eliminar, name='tag_eliminar'),
    
    # Presupuestos
    path('presupuestos/', views.presupuestos_lista, name='presupuestos_lista'),
    path('presupuestos/crear/', views.presupuesto_crear, name='presupuesto_crear'),
    path('presupuestos/<int:pk>/editar/', views.presupuesto_editar, name='presupuesto_editar'),
    path('presupuestos/<int:pk>/eliminar/', views.presupuesto_eliminar, name='presupuesto_eliminar'),
    
    # Metas
    path('metas/', views.metas_lista, name='metas_lista'),
    path('metas/crear/', views.meta_crear, name='meta_crear'),
    path('metas/<int:pk>/editar/', views.meta_editar, name='meta_editar'),
    path('metas/<int:pk>/eliminar/', views.meta_eliminar, name='meta_eliminar'),
    path('metas/<int:pk>/actualizar-progreso/', views.meta_actualizar_progreso, name='meta_actualizar_progreso'),
    
    # Corte de Mes
    path('corte-mes/confirmar/', views.corte_mes_confirmar, name='corte_mes_confirmar'),
    path('corte-mes/ejecutar/', views.corte_mes_ejecutar, name='corte_mes_ejecutar'),
    path('cortes-mes/', views.cortes_mes_lista, name='cortes_mes_lista'),
    path('corte-mes/<int:pk>/detalle/', views.corte_mes_detalle, name='corte_mes_detalle'),
    
    # Gastos Compartidos (unificada)
    path('gastos-compartidos/', views.dashboard_gastos_compartidos, name='dashboard_gastos_compartidos'),
    
    # Grupos de Gastos Compartidos
    path('grupos/', views.grupos_gastos_compartidos_lista, name='grupos_gastos_compartidos_lista'),
    path('grupos/crear/', views.grupo_gastos_compartidos_crear, name='grupo_gastos_compartidos_crear'),
    path('grupos/<int:pk>/editar/', views.grupo_gastos_compartidos_editar, name='grupo_gastos_compartidos_editar'),
    path('grupos/<int:pk>/eliminar/', views.grupo_gastos_compartidos_eliminar, name='grupo_gastos_compartidos_eliminar'),
    path('grupos/<int:pk>/saldos/', views.saldos_grupo, name='saldos_grupo'),
    path('grupos/<int:pk>/miembros/', views.miembros_grupo, name='miembros_grupo'),
    
    # Gastos Compartidos
    path('gastos/', views.gastos_compartidos_lista, name='gastos_compartidos_lista'),
    path('gastos/crear/', views.gasto_compartido_crear, name='gasto_compartido_crear'),
    path('gastos/<int:pk>/editar/', views.gasto_compartido_editar, name='gasto_compartido_editar'),
    path('gastos/<int:pk>/eliminar/', views.gasto_compartido_eliminar, name='gasto_compartido_eliminar'),
    path('gastos/<int:pk>/detalle/', views.gasto_compartido_detalle, name='gasto_compartido_detalle'),
    path('gastos/historico/', views.historico_gastos_compartidos, name='historico_gastos_compartidos'),
    
    # Pagos de Gastos Compartidos
    path('pagos/<int:pk>/editar/', views.pago_gasto_compartido_editar, name='pago_gasto_compartido_editar'),
    
    # APIs para Gastos Compartidos
    path('api/grupo/<int:grupo_id>/miembros/', views.api_grupo_miembros, name='api_grupo_miembros'),
    path('api/grupo/<int:grupo_id>/crear/', views.api_crear_grupo, name='api_crear_grupo'),
    path('api/gasto/crear/', views.api_crear_gasto, name='api_crear_gasto'),
    path('api/pago/editar/', views.api_editar_pago, name='api_editar_pago'),
    
    # Configuración del Sistema
    path('configuracion/', views.configuracion, name='configuracion'),
    path('configuracion/usuarios-pendientes/', views.usuarios_pendientes, name='usuarios_pendientes'),
    path('configuracion/guardar/', views.configuracion_guardar, name='configuracion_guardar'),
    path('mi-configuracion/', views.configuracion_personal, name='configuracion_personal'),
    
    # Gestión de Usuarios
    path('usuarios/crear/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_eliminar, name='usuario_eliminar'),
    path('usuarios/<int:pk>/activar/', views.usuario_activar, name='usuario_activar'),
    path('usuarios/<int:pk>/desactivar/', views.usuario_desactivar, name='usuario_desactivar'),
    
    # Acciones del Sistema
    path('sistema/backup/', views.backup_datos, name='backup_datos'),
    path('sistema/limpiar/', views.limpiar_datos, name='limpiar_datos'),
    path('sistema/exportar/', views.exportar_datos, name='exportar_datos'),
    path('sistema/importar/', views.importar_datos, name='importar_datos'),
    
    # Notificaciones
    path('notificaciones/', views.lista_notificaciones, name='lista_notificaciones'),
    path('notificaciones/leer/<int:pk>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/leer_todas/', views.marcar_todas_notificaciones_leidas, name='marcar_todas_notificaciones_leidas'),
    
    # APIs
    path('api/cuentas-usuario/<int:user_id>/', views.api_cuentas_usuario, name='api_cuentas_usuario'),
    path('api/grupo-info/<int:grupo_id>/', views.api_grupo_info, name='api_grupo_info'),
]
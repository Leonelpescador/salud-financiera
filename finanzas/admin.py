from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Cuenta, Tag, Transaccion, Presupuesto, Meta, ConfiguracionUsuario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'icono', 'tipo', 'usuario', 'activa', 'color_display', 'fecha_creacion']
    list_filter = ['tipo', 'activa', 'usuario', 'fecha_creacion']
    search_fields = ['nombre', 'usuario__username']
    list_editable = ['activa']
    ordering = ['nombre']
    
    def color_display(self, obj):
        return format_html(
            '<div style="background-color: {}; width: 20px; height: 20px; border-radius: 50%;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_cuenta', 'saldo_actual', 'usuario', 'activa', 'icono', 'fecha_creacion']
    list_filter = ['tipo_cuenta', 'activa', 'usuario', 'fecha_creacion']
    search_fields = ['nombre', 'usuario__username']
    list_editable = ['activa']
    ordering = ['nombre']
    readonly_fields = ['saldo_actual']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo_cuenta', 'usuario', 'activa')
        }),
        ('Saldo', {
            'fields': ('saldo_inicial', 'saldo_actual')
        }),
        ('Personalización', {
            'fields': ('icono', 'color')
        }),
        ('Tarjeta de Crédito', {
            'fields': ('fecha_cierre', 'fecha_vencimiento', 'limite_credito'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'color', 'usuario', 'fecha_creacion']
    list_filter = ['fecha_creacion']
    search_fields = ['nombre', 'usuario__username']
    ordering = ['nombre']
    
    def color_display(self, obj):
        return format_html(
            '<div style="background-color: {}; width: 20px; height: 20px; border-radius: 50%;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'tipo', 'categoria', 'cuenta', 'usuario', 'fecha']
    list_filter = ['tipo', 'categoria', 'cuenta', 'fecha', 'es_recurrente']
    search_fields = ['descripcion', 'usuario__username', 'categoria__nombre', 'cuenta__nombre']
    date_hierarchy = 'fecha'
    ordering = ['-fecha', '-fecha_creacion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'monto', 'fecha', 'tipo', 'descripcion')
        }),
        ('Clasificación', {
            'fields': ('categoria', 'cuenta', 'tags')
        }),
        ('Recurrencia', {
            'fields': ('es_recurrente', 'frecuencia_recurrencia', 'fecha_fin_recurrencia'),
            'classes': ('collapse',)
        }),
        ('Transferencia', {
            'fields': ('cuenta_destino',),
            'classes': ('collapse',)
        }),
        ('Adjuntos', {
            'fields': ('imagen_recibo',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('categoria', 'cuenta', 'usuario')

@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'monto_objetivo', 'monto_gastado', 'porcentaje_completado', 'periodo', 'estado', 'usuario']
    list_filter = ['periodo', 'estado', 'fecha_creacion']
    search_fields = ['nombre', 'usuario__username']
    list_editable = ['estado']
    ordering = ['-fecha_creacion']
    readonly_fields = ['monto_gastado', 'porcentaje_completado', 'monto_restante', 'esta_sobrepasado', 'fecha_creacion', 'fecha_modificacion']
    filter_horizontal = ['categorias']
    
    def porcentaje_completado(self, obj):
        return f"{obj.porcentaje_completado:.1f}%"
    porcentaje_completado.short_description = 'Progreso'

@admin.register(Meta)
class MetaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'monto_objetivo', 'monto_actual', 'porcentaje_completado', 'dias_restantes', 'estado', 'usuario']
    list_filter = ['tipo', 'estado', 'fecha_creacion']
    search_fields = ['nombre', 'usuario__username', 'cuenta__nombre']
    list_editable = ['estado']
    ordering = ['-fecha_creacion']
    readonly_fields = ['monto_actual', 'porcentaje_completado', 'monto_restante', 'dias_restantes', 'esta_completada', 'esta_vencida', 'fecha_creacion', 'fecha_modificacion']
    
    def porcentaje_completado(self, obj):
        return f"{obj.porcentaje_completado:.1f}%"
    porcentaje_completado.short_description = 'Progreso'
    
    def dias_restantes(self, obj):
        return obj.dias_restantes
    dias_restantes.short_description = 'Días Restantes'

@admin.register(ConfiguracionUsuario)
class ConfiguracionUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'moneda_principal', 'notificaciones_activas', 'recordatorios_pago', 'fecha_creacion']
    list_filter = ['notificaciones_activas', 'recordatorios_pago', 'fecha_creacion']
    search_fields = ['usuario__username']
    ordering = ['usuario__username']

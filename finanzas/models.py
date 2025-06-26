from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
        ('ambos', 'Ambos'),
    ]
    
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=50, default='📊')  # Emoji como icono
    color = models.CharField(max_length=7, default='#3498db')  # Color en hex
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='gasto')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categorias')
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['nombre', 'usuario']
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"

class Cuenta(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('cuenta_bancaria', 'Cuenta Bancaria'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('billetera_virtual', 'Billetera Virtual'),
        ('cuenta_inversion', 'Cuenta de Inversión'),
        ('otro', 'Otro'),
    ]
    
    MONEDA_CHOICES = [
        ('ARS', 'Peso Argentino'),
        ('USD', 'Dólar Estadounidense'),
        ('EUR', 'Euro'),
        ('BRL', 'Real Brasileño'),
        ('CLP', 'Peso Chileno'),
        ('COP', 'Peso Colombiano'),
        ('MXN', 'Peso Mexicano'),
        ('PEN', 'Sol Peruano'),
        ('UYU', 'Peso Uruguayo'),
        ('VES', 'Bolívar Venezolano'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CUENTA_CHOICES, default='efectivo')
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default='ARS')
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    icono = models.CharField(max_length=50, default='💳')
    color = models.CharField(max_length=7, default='#2ecc71')
    descripcion = models.TextField(blank=True, null=True)
    institucion_financiera = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cuentas')
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Campos específicos para tarjetas de crédito
    fecha_cierre = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"
    
    @property
    def saldo(self):
        """Propiedad para compatibilidad con las plantillas"""
        return self.saldo_actual
    
    @property
    def tipo(self):
        """Propiedad para compatibilidad con las plantillas"""
        return self.tipo_cuenta
    
    def actualizar_saldo(self):
        """Calcula el saldo actual basado en las transacciones"""
        from .models import Transaccion
        
        ingresos = Transaccion.objects.filter(
            cuenta=self,
            tipo='ingreso'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        
        gastos = Transaccion.objects.filter(
            cuenta=self,
            tipo='gasto'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        
        self.saldo_actual = self.saldo_inicial + ingresos - gastos
        self.save()

class Tag(models.Model):
    nombre = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#95a5a6')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['nombre', 'usuario']
        ordering = ['nombre']
    
    def __str__(self):
        return f"#{self.nombre} ({self.usuario.username})"

class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
        ('transferencia', 'Transferencia'),
    ]
    
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha = models.DateField()
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='transacciones')
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='transacciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transacciones')
    tags = models.ManyToManyField(Tag, blank=True, related_name='transacciones')
    
    # Campos adicionales
    es_recurrente = models.BooleanField(default=False)
    frecuencia_recurrencia = models.CharField(max_length=20, blank=True, null=True)  # 'mensual', 'semanal', etc.
    fecha_fin_recurrencia = models.DateField(null=True, blank=True)
    
    # Para transferencias
    cuenta_destino = models.ForeignKey(Cuenta, on_delete=models.CASCADE, null=True, blank=True, related_name='transferencias_recibidas')
    
    # Adjuntos
    imagen_recibo = models.ImageField(upload_to='recibos/', null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha', '-fecha_creacion']
    
    def __str__(self):
        return f"{self.descripcion} - ${self.monto} ({self.fecha})"
    
    def save(self, *args, **kwargs):
        # Si es una transferencia, crear la transacción correspondiente
        if self.tipo == 'transferencia' and self.cuenta_destino:
            super().save(*args, **kwargs)
            
            # Crear la transacción de destino si no existe
            if not Transaccion.objects.filter(
                fecha=self.fecha,
                monto=self.monto,
                tipo='ingreso',
                descripcion=f"Transferencia desde {self.cuenta.nombre}",
                cuenta=self.cuenta_destino,
                usuario=self.usuario
            ).exists():
                Transaccion.objects.create(
                    monto=self.monto,
                    fecha=self.fecha,
                    tipo='ingreso',
                    descripcion=f"Transferencia desde {self.cuenta.nombre}",
                    categoria=self.categoria,
                    cuenta=self.cuenta_destino,
                    usuario=self.usuario,
                    tags=self.tags.all()
                )
        else:
            super().save(*args, **kwargs)
        
        # Actualizar saldos de las cuentas
        self.cuenta.actualizar_saldo()
        if self.cuenta_destino:
            self.cuenta_destino.actualizar_saldo()
    
    def delete(self, *args, **kwargs):
        # Actualizar saldos antes de eliminar
        cuenta_original = self.cuenta
        cuenta_destino = self.cuenta_destino
        
        super().delete(*args, **kwargs)
        
        cuenta_original.actualizar_saldo()
        if cuenta_destino:
            cuenta_destino.actualizar_saldo()

class Presupuesto(models.Model):
    PERIODO_CHOICES = [
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('pausado', 'Pausado'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    monto_objetivo = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    monto_gastado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    periodo = models.CharField(max_length=15, choices=PERIODO_CHOICES, default='mensual')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='activo')
    
    # Relaciones
    categorias = models.ManyToManyField(Categoria, related_name='presupuestos')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presupuestos')
    
    # Configuración
    notificar_al_80 = models.BooleanField(default=True)
    notificar_al_100 = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#3498db')
    icono = models.CharField(max_length=50, default='💰')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - ${self.monto_objetivo} ({self.usuario.username})"
    
    @property
    def porcentaje_completado(self):
        """Calcula el porcentaje de gasto del presupuesto"""
        if self.monto_objetivo == 0:
            return 0
        return (self.monto_gastado / self.monto_objetivo) * 100
    
    @property
    def monto_restante(self):
        """Calcula el monto restante del presupuesto"""
        return max(0, self.monto_objetivo - self.monto_gastado)
    
    @property
    def esta_sobrepasado(self):
        """Verifica si el presupuesto está sobrepasado"""
        return self.monto_gastado > self.monto_objetivo
    
    def actualizar_gasto(self):
        """Actualiza el monto gastado basado en las transacciones"""
        from django.utils import timezone
        from datetime import date
        
        # Obtener transacciones de gasto en el período del presupuesto
        transacciones = Transaccion.objects.filter(
            usuario=self.usuario,
            tipo='gasto',
            fecha__gte=self.fecha_inicio,
            fecha__lte=self.fecha_fin,
            categoria__in=self.categorias.all()
        )
        
        self.monto_gastado = transacciones.aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0')
        self.save()

class Meta(models.Model):
    TIPO_CHOICES = [
        ('ahorro', 'Ahorro'),
        ('inversion', 'Inversión'),
        ('deuda', 'Pago de Deuda'),
        ('compra', 'Compra Específica'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('pausada', 'Pausada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='ahorro')
    monto_objetivo = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    monto_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_objetivo = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='activa')
    
    # Relaciones
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='metas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas')
    
    # Configuración
    notificar_al_80 = models.BooleanField(default=True)
    notificar_al_100 = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#e74c3c')
    icono = models.CharField(max_length=50, default='🎯')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - ${self.monto_objetivo} ({self.usuario.username})"
    
    @property
    def porcentaje_completado(self):
        """Calcula el porcentaje de progreso de la meta"""
        if self.monto_objetivo == 0:
            return 0
        return min(100, (self.monto_actual / self.monto_objetivo) * 100)
    
    @property
    def monto_restante(self):
        """Calcula el monto restante para completar la meta"""
        return max(0, self.monto_objetivo - self.monto_actual)
    
    @property
    def dias_restantes(self):
        """Calcula los días restantes hasta la fecha objetivo"""
        from django.utils import timezone
        from datetime import date
        
        hoy = date.today()
        if self.fecha_objetivo > hoy:
            return (self.fecha_objetivo - hoy).days
        return 0
    
    @property
    def esta_completada(self):
        """Verifica si la meta está completada"""
        return self.monto_actual >= self.monto_objetivo
    
    @property
    def esta_vencida(self):
        """Verifica si la meta está vencida"""
        from django.utils import timezone
        from datetime import date
        
        return self.fecha_objetivo < date.today() and not self.esta_completada

# Modelo para configuraciones del usuario
class ConfiguracionUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuracion')
    moneda_principal = models.CharField(max_length=3, default='ARS')
    zona_horaria = models.CharField(max_length=50, default='America/Argentina/Buenos_Aires')
    notificaciones_activas = models.BooleanField(default=True)
    recordatorios_pago = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Configuración de {self.usuario.username}"

class CorteMes(models.Model):
    """Modelo para registrar los cortes mensuales de finanzas"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cortes_mes')
    fecha_corte = models.DateField()  # Fecha del corte (último día del mes)
    mes_cortado = models.IntegerField()  # Mes que se cortó (1-12)
    año_cortado = models.IntegerField()  # Año que se cortó
    
    # Totales del mes
    total_ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_gastos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_mes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Saldos de cuentas al momento del corte
    saldos_cuentas = models.JSONField(default=dict)  # {cuenta_id: saldo}
    
    # Configuración
    mantener_saldos = models.BooleanField(default=True)  # Si se mantienen los saldos a favor
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'mes_cortado', 'año_cortado']
        ordering = ['-fecha_corte']
    
    def __str__(self):
        return f"Corte {self.mes_cortado}/{self.año_cortado} - {self.usuario.username}"
    
    @property
    def mes_nombre(self):
        """Retorna el nombre del mes"""
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return meses.get(self.mes_cortado, 'Desconocido')

class GrupoGastosCompartidos(models.Model):
    """Modelo para grupos de gastos compartidos (ej: casa, departamento, etc.)"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    icono = models.CharField(max_length=50, default='🏠')
    color = models.CharField(max_length=7, default='#3498db')
    
    # Usuarios que pertenecen al grupo
    miembros = models.ManyToManyField(User, related_name='grupos_gastos_compartidos')
    
    # Usuario que creó el grupo (administrador)
    creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grupos_creados')
    
    # Configuración del grupo
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} (Creado por {self.creador.username})"
    
    @property
    def total_gastos_mes_actual(self):
        """Calcula el total de gastos compartidos del mes actual"""
        from datetime import date
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        
        return GastoCompartido.objects.filter(
            grupo=self,
            fecha__gte=inicio_mes
        ).aggregate(total=models.Sum('monto_total'))['total'] or Decimal('0')
    
    @property
    def cantidad_miembros(self):
        """Retorna la cantidad de miembros en el grupo"""
        return self.miembros.count()

class GastoCompartido(models.Model):
    """Modelo para gastos compartidos entre usuarios"""
    TIPO_CHOICES = [
        ('alquiler', 'Alquiler'),
        ('servicios', 'Servicios (Gas, Agua, Luz)'),
        ('internet', 'Internet/TV'),
        ('limpieza', 'Limpieza'),
        ('comida', 'Comida/Comestibles'),
        ('transporte', 'Transporte'),
        ('mantenimiento', 'Mantenimiento'),
        ('otros', 'Otros'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Información básica del gasto
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='otros')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    
    # Relaciones
    grupo = models.ForeignKey(GrupoGastosCompartidos, on_delete=models.CASCADE, related_name='gastos_compartidos')
    pagado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gastos_pagados', null=True, blank=True)
    cuenta_pago = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='gastos_compartidos_pagados', null=True, blank=True)
    
    # Archivos adjuntos
    imagen_recibo = models.ImageField(upload_to='gastos_compartidos/', null=True, blank=True)
    
    # Metadatos
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha', '-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - ${self.monto_total} ({self.grupo.nombre})"
    
    @property
    def monto_por_persona(self):
        """Calcula el monto que debe pagar cada persona"""
        cantidad_miembros = self.grupo.cantidad_miembros
        if cantidad_miembros > 0:
            return self.monto_total / cantidad_miembros
        return self.monto_total
    
    @property
    def esta_vencido(self):
        """Verifica si el gasto está vencido"""
        if self.fecha_vencimiento:
            from datetime import date
            return date.today() > self.fecha_vencimiento and self.estado == 'pendiente'
        return False
    
    @property
    def dias_restantes(self):
        """Calcula los días restantes para el vencimiento"""
        if self.fecha_vencimiento:
            from datetime import date
            dias = (self.fecha_vencimiento - date.today()).days
            return max(0, dias)
        return None
    
    def actualizar_estado_general(self):
        """Actualiza el estado general del gasto compartido basado en los pagos de los miembros"""
        # Calcula el total pagado por todos los miembros
        total_pagado = self.pagos_miembros.aggregate(
            total=Sum('monto_pagado')
        )['total'] or Decimal('0')
        
        # Determina el nuevo estado
        if total_pagado >= self.monto_total:
            self.estado = 'pagado'
        elif self.esta_vencido:
            self.estado = 'vencido'
        else:
            self.estado = 'pendiente'
        
        # Guarda solo el campo estado para evitar recursión
        self.save(update_fields=['estado'])
    
    def save(self, *args, **kwargs):
        """Sobrescribe save para actualizar automáticamente el estado si está vencido"""
        # Si el gasto está vencido y está pendiente, marcarlo como vencido
        if self.esta_vencido and self.estado == 'pendiente':
            self.estado = 'vencido'
        
        super().save(*args, **kwargs)

class PagoGastoCompartido(models.Model):
    """Modelo para registrar los pagos individuales de cada miembro"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('parcial', 'Pago Parcial'),
        ('cancelado', 'Cancelado'),
    ]
    
    gasto_compartido = models.ForeignKey(GastoCompartido, on_delete=models.CASCADE, related_name='pagos_miembros')
    miembro = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagos_gastos_compartidos')
    
    # Monto que debe pagar este miembro
    monto_debido = models.DecimalField(max_digits=12, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_pago = models.DateField(null=True, blank=True)
    
    # Estado del pago
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    
    # Notas adicionales
    notas = models.TextField(blank=True, null=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['gasto_compartido', 'miembro']
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.miembro.username} - ${self.monto_pagado}/{self.monto_debido} ({self.gasto_compartido.titulo})"
    
    @property
    def monto_pendiente(self):
        """Calcula el monto pendiente de pago"""
        return self.monto_debido - self.monto_pagado
    
    @property
    def porcentaje_pagado(self):
        """Calcula el porcentaje pagado"""
        if self.monto_debido > 0:
            return (self.monto_pagado / self.monto_debido) * 100
        return 0
    
    def actualizar_estado(self):
        """Actualiza el estado basado en el monto pagado"""
        if self.monto_pagado >= self.monto_debido:
            self.estado = 'pagado'
        elif self.monto_pagado > 0:
            self.estado = 'parcial'
        else:
            self.estado = 'pendiente'
        # No llamamos a save() aquí para evitar recursión infinita
    
    def save(self, *args, **kwargs):
        """Sobrescribe save para actualizar automáticamente el estado"""
        # Actualiza el estado antes de guardar
        self.actualizar_estado()
        
        # Guarda el pago
        super().save(*args, **kwargs)
        
        # Después de guardar, actualiza el estado general del gasto compartido
        self.gasto_compartido.actualizar_estado_general()

class Notificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.CharField(max_length=255)
    url_destino = models.URLField(blank=True, null=True, help_text="URL a la que redirige la notificación al hacer clic.")
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje[:50]}..."

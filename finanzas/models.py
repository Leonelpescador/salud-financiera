from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

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
    
    nombre = models.CharField(max_length=100)
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CUENTA_CHOICES, default='efectivo')
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    icono = models.CharField(max_length=50, default='💳')
    color = models.CharField(max_length=7, default='#2ecc71')
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

# 🔧 Manual Técnico - Salud Financiera

## 📋 Descripción del Proyecto

**Salud Financiera** es una aplicación web desarrollada en Django 5.2.3 que permite la gestión integral de finanzas personales. El proyecto está estructurado de manera modular y escalable, siguiendo las mejores prácticas de Django.

---

## 🏗️ Arquitectura del Proyecto

### Estructura de Directorios
```
salud_financiera/
├── finanzas/                    # Aplicación principal
│   ├── models.py               # Modelos de datos
│   ├── views.py                # Vistas y lógica de negocio
│   ├── forms.py                # Formularios
│   ├── urls.py                 # Configuración de URLs
│   ├── admin.py                # Configuración del admin
│   ├── migrations/             # Migraciones de base de datos
│   └── templates/              # Plantillas HTML
│       ├── base/               # Plantillas base
│       ├── dashboard/          # Dashboard
│       ├── transacciones/      # Gestión de transacciones
│       ├── categorias/         # Gestión de categorías
│       ├── cuentas/            # Gestión de cuentas
│       ├── tags/               # Gestión de tags
│       ├── presupuestos/       # Gestión de presupuestos
│       └── metas/              # Gestión de metas
├── salud_financiera/           # Configuración del proyecto
│   ├── settings.py             # Configuración general
│   ├── urls.py                 # URLs principales
│   └── wsgi.py                 # Configuración WSGI
├── manage.py                   # Script de gestión Django
└── db.sqlite3                  # Base de datos SQLite
```

---

## 🗄️ Modelos de Datos

### 1. Categoria
```python
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=50, default='📊')
    color = models.CharField(max_length=7, default='#3498db')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
```

**Propósito**: Clasificar transacciones por tipo (ingreso/gasto) y usuario.

### 2. Cuenta
```python
class Cuenta(models.Model):
    nombre = models.CharField(max_length=100)
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CUENTA_CHOICES)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    # Campos específicos para tarjetas de crédito
    fecha_cierre = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, null=True)
```

**Propósito**: Gestionar diferentes tipos de cuentas financieras del usuario.

### 3. Tag
```python
class Tag(models.Model):
    nombre = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#95a5a6')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
```

**Propósito**: Etiquetar transacciones para mejor organización.

### 4. Transaccion
```python
class Transaccion(models.Model):
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField()
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)
    # Campos adicionales
    es_recurrente = models.BooleanField(default=False)
    cuenta_destino = models.ForeignKey(Cuenta, null=True, blank=True)
    imagen_recibo = models.ImageField(upload_to='recibos/', null=True)
```

**Propósito**: Registrar todos los movimientos financieros del usuario.

### 5. Presupuesto
```python
class Presupuesto(models.Model):
    nombre = models.CharField(max_length=100)
    monto_objetivo = models.DecimalField(max_digits=12, decimal_places=2)
    monto_gastado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    periodo = models.CharField(max_length=15, choices=PERIODO_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES)
    categorias = models.ManyToManyField(Categoria)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
```

**Propósito**: Controlar gastos por categoría en períodos específicos.

### 6. Meta
```python
class Meta(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    monto_objetivo = models.DecimalField(max_digits=12, decimal_places=2)
    monto_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_objetivo = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
```

**Propósito**: Establecer y seguir objetivos financieros personales.

---

## 🎯 Vistas y Lógica de Negocio

### Estructura de Vistas

#### 1. Autenticación
- `login()`: Vista de inicio de sesión
- `logout_view()`: Cerrar sesión
- `@login_required`: Decorador para proteger vistas

#### 2. Dashboard
- `dashboard()`: Vista principal con resumen financiero
- `api_dashboard_data()`: API para datos del dashboard en JSON

#### 3. CRUD Transacciones
- `transacciones_lista()`: Listar con filtros
- `transaccion_crear()`: Crear nueva transacción
- `transaccion_editar()`: Editar transacción existente
- `transaccion_eliminar()`: Eliminar con confirmación

#### 4. CRUD Categorías
- `categorias_lista()`: Listar categorías del usuario
- `categoria_crear()`: Crear nueva categoría
- `categoria_editar()`: Editar categoría
- `categoria_eliminar()`: Eliminar categoría

#### 5. CRUD Cuentas
- `cuentas_lista()`: Listar cuentas del usuario
- `cuenta_crear()`: Crear nueva cuenta
- `cuenta_editar()`: Editar cuenta
- `cuenta_eliminar()`: Eliminar cuenta

#### 6. CRUD Tags
- `tags_lista()`: Listar tags del usuario
- `tag_crear()`: Crear nuevo tag
- `tag_editar()`: Editar tag
- `tag_eliminar()`: Eliminar tag

#### 7. CRUD Presupuestos
- `presupuestos_lista()`: Listar presupuestos
- `presupuesto_crear()`: Crear presupuesto
- `presupuesto_editar()`: Editar presupuesto
- `presupuesto_eliminar()`: Eliminar presupuesto

#### 8. CRUD Metas
- `metas_lista()`: Listar metas
- `meta_crear()`: Crear meta
- `meta_editar()`: Editar meta
- `meta_eliminar()`: Eliminar meta
- `meta_actualizar_progreso()`: Actualizar progreso de meta

---

## 📝 Formularios

### Formularios Principales

#### 1. TransaccionForm
- Validación de montos positivos
- Filtros por usuario para categorías y cuentas
- Manejo de transferencias entre cuentas

#### 2. CategoriaForm
- Validación de nombres únicos por usuario
- Selector de colores con preview
- Tipos de categoría (ingreso/gasto/ambos)

#### 3. CuentaForm
- Diferentes tipos de cuenta
- Campos específicos para tarjetas de crédito
- Validación de saldos iniciales

#### 4. TagForm
- Nombres únicos por usuario
- Selector de colores
- Descripción opcional

#### 5. PresupuestoForm
- Selección múltiple de categorías
- Validación de fechas
- Configuración de notificaciones

#### 6. MetaForm
- Tipos de meta predefinidos
- Validación de fechas objetivo
- Selección de cuenta asociada

---

## 🔗 Configuración de URLs

### Estructura de URLs
```python
urlpatterns = [
    # Autenticación
    path('', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/dashboard-data/', views.api_dashboard_data, name='api_dashboard_data'),
    
    # CRUD Transacciones
    path('transacciones/', views.transacciones_lista, name='transacciones_lista'),
    path('transacciones/crear/', views.transaccion_crear, name='transaccion_crear'),
    path('transacciones/<int:pk>/editar/', views.transaccion_editar, name='transaccion_editar'),
    path('transacciones/<int:pk>/eliminar/', views.transaccion_eliminar, name='transaccion_eliminar'),
    
    # CRUD Categorías, Cuentas, Tags, Presupuestos, Metas...
]
```

---

## 🎨 Sistema de Plantillas

### Estructura de Plantillas

#### 1. Base Template (`base/base.html`)
- Layout principal con sidebar
- Sistema de navegación
- Mensajes flash
- Responsive design

#### 2. Plantillas por Módulo
- **Lista**: Tabla con acciones CRUD
- **Formulario**: Formularios con validación
- **Eliminar**: Confirmación de eliminación

#### 3. Características de Diseño
- CSS Grid y Flexbox
- Diseño responsivo
- Animaciones CSS
- Iconos emoji
- Paleta de colores consistente

---

## 🔐 Seguridad

### Medidas Implementadas

#### 1. Autenticación
- Sistema de login personalizado
- Decorador `@login_required` en todas las vistas
- Redirección a login para usuarios no autenticados

#### 2. Autorización
- Filtrado por usuario en todos los modelos
- `get_object_or_404` con filtro de usuario
- Validación de propiedad de datos

#### 3. Validación de Formularios
- Validación del lado del servidor
- Mensajes de error personalizados
- Sanitización de datos

#### 4. CSRF Protection
- Tokens CSRF en todos los formularios
- Protección contra ataques CSRF

---

## 📊 Funcionalidades Avanzadas

### 1. Cálculos Automáticos
```python
def actualizar_saldo(self):
    """Calcula el saldo actual basado en las transacciones"""
    ingresos = Transaccion.objects.filter(
        cuenta=self, tipo='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    gastos = Transaccion.objects.filter(
        cuenta=self, tipo='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    self.saldo_actual = self.saldo_inicial + ingresos - gastos
    self.save()
```

### 2. Transferencias Automáticas
```python
def save(self, *args, **kwargs):
    if self.tipo == 'transferencia' and self.cuenta_destino:
        # Crear transacción de destino automáticamente
        Transaccion.objects.create(
            monto=self.monto,
            fecha=self.fecha,
            tipo='ingreso',
            descripcion=f"Transferencia desde {self.cuenta.nombre}",
            categoria=self.categoria,
            cuenta=self.cuenta_destino,
            usuario=self.usuario
        )
```

### 3. API para Dashboard
```python
def api_dashboard_data(request):
    """API para obtener datos del dashboard en formato JSON"""
    mes_actual = date.today().replace(day=1)
    transacciones_mes = Transaccion.objects.filter(
        usuario=request.user,
        fecha__gte=mes_actual
    )
    
    data = {
        'ingresos_mes': float(ingresos_mes),
        'gastos_mes': float(gastos_mes),
        'balance_mes': float(ingresos_mes - gastos_mes),
        'gastos_por_categoria': gastos_por_categoria,
    }
    
    return JsonResponse(data)
```

---

## 🚀 Despliegue y Configuración

### Requisitos del Sistema
- Python 3.8+
- Django 5.2.3
- SQLite (desarrollo) / PostgreSQL (producción)
- Pillow (para manejo de imágenes)

### Instalación
```bash
# Clonar repositorio
git clone <repository-url>
cd salud_financiera

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### Configuración de Producción
1. Cambiar `DEBUG = False` en settings.py
2. Configurar `ALLOWED_HOSTS`
3. Configurar base de datos PostgreSQL
4. Configurar archivos estáticos
5. Configurar HTTPS
6. Configurar backup automático

---

## 🔧 Mantenimiento

### Tareas Regulares
1. **Backup de Base de Datos**: Diario
2. **Actualización de Dependencias**: Mensual
3. **Revisión de Logs**: Semanal
4. **Optimización de Consultas**: Según necesidad

### Monitoreo
- Logs de errores
- Rendimiento de consultas
- Uso de recursos
- Actividad de usuarios

---

## 📈 Escalabilidad

### Consideraciones Futuras
1. **Cache**: Implementar Redis para cache
2. **API REST**: Crear API completa
3. **Notificaciones**: Sistema de notificaciones push
4. **Reportes**: Generación de reportes PDF
5. **Múltiples Monedas**: Soporte para diferentes monedas
6. **Sincronización**: Sincronización con bancos

### Optimizaciones
1. **Índices de Base de Datos**: Para consultas frecuentes
2. **Paginación**: Para listas grandes
3. **Lazy Loading**: Para imágenes y datos pesados
4. **CDN**: Para archivos estáticos

---

*Este manual técnico proporciona una visión completa de la arquitectura y funcionamiento interno de la aplicación Salud Financiera. Para más detalles, consulta el código fuente y la documentación de Django.* 
# Sistema de Permisos - Salud Financiera

## 🔐 Descripción General

El sistema de Salud Financiera implementa un sistema de permisos jerárquico que controla el acceso a diferentes funcionalidades del sistema.

## 👥 Tipos de Usuarios

### 1. **Usuario Normal**
- **Permisos**: Acceso básico a funcionalidades personales
- **Características**:
  - Gestionar sus propias transacciones
  - Gestionar sus propias cuentas y categorías
  - Configurar su configuración personal
  - Ver su dashboard personal

### 2. **Usuario Staff** (`is_staff=True`)
- **Permisos**: Acceso administrativo limitado
- **Características**:
  - Todas las funcionalidades de usuario normal
  - Acceso a la configuración del sistema
  - Gestión de usuarios (crear, editar, eliminar)
  - Ver estadísticas del sistema
  - Acceso al panel de administración de Django

### 3. **Superusuario** (`is_superuser=True`)
- **Permisos**: Acceso completo al sistema
- **Características**:
  - Todas las funcionalidades de staff
  - Acceso completo a todas las funciones
  - No puede ser eliminado ni desactivado
  - Control total del sistema

## 🛡️ Protecciones Implementadas

### Decorador `@staff_required`
```python
@login_required
@staff_required
def configuracion(request):
    # Solo usuarios staff o superusuarios pueden acceder
    pass
```

### Verificaciones en Vistas
- **Eliminación de superusuarios**: No permitida
- **Desactivación de superusuarios**: No permitida
- **Acceso a configuración del sistema**: Solo staff/superusuarios

### Interfaz Adaptativa
- **Menú dinámico**: Se muestra configuración del sistema solo a usuarios autorizados
- **Página de acceso denegado**: Información clara sobre permisos requeridos

## 🚀 Comandos de Gestión

### Crear Administrador
```bash
python manage.py crear_admin username email password
```

### Crear Superusuario
```bash
python manage.py crear_admin username email password --superuser
```

### Crear Superusuario con Django
```bash
python manage.py createsuperuser
```

## 📋 Funcionalidades por Tipo de Usuario

| Funcionalidad | Usuario Normal | Staff | Superusuario |
|---------------|----------------|-------|--------------|
| Dashboard personal | ✅ | ✅ | ✅ |
| Transacciones propias | ✅ | ✅ | ✅ |
| Cuentas propias | ✅ | ✅ | ✅ |
| Categorías propias | ✅ | ✅ | ✅ |
| Mi configuración | ✅ | ✅ | ✅ |
| Configuración del sistema | ❌ | ✅ | ✅ |
| Gestión de usuarios | ❌ | ✅ | ✅ |
| Estadísticas del sistema | ❌ | ✅ | ✅ |
| Acciones del sistema | ❌ | ✅ | ✅ |
| Panel de administración Django | ❌ | ✅ | ✅ |

## 🔧 Configuración de Permisos

### Para Usuarios Existentes

#### Convertir a Staff
```python
# En el shell de Django
from django.contrib.auth.models import User
user = User.objects.get(username='nombre_usuario')
user.is_staff = True
user.save()
```

#### Convertir a Superusuario
```python
# En el shell de Django
from django.contrib.auth.models import User
user = User.objects.get(username='nombre_usuario')
user.is_staff = True
user.is_superuser = True
user.save()
```

### Verificar Permisos
```python
# En una vista o template
if user.is_staff or user.is_superuser:
    # Mostrar funcionalidades administrativas
    pass
```

## 🎨 Interfaz de Usuario

### Menú de Navegación
- **Usuarios normales**: Solo ven "Mi Configuración"
- **Staff/Superusuarios**: Ven "Configuración del Sistema" y "Mi Configuración"

### Página de Acceso Denegado
- Explicación clara de por qué se deniega el acceso
- Estado actual del usuario (staff, superusuario)
- Alternativas disponibles
- Información de contacto para solicitar permisos

## 🔒 Seguridad

### Protecciones Implementadas
1. **Decoradores de vistas**: Verificación automática de permisos
2. **Verificaciones en templates**: Menús dinámicos según permisos
3. **Validaciones en formularios**: Prevención de acciones no autorizadas
4. **Mensajes informativos**: Comunicación clara sobre restricciones

### Buenas Prácticas
- Siempre verificar permisos antes de mostrar funcionalidades
- Usar decoradores para proteger vistas sensibles
- Proporcionar alternativas útiles cuando se deniega acceso
- Mantener logs de acciones administrativas

## 📞 Soporte

Si necesitas acceso administrativo o tienes problemas con los permisos:

1. Contacta con el administrador del sistema
2. Proporciona tu nombre de usuario y justificación
3. El administrador puede otorgar permisos usando los comandos de gestión

## 🔄 Actualizaciones

Este sistema de permisos es extensible y puede ser modificado según las necesidades del proyecto:

- Agregar nuevos niveles de permisos
- Crear permisos específicos por funcionalidad
- Implementar grupos de usuarios
- Agregar auditoría de acciones administrativas 
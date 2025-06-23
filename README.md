# 💰 Salud Financiera - Gestión de Finanzas Personales

[![Django](https://img.shields.io/badge/Django-5.2.3-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Descripción

**Salud Financiera** es una aplicación web desarrollada en Django que te permite gestionar tus finanzas personales de manera integral. La aplicación incluye funcionalidades para controlar ingresos, gastos, crear presupuestos, establecer metas financieras y mantener un seguimiento detallado de tu situación económica.

## ✨ Características Principales

### 💰 Gestión de Transacciones
- ✅ Registro de ingresos y gastos
- ✅ Transferencias entre cuentas
- ✅ Categorización de transacciones
- ✅ Sistema de etiquetas (tags)
- ✅ Adjuntar imágenes de recibos
- ✅ Transacciones recurrentes

### 📂 Organización
- 🏷️ **Categorías**: Clasifica transacciones por tipo
- 💳 **Cuentas**: Gestiona múltiples cuentas bancarias
- 🏷️ **Tags**: Etiqueta transacciones para mejor organización
- 🔍 **Filtros**: Búsqueda y filtrado avanzado

### 📊 Dashboard Interactivo
- 📈 Gráficos de gastos por categoría
- 💰 Resumen mensual de ingresos y gastos
- 🎯 Progreso de metas financieras
- 📋 Estado de presupuestos activos

### 📋 Presupuestos
- 🎯 Control de gastos por categoría
- 📅 Períodos personalizables (mensual, trimestral, etc.)
- ⚠️ Alertas al alcanzar límites
- 📊 Seguimiento visual del progreso

### 🎯 Metas Financieras
- 💰 Diferentes tipos de metas (ahorro, inversión, deuda, etc.)
- 📅 Fechas objetivo con seguimiento
- 📊 Progreso visual con porcentajes
- 🔄 Actualización manual del progreso

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git (opcional)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd salud_financiera
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   
   # En Windows:
   venv\Scripts\activate
   
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar base de datos**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

6. **Ejecutar servidor**
   ```bash
   python manage.py runserver
   ```

7. **Acceder a la aplicación**
   - URL: `http://localhost:8000/finanzas/`
   - Usar las credenciales del superusuario creado

## 📖 Documentación

### Manuales Disponibles
- 📖 **[Manual de Usuario](MANUAL_SALUD_FINANCIERA.md)** - Guía completa para usuarios finales
- 🔧 **[Manual Técnico](MANUAL_TECNICO.md)** - Documentación para desarrolladores

### Estructura del Proyecto
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
├── manage.py                   # Script de gestión Django
└── db.sqlite3                  # Base de datos SQLite
```

## 🎯 Funcionalidades por Módulo

### Módulo 1: Gestión Básica
- ✅ **Transacciones**: CRUD completo con filtros
- ✅ **Categorías**: Organización personalizada
- ✅ **Cuentas**: Múltiples tipos de cuenta
- ✅ **Tags**: Sistema de etiquetas

### Módulo 2: Presupuestos y Metas
- ✅ **Presupuestos**: Control de gastos por categoría
- ✅ **Metas**: Objetivos financieros personales
- ✅ **Dashboard**: Vista general con gráficos
- ✅ **Reportes**: Análisis de datos

## 🛡️ Seguridad

### Medidas Implementadas
- 🔐 Autenticación de usuarios
- 🛡️ Protección CSRF
- 🔒 Autorización por usuario
- ✅ Validación de formularios
- 🚫 Filtrado de datos por usuario

## 📱 Diseño Responsivo

### Características
- 📱 **Móvil**: Optimizado para smartphones
- 📱 **Tablet**: Adaptado para tablets
- 💻 **Desktop**: Experiencia completa
- 🎨 **UI Moderna**: Diseño limpio y profesional

## 🔧 Tecnologías Utilizadas

### Backend
- **Django 5.2.3**: Framework web
- **Python 3.8+**: Lenguaje de programación
- **SQLite**: Base de datos (desarrollo)
- **Pillow**: Manejo de imágenes

### Frontend
- **HTML5**: Estructura
- **CSS3**: Estilos y diseño responsivo
- **JavaScript**: Interactividad
- **Emoji**: Iconos nativos

## 📊 Características Técnicas

### Base de Datos
- **Modelos**: 6 modelos principales
- **Relaciones**: Foreign Keys y Many-to-Many
- **Migraciones**: Sistema de versionado de BD
- **Validaciones**: A nivel de modelo y formulario

### API
- **Dashboard Data**: Endpoint JSON para gráficos
- **Filtros**: Búsqueda y filtrado avanzado
- **CRUD**: Operaciones completas por entidad

### Rendimiento
- **Optimización**: Consultas eficientes
- **Caché**: Preparado para implementación
- **Paginación**: Para listas grandes
- **Lazy Loading**: Para imágenes

## 🚀 Despliegue

### Desarrollo
```bash
python manage.py runserver
```

### Producción
1. Configurar `DEBUG = False`
2. Configurar base de datos PostgreSQL
3. Configurar archivos estáticos
4. Configurar HTTPS
5. Configurar backup automático

## 🤝 Contribución

### Cómo Contribuir
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código
- Seguir PEP 8 para Python
- Documentar funciones y clases
- Escribir tests para nuevas funcionalidades
- Mantener compatibilidad con versiones anteriores

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

### Contacto
- **Issues**: Reporta bugs en GitHub Issues
- **Documentación**: Consulta los manuales incluidos
- **Comunidad**: Únete a nuestra comunidad de desarrolladores

### Problemas Comunes
- **Error de migración**: Ejecuta `python manage.py migrate`
- **Error de dependencias**: Reinstala con `pip install -r requirements.txt`
- **Error de permisos**: Verifica permisos de archivos

## 🎉 Agradecimientos

- **Django Community**: Por el excelente framework
- **Contribuidores**: Todos los que han contribuido al proyecto
- **Usuarios**: Por el feedback y sugerencias

---

## 📈 Roadmap

### Próximas Funcionalidades
- 🔔 **Notificaciones**: Sistema de alertas push
- 📊 **Reportes PDF**: Exportación de reportes
- 💱 **Múltiples Monedas**: Soporte para diferentes monedas
- 🔗 **Sincronización Bancaria**: Conexión con APIs bancarias
- 📱 **App Móvil**: Aplicación nativa para móviles
- 🤖 **IA**: Análisis inteligente de gastos

### Mejoras Técnicas
- ⚡ **Cache Redis**: Mejora de rendimiento
- 🔄 **API REST**: API completa para integraciones
- 📊 **Analytics**: Análisis avanzado de datos
- 🔒 **2FA**: Autenticación de dos factores

---

*¡Gracias por usar Salud Financiera! 💪*

*Si te gusta el proyecto, considera darle una ⭐ en GitHub.* 
# 📊 Manual de Usuario - Salud Financiera

## 🎯 Descripción General

**Salud Financiera** es una aplicación web desarrollada en Django que te permite gestionar tus finanzas personales de manera integral. La aplicación te ayuda a controlar ingresos, gastos, crear presupuestos, establecer metas financieras y mantener un seguimiento detallado de tu situación económica.

---

## 🚀 Primeros Pasos

### 1. Acceso al Sistema
- **URL**: `http://localhost:8000/finanzas/`
- **Login**: Ingresa con tu usuario y contraseña
- **Registro**: Si no tienes cuenta, contacta al administrador

### 2. Navegación Principal
La aplicación cuenta con un menú lateral que incluye:
- 📊 **Dashboard** - Vista general de tus finanzas
- 💰 **Transacciones** - Gestión de ingresos y gastos
- 📂 **Categorías** - Organización de transacciones
- 💳 **Cuentas** - Gestión de cuentas bancarias y efectivo
- 🏷️ **Tags** - Etiquetas para organizar transacciones
- 📋 **Presupuestos** - Control de gastos por categoría
- 🎯 **Metas** - Objetivos financieros personales

---

## 💰 Módulo 1: Gestión de Transacciones

### Transacciones
**Ubicación**: Menú → Transacciones

#### Crear una Transacción
1. Haz clic en "Nueva Transacción"
2. Completa los campos:
   - **Monto**: Cantidad de dinero
   - **Fecha**: Fecha de la transacción
   - **Tipo**: Ingreso, Gasto o Transferencia
   - **Descripción**: Detalle de la transacción
   - **Categoría**: Clasificación (ej: Alimentación, Transporte)
   - **Cuenta**: Cuenta desde/para la transacción
   - **Tags**: Etiquetas opcionales para organización

#### Tipos de Transacciones
- **Ingreso**: Dinero que recibes (salario, regalo, etc.)
- **Gasto**: Dinero que gastas (compras, servicios, etc.)
- **Transferencia**: Movimiento entre cuentas propias

#### Funciones Disponibles
- ✅ **Listar**: Ver todas las transacciones con filtros
- ➕ **Crear**: Agregar nuevas transacciones
- ✏️ **Editar**: Modificar transacciones existentes
- 🗑️ **Eliminar**: Eliminar transacciones (con confirmación)

---

## 📂 Gestión de Categorías

### Categorías
**Ubicación**: Menú → Categorías

#### Crear una Categoría
1. Haz clic en "Nueva Categoría"
2. Completa:
   - **Nombre**: Nombre de la categoría
   - **Icono**: Emoji representativo (ej: 🍕 para Comida)
   - **Color**: Color distintivo
   - **Tipo**: Ingreso, Gasto o Ambos

#### Categorías Predefinidas Sugeridas
- 🍕 **Alimentación** (Gasto)
- 🚗 **Transporte** (Gasto)
- 🏠 **Vivienda** (Gasto)
- 💊 **Salud** (Gasto)
- 🎮 **Entretenimiento** (Gasto)
- 💼 **Trabajo** (Ingreso)
- 🎁 **Regalos** (Ingreso)

---

## 💳 Gestión de Cuentas

### Cuentas
**Ubicación**: Menú → Cuentas

#### Tipos de Cuentas Disponibles
- 💵 **Efectivo**: Dinero en mano
- 🏦 **Cuenta Bancaria**: Cuenta corriente o caja de ahorro
- 💳 **Tarjeta de Crédito**: Tarjetas de crédito
- 🏧 **Tarjeta de Débito**: Tarjetas de débito
- 📱 **Billetera Virtual**: Mercado Pago, Ualá, etc.
- 📈 **Cuenta de Inversión**: Plazos fijos, fondos, etc.
- 📋 **Otro**: Otras cuentas

#### Crear una Cuenta
1. Haz clic en "Nueva Cuenta"
2. Completa:
   - **Nombre**: Nombre de la cuenta
   - **Tipo**: Tipo de cuenta
   - **Saldo Inicial**: Saldo actual de la cuenta
   - **Icono**: Emoji representativo
   - **Color**: Color distintivo

#### Características Especiales
- **Saldo Automático**: Se actualiza automáticamente con transacciones
- **Tarjetas de Crédito**: Incluye fecha de cierre y vencimiento
- **Límite de Crédito**: Para tarjetas de crédito

---

## 🏷️ Sistema de Tags

### Tags
**Ubicación**: Menú → Tags

#### Crear un Tag
1. Haz clic en "Nuevo Tag"
2. Completa:
   - **Nombre**: Nombre del tag (ej: "vacaciones", "emergencia")
   - **Color**: Color distintivo
   - **Descripción**: Descripción opcional

#### Uso de Tags
- **Organización**: Etiqueta transacciones relacionadas
- **Filtrado**: Filtra transacciones por tags
- **Análisis**: Analiza patrones de gastos por tags

---

## 📋 Módulo 2: Presupuestos

### Presupuestos
**Ubicación**: Menú → Presupuestos

#### Crear un Presupuesto
1. Haz clic en "Crear Presupuesto"
2. Completa:
   - **Nombre**: Nombre del presupuesto
   - **Descripción**: Detalle del presupuesto
   - **Monto Objetivo**: Cantidad máxima a gastar
   - **Período**: Mensual, Trimestral, Semestral, Anual
   - **Fechas**: Inicio y fin del período
   - **Categorías**: Categorías incluidas en el presupuesto

#### Seguimiento del Presupuesto
- **Progreso Visual**: Barra de progreso con porcentaje
- **Monto Gastado**: Cantidad ya gastada
- **Monto Restante**: Cantidad disponible
- **Estado**: Activo, Pausado, Completado, Cancelado

#### Alertas
- **80% del Presupuesto**: Notificación cuando se alcanza el 80%
- **100% del Presupuesto**: Notificación cuando se alcanza el límite

---

## 🎯 Metas Financieras

### Metas
**Ubicación**: Menú → Metas

#### Tipos de Metas
- 💰 **Ahorro**: Ahorrar para un objetivo
- 📈 **Inversión**: Invertir en algo específico
- 💳 **Pago de Deuda**: Pagar una deuda
- 🛒 **Compra Específica**: Comprar algo específico
- 📋 **Otro**: Otros objetivos financieros

#### Crear una Meta
1. Haz clic en "Crear Meta"
2. Completa:
   - **Nombre**: Nombre de la meta
   - **Descripción**: Detalle de la meta
   - **Tipo**: Tipo de meta
   - **Monto Objetivo**: Cantidad a alcanzar
   - **Fecha Objetivo**: Fecha límite
   - **Cuenta**: Cuenta donde se guardará el dinero

#### Seguimiento de Metas
- **Progreso Visual**: Barra de progreso con porcentaje
- **Monto Actual**: Cantidad ya ahorrada
- **Monto Restante**: Cantidad faltante
- **Días Restantes**: Tiempo hasta la fecha objetivo
- **Estado**: Activa, Pausada, Completada, Cancelada

#### Actualizar Progreso
- Haz clic en "Actualizar Progreso" en la meta
- Ingresa el nuevo monto actual
- El sistema calcula automáticamente el progreso

---

## 📊 Dashboard

### Vista General
**Ubicación**: Menú → Dashboard

#### Información Mostrada
- **Balance del Mes**: Ingresos - Gastos del mes actual
- **Ingresos del Mes**: Total de ingresos del mes
- **Gastos del Mes**: Total de gastos del mes
- **Gráfico de Gastos**: Distribución de gastos por categoría
- **Presupuestos Activos**: Estado de presupuestos vigentes
- **Metas Activas**: Progreso de metas financieras

#### Gráficos Interactivos
- **Gastos por Categoría**: Gráfico circular mostrando distribución
- **Progreso de Metas**: Barras de progreso de metas activas
- **Estado de Presupuestos**: Indicadores visuales de presupuestos

---

## 🔧 Funciones Avanzadas

### Filtros y Búsquedas
- **Por Fecha**: Filtra transacciones por rango de fechas
- **Por Categoría**: Filtra por categorías específicas
- **Por Cuenta**: Filtra por cuentas específicas
- **Por Tags**: Filtra por tags específicos
- **Por Monto**: Filtra por rango de montos

### Exportación de Datos
- **Transacciones**: Exporta historial de transacciones
- **Reportes**: Genera reportes personalizados
- **Gráficos**: Exporta gráficos en diferentes formatos

### Configuraciones
- **Moneda**: Configura la moneda principal
- **Zona Horaria**: Ajusta la zona horaria
- **Notificaciones**: Activa/desactiva notificaciones
- **Recordatorios**: Configura recordatorios de pagos

---

## 📱 Diseño Responsivo

### Características
- **Móvil**: Optimizado para smartphones
- **Tablet**: Adaptado para tablets
- **Desktop**: Experiencia completa en computadoras
- **Navegación**: Menú colapsable en dispositivos móviles

### Accesibilidad
- **Contraste**: Colores con buen contraste
- **Tamaño de Fuente**: Texto legible en todos los dispositivos
- **Navegación por Teclado**: Compatible con navegación por teclado

---

## 🛡️ Seguridad y Privacidad

### Protección de Datos
- **Autenticación**: Sistema de login seguro
- **Sesiones**: Sesiones con tiempo de expiración
- **Datos Personales**: Los datos son privados por usuario
- **Backup**: Respaldo regular de datos

### Buenas Prácticas
- **Contraseñas Seguras**: Usa contraseñas fuertes
- **Cerrar Sesión**: Cierra sesión al terminar
- **Dispositivos Seguros**: Accede desde dispositivos confiables

---

## ❓ Preguntas Frecuentes

### ¿Cómo actualizo el saldo de una cuenta?
Los saldos se actualizan automáticamente al crear, editar o eliminar transacciones.

### ¿Puedo transferir dinero entre cuentas?
Sí, usa el tipo "Transferencia" al crear una transacción y selecciona la cuenta destino.

### ¿Cómo funcionan los presupuestos?
Los presupuestos controlan gastos por categoría en un período específico.

### ¿Puedo pausar una meta?
Sí, puedes cambiar el estado de una meta a "Pausada" desde la edición.

### ¿Cómo agrego una imagen de recibo?
Al crear una transacción, puedes subir una imagen del recibo en el campo correspondiente.

---

## 🆘 Soporte

### Problemas Comunes
1. **No puedo acceder**: Verifica tu usuario y contraseña
2. **Datos no se guardan**: Verifica que todos los campos obligatorios estén completos
3. **Error en cálculos**: Los cálculos son automáticos, verifica los datos ingresados

### Contacto
- **Administrador**: Contacta al administrador del sistema
- **Documentación**: Consulta este manual
- **Actualizaciones**: Mantén la aplicación actualizada

---

## 📈 Consejos de Uso

### Para Mejor Organización
1. **Crea categorías específicas** para tus gastos más comunes
2. **Usa tags** para agrupar transacciones relacionadas
3. **Revisa el dashboard** regularmente para mantener control
4. **Establece metas realistas** y actualiza el progreso
5. **Crea presupuestos** para categorías de alto gasto

### Para Ahorrar Dinero
1. **Analiza tus gastos** usando los gráficos del dashboard
2. **Identifica gastos innecesarios** con el historial de transacciones
3. **Establece metas de ahorro** con fechas específicas
4. **Usa presupuestos** para controlar gastos por categoría
5. **Revisa regularmente** tu progreso financiero

---

*Este manual está diseñado para ayudarte a aprovechar al máximo todas las funcionalidades de Salud Financiera. ¡Que tengas éxito en el manejo de tus finanzas personales! 💪* 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Transaccion, Categoria, Cuenta, Tag, ConfiguracionUsuario, Presupuesto, Meta, CorteMes, GrupoGastosCompartidos, GastoCompartido, PagoGastoCompartido, Notificacion
from .forms import (
    TransaccionForm, CategoriaForm, CuentaForm, TagForm, FiltroTransaccionesForm,
    PresupuestoForm, MetaForm, UsuarioCrearForm, UsuarioEditarForm, 
    ConfiguracionUsuarioForm, ConfiguracionSistemaForm, RegistroPublicoForm,
    GrupoGastosCompartidosForm, GastoCompartidoForm, PagoGastoCompartidoForm,
    FiltroGastosCompartidosForm
)
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from calendar import monthrange
import json
from functools import wraps
from django.views.decorators.http import require_POST
from django.urls import reverse

# Decorador personalizado para verificar permisos de staff
def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return render(request, 'configuracion/acceso_denegado.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Tu cuenta está pendiente de activación. Un administrador la revisará pronto.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'login/login.html')

def registro_publico(request):
    """Vista para registro público de usuarios (marcados como inactivos)"""
    if request.method == 'POST':
        form = RegistroPublicoForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Crear configuración por defecto para el usuario
            ConfiguracionUsuario.objects.create(
                usuario=user,
                moneda_principal='ARS',
                zona_horaria='America/Argentina/Buenos_Aires',
                notificaciones_activas=True,
                recordatorios_pago=True
            )
            
            messages.success(request, 'Tu cuenta ha sido creada exitosamente. Un administrador la revisará y activará pronto.')
            return redirect('login')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistroPublicoForm()
    
    return render(request, 'login/registro.html', {'form': form})

@login_required
def dashboard(request):
    # Obtener el mes actual
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    
    # Estadísticas del mes
    ingresos_mes = Transaccion.objects.filter(
        usuario=request.user,
        tipo='ingreso',
        fecha__gte=inicio_mes
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    gastos_mes = Transaccion.objects.filter(
        usuario=request.user,
        tipo='gasto',
        fecha__gte=inicio_mes
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    balance_neto = ingresos_mes - gastos_mes
    
    # Cuentas activas
    cuentas_activas = Cuenta.objects.filter(usuario=request.user, activa=True)
    total_cuentas = cuentas_activas.count()
    
    # Calcular porcentaje de saldo para cada cuenta
    for cuenta in cuentas_activas:
        if cuenta.saldo_actual > 0:
            cuenta.porcentaje_saldo = min(100, (cuenta.saldo_actual / max(cuenta.saldo_actual, 1)) * 100)
        else:
            cuenta.porcentaje_saldo = abs(cuenta.saldo_actual) / max(abs(cuenta.saldo_actual), 1) * 100
    
    # Gastos por categoría del mes
    gastos_por_categoria = Transaccion.objects.filter(
        usuario=request.user,
        tipo='gasto',
        fecha__gte=inicio_mes
    ).values('categoria__nombre', 'categoria__color').annotate(
        total=Sum('monto')
    ).order_by('-total')
    
    # Calcular porcentajes para el gráfico
    total_gastos = sum(item['total'] for item in gastos_por_categoria)
    for item in gastos_por_categoria:
        if total_gastos > 0:
            item['porcentaje'] = (item['total'] / total_gastos) * 360  # Grados para el gráfico
        else:
            item['porcentaje'] = 0
    
    # Presupuestos activos
    presupuestos_activos = Presupuesto.objects.filter(
        usuario=request.user,
        estado='activo'
    ).order_by('-fecha_creacion')[:5]
    
    # Actualizar gastos de presupuestos
    for presupuesto in presupuestos_activos:
        presupuesto.actualizar_gasto()
    
    # Metas activas
    metas_activas = Meta.objects.filter(
        usuario=request.user,
        estado='activa'
    ).order_by('-fecha_creacion')[:5]
    
    # Transacciones recientes
    transacciones_recientes = Transaccion.objects.filter(
        usuario=request.user
    ).select_related('categoria', 'cuenta').order_by('-fecha', '-fecha_creacion')[:10]
    
    context = {
        'ingresos_mes': ingresos_mes,
        'gastos_mes': gastos_mes,
        'balance_neto': balance_neto,
        'total_cuentas': total_cuentas,
        'cuentas_activas': cuentas_activas,
        'gastos_por_categoria': gastos_por_categoria,
        'presupuestos_activos': presupuestos_activos,
        'metas_activas': metas_activas,
        'transacciones_recientes': transacciones_recientes,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

def logout_view(request):
    auth_logout(request)
    return redirect('login')

# Vistas para Transacciones
@login_required(login_url='/finanzas/')
def transacciones_lista(request):
    form = FiltroTransaccionesForm(request.GET, user=request.user)
    transacciones = Transaccion.objects.filter(usuario=request.user).select_related('categoria', 'cuenta')
    
    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data.get('fecha_desde'):
            transacciones = transacciones.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            transacciones = transacciones.filter(fecha__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data.get('tipo'):
            transacciones = transacciones.filter(tipo=form.cleaned_data['tipo'])
        if form.cleaned_data.get('categoria'):
            transacciones = transacciones.filter(categoria=form.cleaned_data['categoria'])
        if form.cleaned_data.get('cuenta'):
            transacciones = transacciones.filter(cuenta=form.cleaned_data['cuenta'])
        if form.cleaned_data.get('monto_minimo'):
            transacciones = transacciones.filter(monto__gte=form.cleaned_data['monto_minimo'])
        if form.cleaned_data.get('monto_maximo'):
            transacciones = transacciones.filter(monto__lte=form.cleaned_data['monto_maximo'])
    
    # Paginación
    paginator = Paginator(transacciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_transacciones': transacciones.count(),
    }
    return render(request, 'transacciones/lista.html', context)

@login_required(login_url='/finanzas/')
def transaccion_crear(request):
    if request.method == 'POST':
        form = TransaccionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            transaccion = form.save(commit=False)
            transaccion.usuario = request.user
            transaccion.save()
            form.save_m2m()  # Guardar tags
            messages.success(request, 'Transacción creada exitosamente.')
            return redirect('transacciones_lista')
    else:
        form = TransaccionForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nueva Transacción',
    }
    return render(request, 'transacciones/form.html', context)

@login_required(login_url='/finanzas/')
def transaccion_editar(request, pk):
    transaccion = get_object_or_404(Transaccion, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = TransaccionForm(request.POST, request.FILES, instance=transaccion, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transacción actualizada exitosamente.')
            return redirect('transacciones_lista')
    else:
        form = TransaccionForm(instance=transaccion, user=request.user)
    
    context = {
        'form': form,
        'transaccion': transaccion,
        'titulo': 'Editar Transacción',
    }
    return render(request, 'transacciones/form.html', context)

@login_required(login_url='/finanzas/')
def transaccion_eliminar(request, pk):
    transaccion = get_object_or_404(Transaccion, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        transaccion.delete()
        messages.success(request, 'Transacción eliminada exitosamente.')
        return redirect('transacciones_lista')
    
    context = {
        'transaccion': transaccion,
    }
    return render(request, 'transacciones/eliminar.html', context)

# Vistas para Categorías
@login_required(login_url='/finanzas/')
def categorias_lista(request):
    categorias = Categoria.objects.filter(usuario=request.user).order_by('nombre')
    context = {
        'categorias': categorias,
    }
    return render(request, 'categorias/lista.html', context)

@login_required(login_url='/finanzas/')
def categoria_crear(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('categorias_lista')
    else:
        form = CategoriaForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nueva Categoría',
    }
    return render(request, 'categorias/form.html', context)

@login_required(login_url='/finanzas/')
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('categorias_lista')
    else:
        form = CategoriaForm(instance=categoria, user=request.user)
    
    context = {
        'form': form,
        'categoria': categoria,
        'titulo': 'Editar Categoría',
    }
    return render(request, 'categorias/form.html', context)

@login_required(login_url='/finanzas/')
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('categorias_lista')
    
    context = {
        'categoria': categoria
    }
    return render(request, 'categorias/eliminar.html', context)

# Vistas para Cuentas
@login_required(login_url='/finanzas/')
def cuentas_lista(request):
    cuentas = Cuenta.objects.filter(usuario=request.user).order_by('nombre')
    context = {
        'cuentas': cuentas,
    }
    return render(request, 'cuentas/lista.html', context)

@login_required(login_url='/finanzas/')
def cuenta_crear(request):
    if request.method == 'POST':
        form = CuentaForm(request.POST, user=request.user)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.saldo_actual = cuenta.saldo_inicial
            cuenta.save()
            messages.success(request, 'Cuenta creada exitosamente.')
            return redirect('cuentas_lista')
    else:
        form = CuentaForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nueva Cuenta',
    }
    return render(request, 'cuentas/form.html', context)

@login_required(login_url='/finanzas/')
def cuenta_editar(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta actualizada exitosamente.')
            return redirect('cuentas_lista')
    else:
        form = CuentaForm(instance=cuenta, user=request.user)
    
    context = {
        'form': form,
        'cuenta': cuenta,
        'titulo': 'Editar Cuenta',
    }
    return render(request, 'cuentas/form.html', context)

@login_required(login_url='/finanzas/')
def cuenta_eliminar(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        cuenta.delete()
        messages.success(request, 'Cuenta eliminada exitosamente.')
        return redirect('cuentas_lista')
    
    context = {
        'cuenta': cuenta
    }
    return render(request, 'cuentas/eliminar.html', context)

# API para obtener datos del dashboard
@login_required(login_url='/finanzas/')
def api_dashboard_data(request):
    """API para obtener datos del dashboard en formato JSON"""
    mes_actual = date.today().replace(day=1)
    mes_siguiente = (mes_actual + timedelta(days=32)).replace(day=1)
    
    transacciones_mes = Transaccion.objects.filter(
        usuario=request.user,
        fecha__gte=mes_actual,
        fecha__lt=mes_siguiente
    )
    
    ingresos_mes = transacciones_mes.filter(tipo='ingreso').aggregate(
        total=Sum('monto'))['total'] or Decimal('0')
    gastos_mes = transacciones_mes.filter(tipo='gasto').aggregate(
        total=Sum('monto'))['total'] or Decimal('0')
    
    # Gastos por categoría para gráfico
    gastos_por_categoria = list(transacciones_mes.filter(tipo='gasto').values(
        'categoria__nombre', 'categoria__color'
    ).annotate(total=Sum('monto')).order_by('-total')[:10])
    
    data = {
        'ingresos_mes': float(ingresos_mes),
        'gastos_mes': float(gastos_mes),
        'balance_mes': float(ingresos_mes - gastos_mes),
        'gastos_por_categoria': gastos_por_categoria,
    }
    
    return JsonResponse(data)

# Vistas para Presupuestos
@login_required
def presupuestos_lista(request):
    presupuestos = Presupuesto.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    
    # Actualizar gastos de todos los presupuestos
    for presupuesto in presupuestos:
        presupuesto.actualizar_gasto()
    
    context = {
        'presupuestos': presupuestos,
        'titulo': 'Presupuestos'
    }
    return render(request, 'presupuestos/lista.html', context)

@login_required
def presupuesto_crear(request):
    if request.method == 'POST':
        form = PresupuestoForm(request.POST, user=request.user)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            presupuesto.usuario = request.user
            presupuesto.save()
            form.save_m2m()  # Guardar las relaciones many-to-many
            messages.success(request, 'Presupuesto creado exitosamente.')
            return redirect('presupuestos_lista')
    else:
        form = PresupuestoForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Crear Presupuesto'
    }
    return render(request, 'presupuestos/form.html', context)

@login_required
def presupuesto_editar(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = PresupuestoForm(request.POST, instance=presupuesto, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Presupuesto actualizado exitosamente.')
            return redirect('presupuestos_lista')
    else:
        form = PresupuestoForm(instance=presupuesto, user=request.user)
    
    context = {
        'form': form,
        'presupuesto': presupuesto,
        'titulo': 'Editar Presupuesto'
    }
    return render(request, 'presupuestos/form.html', context)

@login_required
def presupuesto_eliminar(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        presupuesto.delete()
        messages.success(request, 'Presupuesto eliminado exitosamente.')
        return redirect('presupuestos_lista')
    
    context = {
        'presupuesto': presupuesto
    }
    return render(request, 'presupuestos/eliminar.html', context)

# Vistas para Metas
@login_required
def metas_lista(request):
    metas = Meta.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    
    context = {
        'metas': metas,
        'titulo': 'Metas'
    }
    return render(request, 'metas/lista.html', context)

@login_required
def meta_crear(request):
    if request.method == 'POST':
        form = MetaForm(request.POST, user=request.user)
        if form.is_valid():
            meta = form.save(commit=False)
            meta.usuario = request.user
            meta.save()
            messages.success(request, 'Meta creada exitosamente.')
            return redirect('metas_lista')
    else:
        form = MetaForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Crear Meta'
    }
    return render(request, 'metas/form.html', context)

@login_required
def meta_editar(request, pk):
    meta = get_object_or_404(Meta, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = MetaForm(request.POST, instance=meta, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meta actualizada exitosamente.')
            return redirect('metas_lista')
    else:
        form = MetaForm(instance=meta, user=request.user)
    
    context = {
        'form': form,
        'meta': meta,
        'titulo': 'Editar Meta'
    }
    return render(request, 'metas/form.html', context)

@login_required
def meta_eliminar(request, pk):
    meta = get_object_or_404(Meta, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        meta.delete()
        messages.success(request, 'Meta eliminada exitosamente.')
        return redirect('metas_lista')
    
    context = {
        'meta': meta
    }
    return render(request, 'metas/eliminar.html', context)

@login_required
def meta_actualizar_progreso(request, pk):
    meta = get_object_or_404(Meta, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        nuevo_monto = request.POST.get('monto_actual')
        try:
            nuevo_monto = float(nuevo_monto)
            if nuevo_monto >= 0:
                meta.monto_actual = nuevo_monto
                meta.save()
                messages.success(request, 'Progreso de la meta actualizado exitosamente.')
            else:
                messages.error(request, 'El monto debe ser mayor o igual a 0.')
        except ValueError:
            messages.error(request, 'Por favor ingrese un monto válido.')
    
    return redirect('metas_lista')

# Vistas para Tags
@login_required
def tags_lista(request):
    tags = Tag.objects.filter(usuario=request.user).order_by('nombre')
    context = {
        'tags': tags,
    }
    return render(request, 'tags/lista.html', context)

@login_required
def tag_crear(request):
    if request.method == 'POST':
        form = TagForm(request.POST, user=request.user)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.usuario = request.user
            tag.save()
            messages.success(request, 'Tag creado exitosamente.')
            return redirect('tags_lista')
    else:
        form = TagForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nuevo Tag',
    }
    return render(request, 'tags/form.html', context)

@login_required
def tag_editar(request, pk):
    tag = get_object_or_404(Tag, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag actualizado exitosamente.')
            return redirect('tags_lista')
    else:
        form = TagForm(instance=tag, user=request.user)
    
    context = {
        'form': form,
        'tag': tag,
        'titulo': 'Editar Tag',
    }
    return render(request, 'tags/form.html', context)

@login_required
def tag_eliminar(request, pk):
    tag = get_object_or_404(Tag, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag eliminado exitosamente.')
        return redirect('tags_lista')
    
    context = {
        'tag': tag
    }
    return render(request, 'tags/eliminar.html', context)

@login_required
def corte_mes_confirmar(request):
    """Vista para confirmar el corte de mes"""
    # Obtener el mes actual
    hoy = date.today()
    mes_actual = hoy.month
    año_actual = hoy.year
    
    # Verificar si ya se hizo el corte para este mes
    corte_existente = CorteMes.objects.filter(
        usuario=request.user,
        mes_cortado=mes_actual,
        año_cortado=año_actual
    ).first()
    
    if corte_existente:
        messages.warning(request, f'Ya se realizó el corte para {corte_existente.mes_nombre} {año_actual}.')
        return redirect('dashboard')
    
    # Calcular el último día del mes
    ultimo_dia = monthrange(año_actual, mes_actual)[1]
    fecha_fin_mes = date(año_actual, mes_actual, ultimo_dia)
    
    # Calcular estadísticas del mes
    inicio_mes = date(año_actual, mes_actual, 1)
    
    ingresos_mes = Transaccion.objects.filter(
        usuario=request.user,
        tipo='ingreso',
        fecha__gte=inicio_mes,
        fecha__lte=fecha_fin_mes
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    gastos_mes = Transaccion.objects.filter(
        usuario=request.user,
        tipo='gasto',
        fecha__gte=inicio_mes,
        fecha__lte=fecha_fin_mes
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    balance_mes = ingresos_mes - gastos_mes
    
    # Obtener saldos actuales de las cuentas
    cuentas_activas = Cuenta.objects.filter(usuario=request.user, activa=True)
    saldos_cuentas = {}
    
    for cuenta in cuentas_activas:
        saldos_cuentas[cuenta.id] = {
            'nombre': cuenta.nombre,
            'saldo_actual': float(cuenta.saldo_actual),
            'tipo': cuenta.tipo_cuenta
        }
    
    # Transacciones del mes
    transacciones_mes = Transaccion.objects.filter(
        usuario=request.user,
        fecha__gte=inicio_mes,
        fecha__lte=fecha_fin_mes
    ).count()
    
    context = {
        'mes_actual': mes_actual,
        'año_actual': año_actual,
        'mes_nombre': CorteMes(mes_cortado=mes_actual).mes_nombre,
        'fecha_fin_mes': fecha_fin_mes,
        'ingresos_mes': ingresos_mes,
        'gastos_mes': gastos_mes,
        'balance_mes': balance_mes,
        'saldos_cuentas': saldos_cuentas,
        'transacciones_mes': transacciones_mes,
        'cuentas_activas': cuentas_activas,
    }
    
    return render(request, 'corte_mes/confirmar.html', context)

@login_required
def corte_mes_ejecutar(request):
    """Vista para ejecutar el corte de mes"""
    if request.method != 'POST':
        return redirect('corte_mes_confirmar')
    
    # Obtener el mes actual
    hoy = date.today()
    mes_actual = hoy.month
    año_actual = hoy.year
    
    # Verificar si ya se hizo el corte para este mes
    corte_existente = CorteMes.objects.filter(
        usuario=request.user,
        mes_cortado=mes_actual,
        año_actual=año_actual
    ).first()
    
    if corte_existente:
        messages.warning(request, f'Ya se realizó el corte para {corte_existente.mes_nombre} {año_actual}.')
        return redirect('dashboard')
    
    # Calcular el último día del mes
    ultimo_dia = monthrange(año_actual, mes_actual)[1]
    fecha_fin_mes = date(año_actual, mes_actual, ultimo_dia)
    
    # Calcular estadísticas del mes
    inicio_mes = date(año_actual, mes_actual, 1)
    
    ingresos_mes = Transaccion.objects.filter(
        usuario=request.user,
        tipo='ingreso',
        fecha__gte=inicio_mes,
        fecha__lte=fecha_fin_mes
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    gastos_mes = Transaccion.objects.filter(
        usuario=request.user,
        tipo='gasto',
        fecha__gte=inicio_mes,
        fecha__lte=fecha_fin_mes
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    balance_mes = ingresos_mes - gastos_mes
    
    # Obtener saldos actuales de las cuentas
    cuentas_activas = Cuenta.objects.filter(usuario=request.user, activa=True)
    saldos_cuentas = {}
    
    for cuenta in cuentas_activas:
        saldos_cuentas[cuenta.id] = float(cuenta.saldo_actual)
    
    # Crear el registro del corte
    corte_mes = CorteMes.objects.create(
        usuario=request.user,
        fecha_corte=fecha_fin_mes,
        mes_cortado=mes_actual,
        año_cortado=año_actual,
        total_ingresos=ingresos_mes,
        total_gastos=gastos_mes,
        balance_mes=balance_mes,
        saldos_cuentas=saldos_cuentas,
        mantener_saldos=True
    )
    
    # Opcional: Archivar transacciones del mes (mover a una tabla de histórico)
    # Por ahora solo registramos el corte sin eliminar transacciones
    
    messages.success(
        request, 
        f'Corte de mes realizado exitosamente para {corte_mes.mes_nombre} {año_actual}. '
        f'Balance: ${balance_mes:,.2f}'
    )
    
    return redirect('dashboard')

@login_required
def cortes_mes_lista(request):
    """Vista para listar todos los cortes de mes"""
    cortes = CorteMes.objects.filter(usuario=request.user).order_by('-fecha_corte')
    
    # Paginación
    paginator = Paginator(cortes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_cortes': cortes.count(),
    }
    
    return render(request, 'corte_mes/lista.html', context)

@login_required
def corte_mes_detalle(request, pk):
    """Vista para mostrar el detalle de un corte de mes"""
    corte = get_object_or_404(CorteMes, pk=pk, usuario=request.user)
    
    # Obtener las transacciones del mes cortado
    inicio_mes = date(corte.año_cortado, corte.mes_cortado, 1)
    ultimo_dia = monthrange(corte.año_cortado, corte.mes_cortado)[1]
    fecha_fin_mes = date(corte.año_cortado, corte.mes_cortado, ultimo_dia)
    
    transacciones = Transaccion.objects.filter(
        usuario=request.user,
        fecha__gte=inicio_mes,
        fecha__lte=fecha_fin_mes
    ).select_related('categoria', 'cuenta').order_by('-fecha')
    
    # Gastos por categoría
    gastos_por_categoria = Transaccion.objects.filter(
        usuario=request.user,
        tipo='gasto',
        fecha__gte=inicio_mes,
        fecha__lte=fecha_fin_mes
    ).values('categoria__nombre', 'categoria__color').annotate(
        total=Sum('monto')
    ).order_by('-total')
    
    context = {
        'corte': corte,
        'transacciones': transacciones,
        'gastos_por_categoria': gastos_por_categoria,
        'total_transacciones': transacciones.count(),
    }
    
    return render(request, 'corte_mes/detalle.html', context)

@login_required
def usuarios_lista(request):
    usuarios = User.objects.filter(is_superuser=False).order_by('username')
    context = {
        'usuarios': usuarios,
    }
    return render(request, 'usuarios/lista.html', context)

@login_required
def usuario_crear(request):
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST, user=request.user)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.password = make_password(form.cleaned_data['password'])
            usuario.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('usuarios_lista')
    else:
        form = UsuarioCrearForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nuevo Usuario',
    }
    return render(request, 'usuarios/form.html', context)

@login_required
def usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk, is_superuser=False)
    
    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('usuarios_lista')
    else:
        form = UsuarioEditarForm(instance=usuario, user=request.user)
    
    context = {
        'form': form,
        'usuario': usuario,
        'titulo': 'Editar Usuario',
    }
    return render(request, 'usuarios/form.html', context)

@login_required
def usuario_eliminar(request, pk):
    usuario = get_object_or_404(User, pk=pk, is_superuser=False)
    
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('usuarios_lista')
    
    context = {
        'usuario': usuario
    }
    return render(request, 'usuarios/eliminar.html', context)

@login_required
def configuracion_usuario(request):
    if request.method == 'POST':
        form = ConfiguracionUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración del usuario actualizada exitosamente.')
            return redirect('dashboard')
    else:
        form = ConfiguracionUsuarioForm(instance=request.user)
    
    context = {
        'form': form,
        'titulo': 'Configuración del Usuario',
    }
    return render(request, 'configuracion_usuario/form.html', context)

@login_required
def configuracion_sistema(request):
    if request.method == 'POST':
        form = ConfiguracionSistemaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración del sistema actualizada exitosamente.')
            return redirect('dashboard')
    else:
        form = ConfiguracionSistemaForm()
    
    context = {
        'form': form,
        'titulo': 'Configuración del Sistema',
    }
    return render(request, 'configuracion_sistema/form.html', context)

# Vistas para Configuración del Sistema
@login_required
@staff_required
def configuracion(request):
    """Vista principal de configuración del sistema"""
    # Obtener todos los usuarios
    usuarios = User.objects.all().order_by('username')
    
    # Obtener configuración del sistema (usar la del usuario actual como ejemplo)
    try:
        config = ConfiguracionUsuario.objects.get(usuario=request.user)
    except ConfiguracionUsuario.DoesNotExist:
        config = ConfiguracionUsuario.objects.create(usuario=request.user)
    
    # Estadísticas del sistema
    total_usuarios = User.objects.count()
    usuarios_pendientes = User.objects.filter(is_active=False).count()
    total_transacciones = Transaccion.objects.count()
    total_cuentas = Cuenta.objects.count()
    total_categorias = Categoria.objects.count()
    
    context = {
        'usuarios': usuarios,
        'config': config,
        'total_usuarios': total_usuarios,
        'usuarios_pendientes': usuarios_pendientes,
        'total_transacciones': total_transacciones,
        'total_cuentas': total_cuentas,
        'total_categorias': total_categorias,
    }
    return render(request, 'configuracion/configuracion.html', context)

@login_required
@staff_required
def usuarios_pendientes(request):
    """Vista para listar usuarios pendientes de activación"""
    usuarios_pendientes = User.objects.filter(is_active=False).order_by('date_joined')
    
    context = {
        'usuarios_pendientes': usuarios_pendientes,
        'total_pendientes': usuarios_pendientes.count(),
    }
    return render(request, 'configuracion/usuarios_pendientes.html', context)

@login_required
@staff_required
def usuario_crear(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        config_form = ConfiguracionUsuarioForm(request.POST)
        
        if form.is_valid() and config_form.is_valid():
            usuario = form.save()
            
            # Crear configuración para el usuario
            config = config_form.save(commit=False)
            config.usuario = usuario
            config.save()
            
            messages.success(request, f'Usuario "{usuario.username}" creado exitosamente.')
            return redirect('configuracion')
    else:
        form = UsuarioCrearForm()
        config_form = ConfiguracionUsuarioForm()
    
    context = {
        'form': form,
        'config_form': config_form,
        'titulo': 'Nuevo Usuario',
    }
    return render(request, 'configuracion/usuario_form.html', context)

@login_required
@staff_required
def usuario_editar(request, pk):
    """Editar usuario existente"""
    usuario = get_object_or_404(User, pk=pk)
    
    # Obtener o crear configuración del usuario
    try:
        config = ConfiguracionUsuario.objects.get(usuario=usuario)
    except ConfiguracionUsuario.DoesNotExist:
        config = ConfiguracionUsuario.objects.create(usuario=usuario)
    
    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        config_form = ConfiguracionUsuarioForm(request.POST, instance=config)
        
        if form.is_valid() and config_form.is_valid():
            # Manejar cambio de contraseña
            new_password = request.POST.get('new_password')
            if new_password:
                usuario.password = make_password(new_password)
            
            form.save()
            config_form.save()
            
            messages.success(request, f'Usuario "{usuario.username}" actualizado exitosamente.')
            return redirect('configuracion')
    else:
        form = UsuarioEditarForm(instance=usuario)
        config_form = ConfiguracionUsuarioForm(instance=config)
    
    context = {
        'form': form,
        'config_form': config_form,
        'usuario': usuario,
        'titulo': 'Editar Usuario',
    }
    return render(request, 'configuracion/usuario_form.html', context)

@login_required
@staff_required
def usuario_eliminar(request, pk):
    """Eliminar usuario"""
    usuario = get_object_or_404(User, pk=pk)
    
    # No permitir eliminar superusuarios
    if usuario.is_superuser:
        messages.error(request, 'No se puede eliminar un superusuario.')
        return redirect('configuracion')
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado exitosamente.')
        return redirect('configuracion')
    
    context = {
        'usuario': usuario
    }
    return render(request, 'configuracion/usuario_eliminar.html', context)

@login_required
@staff_required
def usuario_activar(request, pk):
    """Activar usuario"""
    usuario = get_object_or_404(User, pk=pk)
    usuario.is_active = True
    usuario.save()
    messages.success(request, f'Usuario "{usuario.username}" activado exitosamente.')
    return redirect('configuracion')

@login_required
@staff_required
def usuario_desactivar(request, pk):
    """Desactivar usuario"""
    usuario = get_object_or_404(User, pk=pk)
    
    # No permitir desactivar superusuarios
    if usuario.is_superuser:
        messages.error(request, 'No se puede desactivar un superusuario.')
        return redirect('configuracion')
    
    usuario.is_active = False
    usuario.save()
    messages.success(request, f'Usuario "{usuario.username}" desactivado exitosamente.')
    return redirect('configuracion')

@login_required
@staff_required
def configuracion_guardar(request):
    """Guardar configuración del sistema"""
    if request.method == 'POST':
        # Obtener configuración del usuario actual
        try:
            config = ConfiguracionUsuario.objects.get(usuario=request.user)
        except ConfiguracionUsuario.DoesNotExist:
            config = ConfiguracionUsuario.objects.create(usuario=request.user)
        
        # Actualizar configuración
        config.moneda_principal = request.POST.get('moneda_principal', 'ARS')
        config.zona_horaria = request.POST.get('zona_horaria', 'America/Argentina/Buenos_Aires')
        config.notificaciones_activas = request.POST.get('notificaciones_activas') == 'on'
        config.recordatorios_pago = request.POST.get('recordatorios_pago') == 'on'
        config.save()
        
        messages.success(request, 'Configuración guardada exitosamente.')
    
    return redirect('configuracion')

# Vistas para acciones del sistema
@login_required
@staff_required
def backup_datos(request):
    """Crear backup de datos"""
    # Aquí implementarías la lógica de backup
    messages.info(request, 'Función de backup en desarrollo.')
    return redirect('configuracion')

@login_required
@staff_required
def limpiar_datos(request):
    """Limpiar datos antiguos"""
    # Aquí implementarías la lógica de limpieza
    messages.info(request, 'Función de limpieza en desarrollo.')
    return redirect('configuracion')

@login_required
@staff_required
def exportar_datos(request):
    """Exportar datos"""
    # Aquí implementarías la lógica de exportación
    messages.info(request, 'Función de exportación en desarrollo.')
    return redirect('configuracion')

@login_required
@staff_required
def importar_datos(request):
    """Importar datos"""
    # Aquí implementarías la lógica de importación
    messages.info(request, 'Función de importación en desarrollo.')
    return redirect('configuracion')

@login_required
def configuracion_personal(request):
    """Vista para configuración personal del usuario"""
    # Obtener o crear configuración del usuario
    try:
        config = ConfiguracionUsuario.objects.get(usuario=request.user)
    except ConfiguracionUsuario.DoesNotExist:
        config = ConfiguracionUsuario.objects.create(usuario=request.user)
    
    if request.method == 'POST':
        form = ConfiguracionUsuarioForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu configuración personal ha sido actualizada exitosamente.')
            return redirect('dashboard')
    else:
        form = ConfiguracionUsuarioForm(instance=config)
    
    context = {
        'form': form,
        'config': config,
        'titulo': 'Mi Configuración',
    }
    return render(request, 'configuracion/configuracion_personal.html', context)

# Vistas para Gastos Compartidos
@login_required
def grupos_gastos_compartidos_lista(request):
    """Lista de grupos de gastos compartidos del usuario"""
    grupos = GrupoGastosCompartidos.objects.filter(miembros=request.user, activo=True).order_by('nombre')
    
    context = {
        'grupos': grupos,
    }
    return render(request, 'gastos_compartidos/grupos_lista.html', context)

@login_required
def grupo_gastos_compartidos_crear(request):
    """Crear un nuevo grupo de gastos compartidos"""
    if request.method == 'POST':
        form = GrupoGastosCompartidosForm(request.POST, user=request.user)
        if form.is_valid():
            grupo = form.save()
            messages.success(request, 'Grupo de gastos compartidos creado exitosamente.')
            return redirect('grupos_gastos_compartidos_lista')
    else:
        form = GrupoGastosCompartidosForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nuevo Grupo de Gastos Compartidos',
    }
    return render(request, 'gastos_compartidos/grupo_form.html', context)

@login_required
def grupo_gastos_compartidos_editar(request, pk):
    """Editar un grupo de gastos compartidos"""
    grupo = get_object_or_404(GrupoGastosCompartidos, pk=pk, creador=request.user)
    
    if request.method == 'POST':
        form = GrupoGastosCompartidosForm(request.POST, instance=grupo, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo actualizado exitosamente.')
            return redirect('grupos_gastos_compartidos_lista')
    else:
        form = GrupoGastosCompartidosForm(instance=grupo, user=request.user)
    
    context = {
        'form': form,
        'grupo': grupo,
        'titulo': 'Editar Grupo de Gastos Compartidos',
    }
    return render(request, 'gastos_compartidos/grupo_form.html', context)

@login_required
def grupo_gastos_compartidos_eliminar(request, pk):
    """Eliminar un grupo de gastos compartidos"""
    grupo = get_object_or_404(GrupoGastosCompartidos, pk=pk, creador=request.user)
    
    if request.method == 'POST':
        grupo.activo = False
        grupo.save()
        messages.success(request, 'Grupo eliminado exitosamente.')
        return redirect('grupos_gastos_compartidos_lista')
    
    context = {
        'grupo': grupo,
    }
    return render(request, 'gastos_compartidos/grupo_eliminar.html', context)

@login_required
def gastos_compartidos_lista(request):
    """Lista de gastos compartidos del usuario"""
    form = FiltroGastosCompartidosForm(request.GET, user=request.user)
    
    # Obtener gastos de grupos donde el usuario es miembro
    gastos = GastoCompartido.objects.filter(grupo__miembros=request.user).select_related('grupo', 'pagado_por')
    
    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data.get('fecha_desde'):
            gastos = gastos.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            gastos = gastos.filter(fecha__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data.get('tipo'):
            gastos = gastos.filter(tipo=form.cleaned_data['tipo'])
        if form.cleaned_data.get('estado'):
            gastos = gastos.filter(estado=form.cleaned_data['estado'])
        if form.cleaned_data.get('grupo'):
            gastos = gastos.filter(grupo=form.cleaned_data['grupo'])
        if form.cleaned_data.get('monto_minimo'):
            gastos = gastos.filter(monto_total__gte=form.cleaned_data['monto_minimo'])
        if form.cleaned_data.get('monto_maximo'):
            gastos = gastos.filter(monto_total__lte=form.cleaned_data['monto_maximo'])
    
    # Paginación
    paginator = Paginator(gastos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_gastos': gastos.count(),
    }
    return render(request, 'gastos_compartidos/lista.html', context)

@login_required
def gasto_compartido_crear(request):
    """Crear un nuevo gasto compartido"""
    grupos = GrupoGastosCompartidos.objects.filter(miembros=request.user, activo=True)
    if not grupos.exists():
        messages.error(request, 'Debe crear un grupo de gastos compartidos antes de agregar gastos.')
        return redirect('grupos_gastos_compartidos_lista')
    
    if request.method == 'POST':
        grupo_id = request.POST.get('grupo')
        grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, miembros=request.user)
        form = GastoCompartidoForm(request.POST, request.FILES, user=request.user, grupo=grupo)
        
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.grupo = grupo
            gasto.save()
            
            # Determinar quién pagó el gasto
            pagado_por_usuario = gasto.pagado_por
            
            # Crear registros de pago para cada miembro
            for miembro in grupo.miembros.all():
                monto_debido_miembro = gasto.monto_por_persona
                monto_pagado_miembro = Decimal('0')
                
                # Si este miembro es quien pagó, registrar su pago
                if pagado_por_usuario and miembro == pagado_por_usuario:
                    monto_pagado_miembro = monto_debido_miembro
                
                PagoGastoCompartido.objects.create(
                    gasto_compartido=gasto,
                    miembro=miembro,
                    monto_debido=monto_debido_miembro,
                    monto_pagado=monto_pagado_miembro
                )
            
            # Crear notificaciones para los miembros (excepto el creador)
            url_gasto = reverse('gasto_compartido_detalle', args=[gasto.pk])
            for miembro in grupo.miembros.all():
                if miembro != request.user:
                    Notificacion.objects.create(
                        usuario=miembro,
                        mensaje=f"{request.user.username} ha añadido un nuevo gasto en '{grupo.nombre}': {gasto.titulo}.",
                        url_destino=url_gasto
                    )
            
            messages.success(request, 'Gasto compartido creado exitosamente.')
            return redirect('gastos_compartidos_lista')
    else:
        # Pre-seleccionar grupo si viene como parámetro GET
        grupo_id = request.GET.get('grupo')
        if grupo_id:
            grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, miembros=request.user, activo=True)
            form = GastoCompartidoForm(user=request.user, grupo=grupo)
        else:
            form = GastoCompartidoForm(user=request.user, grupo=grupos.first())
    
    context = {
        'form': form,
        'grupos': grupos,
        'titulo': 'Nuevo Gasto Compartido',
    }
    return render(request, 'gastos_compartidos/form.html', context)

@login_required
def gasto_compartido_editar(request, pk):
    """Editar un gasto compartido"""
    gasto = get_object_or_404(GastoCompartido, pk=pk, grupo__miembros=request.user)
    
    if request.method == 'POST':
        form = GastoCompartidoForm(request.POST, request.FILES, instance=gasto, user=request.user, grupo=gasto.grupo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto compartido actualizado exitosamente.')
            return redirect('gastos_compartidos_lista')
    else:
        form = GastoCompartidoForm(instance=gasto, user=request.user, grupo=gasto.grupo)
    
    context = {
        'form': form,
        'gasto': gasto,
        'titulo': 'Editar Gasto Compartido',
    }
    return render(request, 'gastos_compartidos/form.html', context)

@login_required
def gasto_compartido_eliminar(request, pk):
    """Eliminar un gasto compartido"""
    gasto = get_object_or_404(GastoCompartido, pk=pk, grupo__miembros=request.user)
    
    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto compartido eliminado exitosamente.')
        return redirect('gastos_compartidos_lista')
    
    context = {
        'gasto': gasto,
    }
    return render(request, 'gastos_compartidos/eliminar.html', context)

@login_required
def gasto_compartido_detalle(request, pk):
    """Ver detalles de un gasto compartido"""
    gasto = get_object_or_404(GastoCompartido, pk=pk, grupo__miembros=request.user)
    pagos = PagoGastoCompartido.objects.filter(gasto_compartido=gasto).select_related('miembro')
    
    context = {
        'gasto': gasto,
        'pagos': pagos,
    }
    return render(request, 'gastos_compartidos/detalle.html', context)

@login_required
def pago_gasto_compartido_editar(request, pk):
    """Editar el pago de un miembro para un gasto compartido"""
    pago = get_object_or_404(PagoGastoCompartido, pk=pk, miembro=request.user)
    
    if request.method == 'POST':
        form = PagoGastoCompartidoForm(request.POST, instance=pago)
        if form.is_valid():
            # El save() del modelo ya actualiza automáticamente el estado
            form.save()
            messages.success(request, 'Pago actualizado exitosamente.')
            return redirect('gasto_compartido_detalle', pk=pago.gasto_compartido.pk)
    else:
        form = PagoGastoCompartidoForm(instance=pago)
    
    context = {
        'form': form,
        'pago': pago,
        'titulo': 'Editar Pago',
    }
    return render(request, 'gastos_compartidos/pago_form.html', context)

@login_required
def dashboard_gastos_compartidos(request):
    """Vista unificada para toda la gestión de gastos compartidos"""
    from decimal import Decimal
    from datetime import date
    
    # Acciones posibles: crear/editar/eliminar grupo, gasto, pago, miembros, ver detalles, etc.
    accion = request.GET.get('accion') or request.POST.get('accion')
    grupo_id = request.GET.get('grupo_id') or request.POST.get('grupo_id')
    gasto_id = request.GET.get('gasto_id') or request.POST.get('gasto_id')
    pago_id = request.GET.get('pago_id') or request.POST.get('pago_id')
    miembro_id = request.GET.get('miembro_id') or request.POST.get('miembro_id')
    contexto_extra = {}

    # --- Gestión de Grupos ---
    if accion == 'crear_grupo':
        if request.method == 'POST':
            form = GrupoGastosCompartidosForm(request.POST, user=request.user)
            if form.is_valid():
                grupo = form.save()
                messages.success(request, 'Grupo creado exitosamente.')
                return redirect('dashboard_gastos_compartidos')
        else:
            form = GrupoGastosCompartidosForm(user=request.user)
        contexto_extra['form_grupo'] = form
        contexto_extra['modal'] = 'grupo'

    elif accion == 'editar_grupo' and grupo_id:
        grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, creador=request.user)
        if request.method == 'POST':
            form = GrupoGastosCompartidosForm(request.POST, instance=grupo, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Grupo actualizado exitosamente.')
                return redirect('dashboard_gastos_compartidos')
        else:
            form = GrupoGastosCompartidosForm(instance=grupo, user=request.user)
        contexto_extra['form_grupo'] = form
        contexto_extra['grupo_editar'] = grupo
        contexto_extra['modal'] = 'grupo'

    elif accion == 'eliminar_grupo' and grupo_id:
        grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, creador=request.user)
        if request.method == 'POST':
            grupo.activo = False
            grupo.save()
            messages.success(request, 'Grupo eliminado exitosamente.')
            return redirect('dashboard_gastos_compartidos')
        contexto_extra['grupo_eliminar'] = grupo
        contexto_extra['modal'] = 'eliminar_grupo'

    # --- Gestión de Gastos ---
    elif accion == 'crear_gasto':
        grupos = GrupoGastosCompartidos.objects.filter(miembros=request.user, activo=True)
        if request.method == 'POST':
            grupo = get_object_or_404(GrupoGastosCompartidos, pk=request.POST.get('grupo'), miembros=request.user)
            form = GastoCompartidoForm(request.POST, request.FILES, user=request.user, grupo=grupo)
            if form.is_valid():
                gasto = form.save(commit=False)
                gasto.grupo = grupo
                gasto.save()
                # Crear pagos para cada miembro
                pagado_por_usuario = gasto.pagado_por
                for miembro in grupo.miembros.all():
                    monto_debido_miembro = gasto.monto_por_persona
                    monto_pagado_miembro = Decimal('0')
                    if pagado_por_usuario and miembro == pagado_por_usuario:
                        monto_pagado_miembro = monto_debido_miembro
                    PagoGastoCompartido.objects.create(
                        gasto_compartido=gasto,
                        miembro=miembro,
                        monto_debido=monto_debido_miembro,
                        monto_pagado=monto_pagado_miembro
                    )
                messages.success(request, 'Gasto creado exitosamente.')
                return redirect('dashboard_gastos_compartidos')
        else:
            grupo_pre = request.GET.get('grupo')
            if grupo_pre:
                grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_pre, miembros=request.user, activo=True)
                form = GastoCompartidoForm(user=request.user, grupo=grupo)
            else:
                form = GastoCompartidoForm(user=request.user, grupo=grupos.first())
        contexto_extra['form_gasto'] = form
        contexto_extra['grupos'] = grupos
        contexto_extra['modal'] = 'gasto'

    elif accion == 'editar_gasto' and gasto_id:
        gasto = get_object_or_404(GastoCompartido, pk=gasto_id, grupo__miembros=request.user)
        if request.method == 'POST':
            form = GastoCompartidoForm(request.POST, request.FILES, instance=gasto, user=request.user, grupo=gasto.grupo)
            if form.is_valid():
                form.save()
                messages.success(request, 'Gasto actualizado exitosamente.')
                return redirect('dashboard_gastos_compartidos')
        else:
            form = GastoCompartidoForm(instance=gasto, user=request.user, grupo=gasto.grupo)
        contexto_extra['form_gasto'] = form
        contexto_extra['gasto_editar'] = gasto
        contexto_extra['modal'] = 'gasto'

    elif accion == 'eliminar_gasto' and gasto_id:
        gasto = get_object_or_404(GastoCompartido, pk=gasto_id, grupo__miembros=request.user)
        if request.method == 'POST':
            gasto.delete()
            messages.success(request, 'Gasto eliminado exitosamente.')
            return redirect('dashboard_gastos_compartidos')
        contexto_extra['gasto_eliminar'] = gasto
        contexto_extra['modal'] = 'eliminar_gasto'

    # --- Gestión de Pagos ---
    elif accion == 'editar_pago' and pago_id:
        pago = get_object_or_404(PagoGastoCompartido, pk=pago_id, miembro=request.user)
        if request.method == 'POST':
            form = PagoGastoCompartidoForm(request.POST, instance=pago)
            if form.is_valid():
                form.save()
                messages.success(request, 'Pago actualizado exitosamente.')
                return redirect('dashboard_gastos_compartidos')
        else:
            form = PagoGastoCompartidoForm(instance=pago)
        contexto_extra['form_pago'] = form
        contexto_extra['pago_editar'] = pago
        contexto_extra['modal'] = 'pago'

    # --- Gestión de Miembros ---
    elif accion == 'gestionar_miembros' and grupo_id:
        grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, creador=request.user, activo=True)
        if request.method == 'POST':
            accion_miembro = request.POST.get('accion_miembro')
            usuario_id = request.POST.get('usuario_id')
            if accion_miembro == 'agregar' and usuario_id:
                try:
                    usuario = User.objects.get(id=usuario_id, is_active=True)
                    if usuario not in grupo.miembros.all():
                        grupo.miembros.add(usuario)
                        messages.success(request, f'Usuario {usuario.username} agregado al grupo exitosamente.')
                    else:
                        messages.warning(request, f'El usuario {usuario.username} ya es miembro del grupo.')
                except User.DoesNotExist:
                    messages.error(request, 'Usuario no encontrado.')
            elif accion_miembro == 'remover' and usuario_id:
                try:
                    usuario = User.objects.get(id=usuario_id)
                    if usuario == request.user:
                        messages.error(request, 'No puedes removerte a ti mismo del grupo.')
                    else:
                        grupo.miembros.remove(usuario)
                        messages.success(request, f'Usuario {usuario.username} removido del grupo exitosamente.')
                except User.DoesNotExist:
                    messages.error(request, 'Usuario no encontrado.')
            return redirect('dashboard_gastos_compartidos')
        usuarios_disponibles = User.objects.filter(is_active=True).exclude(id__in=grupo.miembros.values_list('id', flat=True)).exclude(id=request.user.id)
        contexto_extra['grupo_miembros'] = grupo
        contexto_extra['miembros'] = grupo.miembros.all()
        contexto_extra['usuarios_disponibles'] = usuarios_disponibles
        contexto_extra['modal'] = 'miembros'

    # --- Saldos de Grupo ---
    elif accion == 'saldos_grupo' and grupo_id:
        grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, miembros=request.user, activo=True)
        saldos = {}
        deudas = []
        gastos_grupo = GastoCompartido.objects.filter(grupo=grupo)
        for miembro in grupo.miembros.all():
            saldo = Decimal('0')
            pagos_realizados = PagoGastoCompartido.objects.filter(
                gasto_compartido__grupo=grupo,
                miembro=miembro,
                estado='pagado'
            ).aggregate(total=Sum('monto_pagado'))['total'] or Decimal('0')
            gastos_debidos = PagoGastoCompartido.objects.filter(
                gasto_compartido__grupo=grupo,
                miembro=miembro
            ).aggregate(total=Sum('monto_debido'))['total'] or Decimal('0')
            saldo = pagos_realizados - gastos_debidos
            saldos[miembro.get_full_name() or miembro.username] = saldo
        miembros_list = list(saldos.items())
        for i, (deudor, saldo_deudor) in enumerate(miembros_list):
            if saldo_deudor < 0:
                for j, (acreedor, saldo_acreedor) in enumerate(miembros_list):
                    if i != j and saldo_acreedor > 0:
                        monto_transferir = min(abs(saldo_deudor), saldo_acreedor)
                        if monto_transferir > 0:
                            deudas.append({
                                'deudor': deudor,
                                'acreedor': acreedor,
                                'monto': monto_transferir
                            })
                            saldos[deudor] += monto_transferir
                            saldos[acreedor] -= monto_transferir
        contexto_extra['grupo_saldos'] = grupo
        contexto_extra['saldos'] = saldos
        contexto_extra['deudas'] = deudas
        contexto_extra['modal'] = 'saldos'

    # --- Estadísticas y dashboard principal ---
    grupos = GrupoGastosCompartidos.objects.filter(miembros=request.user, activo=True)
    total_gastos = GastoCompartido.objects.filter(grupo__miembros=request.user).count()
    gastos_pendientes = GastoCompartido.objects.filter(
        grupo__miembros=request.user, 
        estado='pendiente'
    ).count()
    gastos_vencidos = GastoCompartido.objects.filter(
        grupo__miembros=request.user,
        fecha_vencimiento__lt=date.today(),
        estado='pendiente'
    ).count()
    pagos_pendientes = PagoGastoCompartido.objects.filter(
        miembro=request.user,
        estado__in=['pendiente', 'parcial']
    )
    total_adeudado = sum(pago.monto_pendiente for pago in pagos_pendientes)
    gastos_recientes = GastoCompartido.objects.filter(
        grupo__miembros=request.user
    ).select_related('grupo').order_by('-fecha')[:10]
    pagos_pendientes_usuario = PagoGastoCompartido.objects.filter(
        miembro=request.user,
        estado__in=['pendiente', 'parcial']
    ).select_related('gasto_compartido', 'gasto_compartido__grupo').order_by('gasto_compartido__fecha_vencimiento')[:10]

    context = {
        'grupos': grupos,
        'total_gastos': total_gastos,
        'gastos_pendientes': gastos_pendientes,
        'gastos_vencidos': gastos_vencidos,
        'total_adeudado': total_adeudado,
        'gastos_recientes': gastos_recientes,
        'pagos_pendientes_usuario': pagos_pendientes_usuario,
    }
    context.update(contexto_extra)
    return render(request, 'gastos_compartidos/dashboard.html', context)

@login_required
def lista_notificaciones(request):
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'notificaciones/lista.html', {'notificaciones': notificaciones})

@login_required
@require_POST
def marcar_notificacion_leida(request, pk):
    try:
        notificacion = Notificacion.objects.get(pk=pk, usuario=request.user)
        notificacion.leida = True
        notificacion.save()
        return JsonResponse({'status': 'success'})
    except Notificacion.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notificación no encontrada o no pertenece al usuario'}, status=404)

@login_required
@require_POST
def marcar_todas_notificaciones_leidas(request):
    """Marcar todas las notificaciones del usuario como leídas"""
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return JsonResponse({'success': True})

@login_required
def api_cuentas_usuario(request, user_id):
    """API para obtener las cuentas de un usuario específico"""
    try:
        # Verificar que el usuario existe y está activo
        usuario = get_object_or_404(User, id=user_id, is_active=True)
        
        # Obtener las cuentas activas del usuario
        cuentas = Cuenta.objects.filter(usuario=usuario, activa=True).values('id', 'nombre', 'tipo_cuenta')
        
        return JsonResponse({
            'success': True,
            'cuentas': list(cuentas)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def api_grupo_info(request, grupo_id):
    """API para obtener información de un grupo específico"""
    try:
        # Verificar que el grupo existe y el usuario es miembro
        grupo = get_object_or_404(GrupoGastosCompartidos, id=grupo_id, miembros=request.user, activo=True)
        
        return JsonResponse({
            'success': True,
            'cantidad_miembros': grupo.cantidad_miembros,
            'nombre': grupo.nombre
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def saldos_grupo(request, pk):
    """Mostrar saldos y deudas de un grupo específico"""
    grupo = get_object_or_404(GrupoGastosCompartidos, pk=pk, miembros=request.user, activo=True)
    
    # Calcular saldos de cada miembro
    saldos = {}
    deudas = []
    
    # Obtener todos los gastos del grupo
    gastos_grupo = GastoCompartido.objects.filter(grupo=grupo)
    
    # Calcular saldos por miembro
    for miembro in grupo.miembros.all():
        saldo = Decimal('0')
        
        # Sumar todos los pagos realizados por este miembro
        pagos_realizados = PagoGastoCompartido.objects.filter(
            gasto_compartido__grupo=grupo,
            miembro=miembro,
            estado='pagado'
        ).aggregate(total=Sum('monto_pagado'))['total'] or Decimal('0')
        
        # Sumar todos los gastos que debe pagar este miembro
        gastos_debidos = PagoGastoCompartido.objects.filter(
            gasto_compartido__grupo=grupo,
            miembro=miembro
        ).aggregate(total=Sum('monto_debido'))['total'] or Decimal('0')
        
        saldo = pagos_realizados - gastos_debidos
        saldos[miembro.get_full_name() or miembro.username] = saldo
    
    # Calcular deudas entre miembros
    miembros_list = list(saldos.items())
    for i, (deudor, saldo_deudor) in enumerate(miembros_list):
        if saldo_deudor < 0:  # Si debe dinero
            for j, (acreedor, saldo_acreedor) in enumerate(miembros_list):
                if i != j and saldo_acreedor > 0:  # Si otro miembro tiene saldo positivo
                    monto_transferir = min(abs(saldo_deudor), saldo_acreedor)
                    if monto_transferir > 0:
                        deudas.append({
                            'deudor': deudor,
                            'acreedor': acreedor,
                            'monto': monto_transferir
                        })
                        # Actualizar saldos
                        saldos[deudor] += monto_transferir
                        saldos[acreedor] -= monto_transferir
    
    context = {
        'grupo': grupo,
        'saldos': saldos,
        'deudas': deudas,
    }
    return render(request, 'gastos_compartidos/saldos_grupo.html', context)

@login_required
def miembros_grupo(request, pk):
    """Gestionar miembros de un grupo"""
    grupo = get_object_or_404(GrupoGastosCompartidos, pk=pk, creador=request.user, activo=True)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        usuario_id = request.POST.get('usuario_id')
        
        if accion == 'agregar' and usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id, is_active=True)
                if usuario not in grupo.miembros.all():
                    grupo.miembros.add(usuario)
                    messages.success(request, f'Usuario {usuario.username} agregado al grupo exitosamente.')
                else:
                    messages.warning(request, f'El usuario {usuario.username} ya es miembro del grupo.')
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
        
        elif accion == 'remover' and usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id)
                if usuario == request.user:
                    messages.error(request, 'No puedes removerte a ti mismo del grupo.')
                else:
                    grupo.miembros.remove(usuario)
                    messages.success(request, f'Usuario {usuario.username} removido del grupo exitosamente.')
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
        
        return redirect('miembros_grupo', pk=pk)
    
    # Obtener usuarios disponibles para agregar (excluyendo los que ya están en el grupo)
    usuarios_disponibles = User.objects.filter(
        is_active=True
    ).exclude(
        id__in=grupo.miembros.values_list('id', flat=True)
    ).exclude(id=request.user.id)
    
    context = {
        'grupo': grupo,
        'miembros': grupo.miembros.all(),
        'usuarios_disponibles': usuarios_disponibles,
    }
    return render(request, 'gastos_compartidos/miembros_grupo.html', context)

@login_required
def detalles_gasto(request, pk):
    """Vista alternativa para mostrar detalles de un gasto compartido"""
    gasto = get_object_or_404(GastoCompartido, pk=pk, grupo__miembros=request.user)
    pagos = PagoGastoCompartido.objects.filter(gasto_compartido=gasto).select_related('miembro')
    
    # Calcular estadísticas adicionales
    total_pagado = pagos.filter(estado='pagado').aggregate(total=Sum('monto_pagado'))['total'] or Decimal('0')
    total_pendiente = gasto.monto_total - total_pagado
    porcentaje_pagado = (total_pagado / gasto.monto_total * 100) if gasto.monto_total > 0 else 0
    
    context = {
        'gasto': gasto,
        'pagos': pagos,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'porcentaje_pagado': porcentaje_pagado,
    }
    return render(request, 'gastos_compartidos/detalles_gasto.html', context)

@login_required
def grupo_confirm_delete(request, pk):
    """Confirmación de eliminación de grupo (vista alternativa)"""
    grupo = get_object_or_404(GrupoGastosCompartidos, pk=pk, creador=request.user, activo=True)
    
    # Contar gastos asociados al grupo
    gastos_count = GastoCompartido.objects.filter(grupo=grupo).count()
    
    if request.method == 'POST':
        grupo.activo = False
        grupo.save()
        messages.success(request, 'Grupo eliminado exitosamente.')
        return redirect('grupos_gastos_compartidos_lista')
    
    context = {
        'grupo': grupo,
        'gastos_count': gastos_count,
    }
    return render(request, 'gastos_compartidos/grupo_confirm_delete.html', context)

@login_required
def gastos_compartidos_lista_alternativa(request):
    """Lista alternativa de gastos compartidos"""
    form = FiltroGastosCompartidosForm(request.GET, user=request.user)
    
    # Obtener gastos de grupos donde el usuario es miembro
    gastos = GastoCompartido.objects.filter(grupo__miembros=request.user).select_related('grupo', 'pagado_por')
    
    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data.get('fecha_desde'):
            gastos = gastos.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            gastos = gastos.filter(fecha__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data.get('tipo'):
            gastos = gastos.filter(tipo=form.cleaned_data['tipo'])
        if form.cleaned_data.get('estado'):
            gastos = gastos.filter(estado=form.cleaned_data['estado'])
        if form.cleaned_data.get('grupo'):
            gastos = gastos.filter(grupo=form.cleaned_data['grupo'])
        if form.cleaned_data.get('monto_minimo'):
            gastos = gastos.filter(monto_total__gte=form.cleaned_data['monto_minimo'])
        if form.cleaned_data.get('monto_maximo'):
            gastos = gastos.filter(monto_total__lte=form.cleaned_data['monto_maximo'])
    
    # Paginación
    paginator = Paginator(gastos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_gastos': gastos.count(),
    }
    return render(request, 'gastos_compartidos/gastos_compartidos_lista.html', context)

@login_required
def crear_editar_gasto_alternativo(request, pk=None):
    """Vista alternativa para crear/editar gastos compartidos"""
    grupos = GrupoGastosCompartidos.objects.filter(miembros=request.user, activo=True)
    
    if not grupos.exists():
        messages.error(request, 'Debe crear un grupo de gastos compartidos antes de agregar gastos.')
        return redirect('grupos_gastos_compartidos_lista')
    
    if pk:
        # Editar gasto existente
        gasto = get_object_or_404(GastoCompartido, pk=pk, grupo__miembros=request.user)
        titulo = 'Editar Gasto Compartido'
    else:
        # Crear nuevo gasto
        gasto = None
        titulo = 'Nuevo Gasto Compartido'
    
    if request.method == 'POST':
        grupo_id = request.POST.get('grupo')
        grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, miembros=request.user)
        form = GastoCompartidoForm(request.POST, request.FILES, instance=gasto, user=request.user, grupo=grupo)
        
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.grupo = grupo
            gasto.save()
            
            # Si es un gasto nuevo, crear registros de pago
            if not pk:
                # Determinar quién pagó el gasto
                pagado_por_usuario = gasto.pagado_por
                
                # Crear registros de pago para cada miembro
                for miembro in grupo.miembros.all():
                    monto_debido_miembro = gasto.monto_por_persona
                    monto_pagado_miembro = Decimal('0')
                    
                    # Si este miembro es quien pagó, registrar su pago
                    if pagado_por_usuario and miembro == pagado_por_usuario:
                        monto_pagado_miembro = monto_debido_miembro
                    
                    PagoGastoCompartido.objects.create(
                        gasto_compartido=gasto,
                        miembro=miembro,
                        monto_debido=monto_debido_miembro,
                        monto_pagado=monto_pagado_miembro
                    )
                
                # Crear notificaciones para los miembros (excepto el creador)
                url_gasto = reverse('gasto_compartido_detalle', args=[gasto.pk])
                for miembro in grupo.miembros.all():
                    if miembro != request.user:
                        Notificacion.objects.create(
                            usuario=miembro,
                            mensaje=f"{request.user.username} ha añadido un nuevo gasto en '{grupo.nombre}': {gasto.titulo}.",
                            url_destino=url_gasto
                        )
            
            messages.success(request, 'Gasto compartido guardado exitosamente.')
            return redirect('gastos_compartidos_lista')
    else:
        # Pre-seleccionar grupo si viene como parámetro GET
        grupo_id = request.GET.get('grupo')
        if grupo_id:
            grupo = get_object_or_404(GrupoGastosCompartidos, pk=grupo_id, miembros=request.user, activo=True)
            form = GastoCompartidoForm(user=request.user, grupo=grupo, instance=gasto)
        else:
            form = GastoCompartidoForm(user=request.user, grupo=grupos.first(), instance=gasto)
    
    context = {
        'form': form,
        'grupos': grupos,
        'gasto': gasto,
        'titulo': titulo,
    }
    return render(request, 'gastos_compartidos/crear_editar_gasto.html', context)

@login_required
def eliminar_gasto_alternativo(request, pk):
    """Vista alternativa para eliminar gastos compartidos"""
    gasto = get_object_or_404(GastoCompartido, pk=pk, grupo__miembros=request.user)
    
    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto compartido eliminado exitosamente.')
        return redirect('gastos_compartidos_lista')
    
    context = {
        'gasto': gasto,
    }
    return render(request, 'gastos_compartidos/eliminar_gasto.html', context)

# APIs para Gastos Compartidos
@login_required
def api_grupo_miembros(request, grupo_id):
    """API para obtener los miembros de un grupo"""
    try:
        grupo = get_object_or_404(GrupoGastosCompartidos, id=grupo_id, miembros=request.user, activo=True)
        miembros = []
        for miembro in grupo.miembros.all():
            miembros.append({
                'id': miembro.id,
                'nombre': miembro.get_full_name() or miembro.username,
                'username': miembro.username
            })
        
        return JsonResponse({
            'success': True,
            'miembros': miembros
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def api_crear_grupo(request):
    """API para crear un grupo desde el modal"""
    try:
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        color = request.POST.get('color', '#667eea')
        
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre del grupo es requerido'
            }, status=400)
        
        grupo = GrupoGastosCompartidos.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            color=color,
            creador=request.user
        )
        grupo.miembros.add(request.user)
        
        return JsonResponse({
            'success': True,
            'grupo_id': grupo.id,
            'message': 'Grupo creado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def api_crear_gasto(request):
    """API para crear un gasto desde el modal"""
    try:
        from datetime import datetime
        
        grupo_id = request.POST.get('grupo')
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion', '')
        monto_total = request.POST.get('monto_total')
        fecha = request.POST.get('fecha')
        fecha_vencimiento = request.POST.get('fecha_vencimiento')
        pagado_por_id = request.POST.get('pagado_por')
        
        if not all([grupo_id, titulo, monto_total, fecha]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos obligatorios deben estar completos'
            }, status=400)
        
        grupo = get_object_or_404(GrupoGastosCompartidos, id=grupo_id, miembros=request.user, activo=True)
        pagado_por = None
        if pagado_por_id:
            pagado_por = get_object_or_404(User, id=pagado_por_id)
        
        # Convertir fechas de string a objetos date
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        fecha_vencimiento_obj = None
        if fecha_vencimiento:
            fecha_vencimiento_obj = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
        
        gasto = GastoCompartido.objects.create(
            grupo=grupo,
            titulo=titulo,
            descripcion=descripcion,
            monto_total=monto_total,
            fecha=fecha_obj,
            fecha_vencimiento=fecha_vencimiento_obj,
            pagado_por=pagado_por
        )
        
        # Crear registros de pago para cada miembro
        for miembro in grupo.miembros.all():
            monto_debido_miembro = gasto.monto_por_persona
            monto_pagado_miembro = Decimal('0')
            
            if pagado_por and miembro == pagado_por:
                monto_pagado_miembro = monto_debido_miembro
            
            PagoGastoCompartido.objects.create(
                gasto_compartido=gasto,
                miembro=miembro,
                monto_debido=monto_debido_miembro,
                monto_pagado=monto_pagado_miembro
            )
        
        return JsonResponse({
            'success': True,
            'gasto_id': gasto.id,
            'message': 'Gasto creado exitosamente'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Error en el formato de fecha: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def api_editar_pago(request):
    """API para editar un pago desde el modal"""
    try:
        pago_id = request.POST.get('pago_id')
        monto_pagado = request.POST.get('monto_pagado')
        estado = request.POST.get('estado')
        notas = request.POST.get('comentario', '')  # El campo en el formulario se llama 'comentario'
        
        if not all([pago_id, monto_pagado, estado]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos obligatorios deben estar completos'
            }, status=400)
        
        pago = get_object_or_404(PagoGastoCompartido, id=pago_id, miembro=request.user)
        pago.monto_pagado = monto_pagado
        pago.estado = estado
        pago.notas = notas  # El campo en el modelo se llama 'notas'
        pago.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Pago actualizado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


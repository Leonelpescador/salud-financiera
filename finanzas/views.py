from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Transaccion, Categoria, Cuenta, Tag, ConfiguracionUsuario, Presupuesto, Meta, CorteMes
from .forms import TransaccionForm, CategoriaForm, CuentaForm, TagForm, FiltroTransaccionesForm, PresupuestoForm, MetaForm
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from calendar import monthrange
import json

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'login/login.html')

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


from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Transaccion, Categoria, Cuenta, Tag, ConfiguracionUsuario, Presupuesto, Meta, GrupoGastosCompartidos, GastoCompartido, PagoGastoCompartido
from django.utils import timezone
from datetime import date
from django.core.exceptions import ValidationError
from decimal import Decimal

class TransaccionForm(forms.ModelForm):
    es_en_cuotas = forms.BooleanField(required=False, label='¿Es en cuotas?')
    numero_cuotas = forms.IntegerField(required=False, min_value=1, label='Cantidad de cuotas')
    cuota_actual = forms.IntegerField(required=False, min_value=1, label='¿En qué cuota va?')
    fecha_fin_cuotas = forms.DateField(required=False, label='Fecha de finalización de cuotas')
    class Meta:
        model = Transaccion
        fields = ['monto', 'fecha', 'tipo', 'descripcion', 'categoria', 'cuenta', 'tags', 'es_recurrente', 'frecuencia_recurrencia', 'cuenta_destino', 'imagen_recibo', 'es_en_cuotas', 'numero_cuotas', 'cuota_actual', 'fecha_fin_cuotas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción de la transacción'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'cuenta': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'cuenta_destino': forms.Select(attrs={'class': 'form-control'}),
            'imagen_recibo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar categorías y cuentas por usuario
            self.fields['categoria'].queryset = Categoria.objects.filter(usuario=user, activa=True)
            self.fields['cuenta'].queryset = Cuenta.objects.filter(usuario=user, activa=True)
            self.fields['cuenta_destino'].queryset = Cuenta.objects.filter(usuario=user, activa=True)
            self.fields['tags'].queryset = Tag.objects.filter(usuario=user)
            
            # Establecer fecha por defecto
            if not self.instance.pk:
                self.fields['fecha'].initial = date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cuenta_destino = cleaned_data.get('cuenta_destino')
        es_en_cuotas = cleaned_data.get('es_en_cuotas')
        numero_cuotas = cleaned_data.get('numero_cuotas')
        cuota_actual = cleaned_data.get('cuota_actual')
        
        # Validar que para transferencias se especifique cuenta destino
        if tipo == 'transferencia' and not cuenta_destino:
            raise forms.ValidationError("Para transferencias debe especificar una cuenta destino.")
        
        # Validar que cuenta origen y destino sean diferentes
        cuenta_origen = cleaned_data.get('cuenta')
        if tipo == 'transferencia' and cuenta_origen == cuenta_destino:
            raise forms.ValidationError("La cuenta origen y destino deben ser diferentes.")
        
        if es_en_cuotas:
            if not numero_cuotas or not cuota_actual:
                raise forms.ValidationError('Debe indicar la cantidad de cuotas y la cuota actual.')
            if cuota_actual > numero_cuotas:
                raise forms.ValidationError('La cuota actual no puede ser mayor que el número de cuotas.')
        
        return cleaned_data

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'icono', 'color', 'tipo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'}),
            'icono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '📊'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.instance.usuario = user

class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['nombre', 'tipo_cuenta', 'moneda', 'saldo_inicial', 'icono', 'color', 'descripcion', 'institucion_financiera', 'activa', 'fecha_cierre', 'fecha_vencimiento', 'limite_credito']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la cuenta'}),
            'tipo_cuenta': forms.Select(attrs={'class': 'form-control'}),
            'moneda': forms.Select(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'icono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '💳'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la cuenta (opcional)'}),
            'institucion_financiera': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Banco o institución financiera'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'fecha_cierre': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'limite_credito': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Límite de crédito'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.instance.usuario = user

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['nombre', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del tag'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.instance.usuario = user

class FiltroTransaccionesForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    tipo = forms.ChoiceField(
        choices=[('', 'Todos')] + Transaccion.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cuenta = forms.ModelChoiceField(
        queryset=Cuenta.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    monto_minimo = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto mínimo'})
    )
    monto_maximo = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto máximo'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['categoria'].queryset = Categoria.objects.filter(usuario=user, activa=True)
            self.fields['cuenta'].queryset = Cuenta.objects.filter(usuario=user, activa=True) 

class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['nombre', 'descripcion', 'monto_objetivo', 'periodo', 'fecha_inicio', 'fecha_fin', 'estado', 'categorias', 'notificar_al_80', 'notificar_al_100', 'color', 'icono']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre del presupuesto'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción del presupuesto'}),
            'monto_objetivo': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['categorias'].queryset = Categoria.objects.filter(usuario=user, activa=True, tipo__in=['gasto', 'ambos'])

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        return cleaned_data

class MetaForm(forms.ModelForm):
    class Meta:
        model = Meta
        fields = ['nombre', 'descripcion', 'tipo', 'monto_objetivo', 'fecha_objetivo', 'estado', 'cuenta', 'notificar_al_80', 'notificar_al_100', 'color', 'icono']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre de la meta'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción de la meta'}),
            'monto_objetivo': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'fecha_objetivo': forms.DateInput(attrs={'type': 'date'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(usuario=user, activa=True)

    def clean_fecha_objetivo(self):
        fecha_objetivo = self.cleaned_data['fecha_objetivo']
        
        if fecha_objetivo and fecha_objetivo < date.today():
            raise ValidationError('La fecha objetivo no puede ser anterior a hoy.')
        
        return fecha_objetivo

# Formularios para gestión de usuarios
class UsuarioCrearForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }

class UsuarioEditarForm(UserChangeForm):
    password = None  # No mostrar campo de contraseña en edición
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }

class ConfiguracionUsuarioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionUsuario
        fields = ['moneda_principal', 'zona_horaria', 'notificaciones_activas', 'recordatorios_pago']
        widgets = {
            'moneda_principal': forms.Select(attrs={'class': 'form-control'}),
            'zona_horaria': forms.Select(attrs={'class': 'form-control'}),
            'notificaciones_activas': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'recordatorios_pago': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }

class ConfiguracionSistemaForm(forms.Form):
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
    
    ZONA_HORARIA_CHOICES = [
        ('America/Argentina/Buenos_Aires', 'Argentina (Buenos Aires)'),
        ('America/New_York', 'Estados Unidos (Nueva York)'),
        ('Europe/Madrid', 'España (Madrid)'),
        ('America/Sao_Paulo', 'Brasil (São Paulo)'),
        ('America/Santiago', 'Chile (Santiago)'),
        ('America/Bogota', 'Colombia (Bogotá)'),
        ('America/Mexico_City', 'México (Ciudad de México)'),
        ('America/Lima', 'Perú (Lima)'),
        ('America/Montevideo', 'Uruguay (Montevideo)'),
        ('America/Caracas', 'Venezuela (Caracas)'),
    ]
    
    moneda_principal = forms.ChoiceField(
        choices=MONEDA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    zona_horaria = forms.ChoiceField(
        choices=ZONA_HORARIA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notificaciones_activas = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control'})
    )
    recordatorios_pago = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control'})
    )

class RegistroPublicoForm(UserCreationForm):
    """Formulario para registro público de usuarios (marcados como inactivos)"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar mensajes de ayuda
        self.fields['username'].help_text = 'Requerido. 150 caracteres o menos. Solo letras, dígitos y @/./+/-/_'
        self.fields['password1'].help_text = 'Tu contraseña debe contener al menos 8 caracteres.'
        self.fields['password2'].help_text = 'Ingresa la misma contraseña que antes, para verificación.'
        
        # Ocultar mensajes de ayuda por defecto
        for field in self.fields.values():
            field.help_text = ''
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Marcar como inactivo por defecto
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        
        if commit:
            user.save()
        return user
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

class GrupoGastosCompartidosForm(forms.ModelForm):
    # Campo adicional para seleccionar miembros
    miembros = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Selecciona los usuarios que formarán parte del grupo"
    )
    
    class Meta:
        model = GrupoGastosCompartidos
        fields = ['nombre', 'descripcion', 'icono', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del grupo (ej: Casa, Departamento)'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del grupo'}),
            'icono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '🏠'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.instance.creador = user
            # Excluir al usuario actual de la lista de miembros (ya se agrega automáticamente)
            self.fields['miembros'].queryset = User.objects.filter(is_active=True).exclude(id=user.id)
            
            # Si es una edición, pre-seleccionar los miembros actuales
            if self.instance.pk:
                self.fields['miembros'].initial = self.instance.miembros.exclude(id=user.id)
    
    def save(self, commit=True):
        grupo = super().save(commit=False)
        if commit:
            grupo.save()
            # Agregar el creador como miembro si no está ya
            grupo.miembros.add(self.instance.creador)
            # Agregar los miembros seleccionados
            if self.cleaned_data.get('miembros'):
                grupo.miembros.add(*self.cleaned_data['miembros'])
        return grupo

class GastoCompartidoForm(forms.ModelForm):
    es_en_cuotas = forms.BooleanField(required=False, label='¿Es en cuotas?')
    numero_cuotas = forms.IntegerField(required=False, min_value=1, label='Cantidad de cuotas')
    cuota_actual = forms.IntegerField(required=False, min_value=1, label='¿En qué cuota va?')
    fecha_fin_cuotas = forms.DateField(required=False, label='Fecha de finalización de cuotas')
    # Campo adicional para especificar cuánto pagó inicialmente quien pagó
    monto_pagado_inicial = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Monto que pagó inicialmente (opcional)'
        }),
        help_text="Si quien pagó solo pagó una parte del gasto, especifica cuánto pagó. Si no especificas, se asume que pagó todo."
    )
    
    class Meta:
        model = GastoCompartido
        fields = ['grupo', 'titulo', 'descripcion', 'monto_total', 'fecha', 'fecha_vencimiento', 'tipo', 'estado', 'pagado_por', 'cuenta_pago', 'imagen_recibo', 'monto_pagado_inicial', 'es_en_cuotas', 'numero_cuotas', 'cuota_actual', 'fecha_fin_cuotas']
        widgets = {
            'grupo': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del gasto compartido'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del gasto'}),
            'monto_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': 'Monto total'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'pagado_por': forms.Select(attrs={'class': 'form-control'}),
            'cuenta_pago': forms.Select(attrs={'class': 'form-control'}),
            'imagen_recibo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        grupo = kwargs.pop('grupo', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar grupos del usuario para el campo grupo
            self.fields['grupo'].queryset = GrupoGastosCompartidos.objects.filter(miembros=user, activo=True)
            
            # Si se pasa un grupo específico, pre-seleccionarlo
            if grupo:
                self.fields['grupo'].initial = grupo
                # Filtrar miembros del grupo para el campo pagado_por
                self.fields['pagado_por'].queryset = grupo.miembros.all()
            else:
                # Si no hay grupo específico, usar el primer grupo disponible
                grupos_usuario = GrupoGastosCompartidos.objects.filter(miembros=user, activo=True)
                if grupos_usuario.exists():
                    primer_grupo = grupos_usuario.first()
                    self.fields['grupo'].initial = primer_grupo
                    self.fields['pagado_por'].queryset = primer_grupo.miembros.all()
                else:
                    self.fields['pagado_por'].queryset = User.objects.none()
            
            # Filtrar cuentas del usuario que pagó
            if self.instance.pk and self.instance.pagado_por:
                self.fields['cuenta_pago'].queryset = Cuenta.objects.filter(usuario=self.instance.pagado_por, activa=True)
            else:
                # Por defecto, mostrar las cuentas del usuario actual
                self.fields['cuenta_pago'].queryset = Cuenta.objects.filter(usuario=user, activa=True)
            
            # Establecer fecha por defecto
            if not self.instance.pk:
                self.fields['fecha'].initial = date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        pagado_por = cleaned_data.get('pagado_por')
        cuenta_pago = cleaned_data.get('cuenta_pago')
        fecha = cleaned_data.get('fecha')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        monto_total = cleaned_data.get('monto_total')
        monto_pagado_inicial = cleaned_data.get('monto_pagado_inicial')
        es_en_cuotas = cleaned_data.get('es_en_cuotas')
        numero_cuotas = cleaned_data.get('numero_cuotas')
        cuota_actual = cleaned_data.get('cuota_actual')
        
        # Validar que la cuenta de pago pertenezca al usuario que pagó
        if pagado_por and cuenta_pago and cuenta_pago.usuario != pagado_por:
            raise forms.ValidationError("La cuenta de pago debe pertenecer al usuario que pagó el gasto.")
        
        # Validar que la fecha de vencimiento sea posterior a la fecha del gasto
        if fecha and fecha_vencimiento and fecha_vencimiento <= fecha:
            raise forms.ValidationError("La fecha de vencimiento debe ser posterior a la fecha del gasto.")
        
        # Validar que la fecha de vencimiento no sea futura si el gasto ya está pagado
        if fecha_vencimiento and fecha_vencimiento > date.today():
            estado = cleaned_data.get('estado')
            if estado == 'pagado':
                raise forms.ValidationError("Un gasto pagado no puede tener fecha de vencimiento futura.")
        
        # Validar que el monto total sea razonable
        if monto_total and monto_total > Decimal('999999.99'):
            raise forms.ValidationError("El monto total no puede exceder $999,999.99")
        
        # Validar que el monto pagado inicial no exceda el monto total
        if monto_pagado_inicial and monto_total:
            if monto_pagado_inicial > monto_total:
                raise forms.ValidationError("El monto pagado inicial no puede exceder el monto total del gasto.")
        
        if es_en_cuotas:
            if not numero_cuotas or not cuota_actual:
                raise forms.ValidationError('Debe indicar la cantidad de cuotas y la cuota actual.')
            if cuota_actual > numero_cuotas:
                raise forms.ValidationError('La cuota actual no puede ser mayor que el número de cuotas.')
        
        return cleaned_data

class PagoGastoCompartidoForm(forms.ModelForm):
    class Meta:
        model = PagoGastoCompartido
        fields = ['monto_pagado', 'fecha_pago', 'estado', 'notas']
        widgets = {
            'monto_pagado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Monto pagado'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales'}),
        }
    
    def __init__(self, *args, **kwargs):
        pago = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        if pago:
            # Establecer el monto máximo que puede pagar
            self.fields['monto_pagado'].widget.attrs['max'] = pago.monto_debido
            # Establecer fecha por defecto
            if not pago.fecha_pago:
                self.fields['fecha_pago'].initial = date.today()
    
    def clean_monto_pagado(self):
        monto_pagado = self.cleaned_data.get('monto_pagado')
        if self.instance and monto_pagado > self.instance.monto_debido:
            raise forms.ValidationError(f"No puede pagar más de ${self.instance.monto_debido}")
        if monto_pagado < 0:
            raise forms.ValidationError("El monto pagado no puede ser negativo")
        return monto_pagado
    
    def clean_fecha_pago(self):
        fecha_pago = self.cleaned_data.get('fecha_pago')
        if fecha_pago and fecha_pago > date.today():
            raise forms.ValidationError("La fecha de pago no puede ser futura")
        return fecha_pago
    
    def clean(self):
        cleaned_data = super().clean()
        monto_pagado = cleaned_data.get('monto_pagado')
        fecha_pago = cleaned_data.get('fecha_pago')
        
        # Si se especifica un monto pagado, la fecha de pago es obligatoria
        if monto_pagado and monto_pagado > 0 and not fecha_pago:
            raise forms.ValidationError("Debe especificar la fecha de pago cuando registra un monto pagado")
        
        return cleaned_data

class FiltroGastosCompartidosForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    tipo = forms.ChoiceField(
        choices=[('', 'Todos')] + GastoCompartido.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos')] + GastoCompartido.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    grupo = forms.ModelChoiceField(
        queryset=GrupoGastosCompartidos.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    monto_minimo = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto mínimo'})
    )
    monto_maximo = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto máximo'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['grupo'].queryset = GrupoGastosCompartidos.objects.filter(miembros=user, activo=True) 
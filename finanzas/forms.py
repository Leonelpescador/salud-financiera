from django import forms
from django.contrib.auth.models import User
from .models import Transaccion, Categoria, Cuenta, Tag, ConfiguracionUsuario, Presupuesto, Meta
from django.utils import timezone
from datetime import date
from django.core.exceptions import ValidationError
from decimal import Decimal

class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['monto', 'fecha', 'tipo', 'descripcion', 'categoria', 'cuenta', 'tags', 'es_recurrente', 'frecuencia_recurrencia', 'cuenta_destino', 'imagen_recibo']
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
        
        # Validar que para transferencias se especifique cuenta destino
        if tipo == 'transferencia' and not cuenta_destino:
            raise forms.ValidationError("Para transferencias debe especificar una cuenta destino.")
        
        # Validar que cuenta origen y destino sean diferentes
        cuenta_origen = cleaned_data.get('cuenta')
        if tipo == 'transferencia' and cuenta_origen == cuenta_destino:
            raise forms.ValidationError("La cuenta origen y destino deben ser diferentes.")
        
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
        fields = ['nombre', 'tipo_cuenta', 'saldo_inicial', 'icono', 'color', 'fecha_cierre', 'fecha_vencimiento', 'limite_credito']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la cuenta'}),
            'tipo_cuenta': forms.Select(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'icono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '💳'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'fecha_cierre': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'limite_credito': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
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
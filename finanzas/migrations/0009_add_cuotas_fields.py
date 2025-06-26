from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('finanzas', '0008_alter_configuracionusuario_moneda_principal_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaccion',
            name='es_en_cuotas',
            field=models.BooleanField(default=False, help_text='¿Este gasto es en cuotas?'),
        ),
        migrations.AddField(
            model_name='transaccion',
            name='numero_cuotas',
            field=models.PositiveIntegerField(null=True, blank=True, help_text='Cantidad total de cuotas'),
        ),
        migrations.AddField(
            model_name='transaccion',
            name='cuota_actual',
            field=models.PositiveIntegerField(null=True, blank=True, help_text='Número de la cuota actual'),
        ),
        migrations.AddField(
            model_name='transaccion',
            name='fecha_fin_cuotas',
            field=models.DateField(null=True, blank=True, help_text='Fecha de finalización de las cuotas'),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='es_en_cuotas',
            field=models.BooleanField(default=False, help_text='¿Este gasto es en cuotas?'),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='numero_cuotas',
            field=models.PositiveIntegerField(null=True, blank=True, help_text='Cantidad total de cuotas'),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='cuota_actual',
            field=models.PositiveIntegerField(null=True, blank=True, help_text='Número de la cuota actual'),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='fecha_fin_cuotas',
            field=models.DateField(null=True, blank=True, help_text='Fecha de finalización de las cuotas'),
        ),
    ] 
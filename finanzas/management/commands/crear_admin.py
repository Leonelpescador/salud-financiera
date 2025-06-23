from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from finanzas.models import ConfiguracionUsuario

class Command(BaseCommand):
    help = 'Crea un usuario administrador con permisos de staff y superusuario'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('email', type=str, help='Email del usuario')
        parser.add_argument('password', type=str, help='Contraseña del usuario')
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Crear como superusuario (acceso completo al sistema)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        is_superuser = options['superuser']

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'El usuario "{username}" ya existe.')
            )
            return

        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=is_superuser
        )

        # Crear configuración para el usuario
        ConfiguracionUsuario.objects.create(
            usuario=user,
            moneda_principal='ARS',
            zona_horaria='America/Argentina/Buenos_Aires',
            notificaciones_activas=True,
            recordatorios_pago=True
        )

        # Mensaje de confirmación
        user_type = "superusuario" if is_superuser else "administrador"
        self.stdout.write(
            self.style.SUCCESS(
                f'Usuario "{username}" creado exitosamente como {user_type}.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Email: {email}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Permisos: Staff={user.is_staff}, Superusuario={user.is_superuser}'
            )
        ) 
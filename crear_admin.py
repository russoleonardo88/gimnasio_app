import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gimnasio_app.settings')
django.setup()

from django.contrib.auth.models import User

# Cambiá 'admin' y 'tu_password' por lo que quieras usar
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'tu_password_aqui')
    print("Superusuario creado con éxito")
else:
    print("El superusuario ya existe")
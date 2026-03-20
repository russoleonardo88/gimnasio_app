import os
import dj_database_url 
from pathlib import Path

# --- RUTAS BÁSICAS ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-3*r893bw)ik7h=!fd$x7ky$hiigyx@dy+*772wv^&e2t#hn#f&')

# DEBUG debe ser False en Render. Configuralo en el Dashboard de Render como Variable de Entorno.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['gimnasio-app-ftq4.onrender.com', 'localhost', '127.0.0.1', '.onrender.com']

# --- APLICACIONES ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'alumnos',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gimnasio_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gimnasio_app.wsgi.application'

# --- BASE DE DATOS (NEON / SQLITE) ---
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{os.path.join(BASE_DIR, "db.sqlite3")}',
        conn_max_age=600
    )
}

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- CONFIGURACIÓN DE LOGIN ---
LOGIN_REDIRECT_URL = 'dashboard_alumno'
LOGIN_URL = 'login'

# --- CONFIGURACIÓN DE SESIONES ---
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 31536000 
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# --- SEGURIDAD CSRF PARA RENDER ---
CSRF_TRUSTED_ORIGINS = [
    'https://gimnasio-app-ftq4.onrender.com',
    'https://*.onrender.com'
]

# --- BLOQUE PARA PRODUCCIÓN (RENDER / APK) ---
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'None'
    CSRF_COOKIE_SAMESITE = 'None'
    
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # IMPORTANTE: Desactivado para evitar que la página se quede cargando infinito en Render
    SECURE_SSL_REDIRECT = False 
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- LÓGICA DE AUTO-CREACIÓN DE USUARIOS EN EL DEPLOY ---
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def crear_usuarios_iniciales(sender, **kwargs):
    # Verificamos por el nombre de la app para evitar duplicidad
    if sender.name == 'alumnos': 
        from django.contrib.auth.models import User
        # Crear Superusuario (Mariano)
        if not User.objects.filter(username='Mariano').exists():
            User.objects.create_superuser('Mariano', 'admin@example.com', 'aquiles1234')
        
        # Crear Usuario Alumno (Leo_Russo)
        if not User.objects.filter(username='Leo_Russo').exists():
            User.objects.create_user('Leo_Russo', 'leo@example.com', 'aquiles1234')
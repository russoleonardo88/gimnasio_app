from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
# Importamos settings y la función static
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('', include('alumnos.urls')),
]

# Esta es la conexión clave para que funcionen las imágenes y el CSS
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
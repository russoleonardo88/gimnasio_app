from django.contrib import admin
from django.urls import path
from alumnos.views import login_view, mi_rutina
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('mi-rutina/', mi_rutina, name='mi_rutina'),
    # Esto es por si quieres añadir un logout en el futuro
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
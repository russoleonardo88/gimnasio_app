from django.urls import path
from . import views

urlpatterns = [
    path("mi-rutina/", views.mi_rutina),
]
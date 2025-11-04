from django.contrib import admin
from django.urls import path, include
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  # Página principal
    path('login/', views.login_view, name='login'),  # Página de login
    path('logout/', views.logout_view, name='logout'), # Página para cerrar sesión

    path('listar/', views.servicios_panel, name='listar'), # Panel o dashboard
    path('listar/<int:id>/', views.servicios_panel, name='listar_edit'),  # <- NUEVA
    #path('marcar-listo/<int:pk>/', views.marcar_listo, name='marcar_listo'),

    path('eliminar/<int:id>/', views.eliminar_servicio, name='eliminar'),
]
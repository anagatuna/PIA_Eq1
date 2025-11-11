from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  # Página principal
    path('login/', views.login_view, name='login'),  # Página de login
    path('logout/', views.logout_view, name='logout'), # Página para cerrar sesión
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("img/logo.png")),
    ),

    path('servicios/', views.servicios_panel, name='servicios'), # Panel o dashboard
    path('servicios/<int:id>/', views.servicios_panel, name='servicios_edit'),  # <- NUEVA
    path('eliminar/<int:id>/', views.eliminar_servicio, name='eliminar'),
    #path('marcar-listo/<int:pk>/', views.marcar_listo, name='marcar_listo'),

    path('citas/', views.citas_panel, name='citas'),
    path('citas/<int:id>/', views.citas_panel, name='citas_edit'),
    path('citas/<int:id>/eliminar/', views.eliminar_cita, name='citas_eliminar'),
]
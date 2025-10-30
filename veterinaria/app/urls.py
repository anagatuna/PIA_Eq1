from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_productos, name='listar'),
    path('crear/', views.crear_producto, name='crear'),
    path('editar/<int:id>/', views.editar_producto, name='editar'),
    path('eliminar/<int:id>/', views.eliminar_producto, name='eliminar'),

]
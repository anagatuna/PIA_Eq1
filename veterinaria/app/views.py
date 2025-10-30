from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404

from .models import SERVICIO

# Create your views here.
def listar_productos(request):
    productos = SERVICIO.objects.all()
    return render(request, 'listar.html', {'productos': productos})

def crear_producto(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        precio = request.POST['precio']
        descripcion = request.POST['descripcion']
        SERVICIO.objects.create(nombre=nombre, precio=precio, descripcion=descripcion)
        return redirect('listar')
    return render(request, 'crear.html')

def editar_producto(request, id):
    producto = get_object_or_404(SERVICIO, id=id)
    if request.method == 'POST':
        producto.nombre = request.POST['nombre']
        producto.precio = request.POST['precio']
        producto.descripcion = request.POST['descripcion']
        producto.save()
        return redirect('listar')

    return render(request, 'editar.html', {'producto': producto})

def eliminar_producto(request, id):
    producto = get_object_or_404(SERVICIO, id=id)
    producto.delete()

    return redirect('listar')
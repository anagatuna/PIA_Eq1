from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404

from .models import SERVICIO

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.username}')
            return redirect('/listar')  # 👈 tu panel principal
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('index')  # 👈 o la página principal pública

def index(request):
    return render(request, 'index.html')

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
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404

from .models import SERVICIO

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.username}')
            return redirect('/servicios')  # panel principal
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('index')  # página principal pública

def index(request):
    return render(request, 'index.html')

@login_required
def servicios_panel(request, id=None):
    servicio = get_object_or_404(SERVICIO, id=id) if id else None

    # Crear o actualizar según si viene id en la URL
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        precio = request.POST.get("precio", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()

        if servicio:  # editar
            servicio.nombre = nombre
            servicio.precio = precio or 0
            servicio.descripcion = descripcion
            servicio.save()
        else:        
            SERVICIO.objects.create(
                nombre=nombre,
                precio=precio or 0,
                descripcion=descripcion
            )
        return redirect("servicios")

    servicios = SERVICIO.objects.all().order_by("nombre")
    ctx = {"servicios": servicios, "servicio": servicio, "editando": bool(servicio)}

    return render(request, "servicios.html", ctx)

def eliminar_servicio(request, id):
    servicio = get_object_or_404(SERVICIO, id=id)
    servicio.delete()

    return redirect('servicios')

def listar_servicios(request):
    servicios = SERVICIO.objects.all()
    return render(request, 'servicios.html', {'servicios': servicios})


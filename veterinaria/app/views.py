from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime

from .models import SERVICIO, CITA_VETERINARIA

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
        nombre = request.POST.get("nombre", "").strip().capitalize()
        precio = request.POST.get("precio", "").strip()
        descripcion = request.POST.get("descripcion", "").strip().capitalize()

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

@login_required
def eliminar_servicio(request, id):
    servicio = get_object_or_404(SERVICIO, id=id)
    servicio.delete()
    messages.error(request, "Se eliminó correctamente el servicio.")

    return redirect('servicios')

@login_required
def listar_servicios(request):
    servicios = SERVICIO.objects.all()
    return render(request, 'servicios.html', {'servicios': servicios})

@login_required
def citas_panel(request, id=None):
    cita = get_object_or_404(CITA_VETERINARIA, pk=id) if id else None
    servicios = SERVICIO.objects.all() # Necesario para traer los servicios al ddl

    if request.method == "POST":
        nombre_dueño   = (request.POST.get("nombre_dueño") or "").strip().title()
        nombre_mascota = (request.POST.get("nombre_mascota") or "").strip().title()
        fecha_cita_raw = (request.POST.get("fecha_cita") or "").strip()
        motivo         = (request.POST.get("motivo") or "").strip().capitalize()
        estatus        = (request.POST.get("estatus") or "Pendiente").strip().capitalize()
        servicio_id    = (request.POST.get("servicio") or "").strip()

        # Sacar la especie del ddl y validar si selecciona o no 'otro'
        especie_select = (request.POST.get("especie_select") or "").strip()
        especie_otro   = (request.POST.get("especie_otro") or "").strip()
        if not especie_select:
            messages.error(request, "Selecciona una especie.")
            return render(request, "citas.html", {
                "citas": CITA_VETERINARIA.objects.all(),
                "cita": cita,
                "editando": bool(cita),
                "servicios": servicios,
            })
        elif especie_select == "Otro":
            if not especie_otro:
                messages.error(request, "Indica la especie en el campo 'Especifique la especie'.")
                return render(request, "citas.html", {
                    "citas": CITA_VETERINARIA.objects.all(),
                    "cita": cita,
                    "editando": bool(cita),
                    "servicios": servicios,
                })
            especie_final = especie_otro.capitalize()
        else:
            especie_final = especie_select.capitalize()

        # Validaciones básicas 
        if not servicio_id: # re-render con error y el ddl poblado 
            ctx = { 
                "citas": CITA_VETERINARIA.objects.all(), 
                "cita": cita, 
                "editando": bool(cita), 
                "servicios": servicios, 
                "error": "Selecciona un servicio.", 
            } 
            return render(request, "citas.html", ctx) 
        
        ser_obj = get_object_or_404(SERVICIO, pk=servicio_id) 

        # Parseo del datetime-local (YYYY-MM-DDTHH:MM), si usas zona horaria, conviértelo a aware 
        fecha_cita_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M") 
        if timezone.is_naive(fecha_cita_dt): 
            fecha_cita_dt = timezone.make_aware(fecha_cita_dt, 
            timezone.get_current_timezone())

        # Evitar dos citas del MISMO servicio a la MISMA fecha/hora
        validacionCita = CITA_VETERINARIA.objects.filter(
            servicio=ser_obj,
            fecha_cita=fecha_cita_dt
        )
        if cita:  # si estás editando, excluye la misma cita
            validacionCita = validacionCita.exclude(pk=cita.pk)

        if validacionCita.exists():
            messages.error(request, "Ese servicio ya tiene una cita en esa fecha y hora.")
            return render(request, "citas.html", {
                "citas": CITA_VETERINARIA.objects.all(),
                "cita": cita,
                "editando": bool(cita),
                "servicios": servicios,
            })
        
        # Editar 
        if cita:
            cita.nombre_dueño   = nombre_dueño
            cita.nombre_mascota = nombre_mascota
            cita.especie        = especie_final
            cita.fecha_cita     = fecha_cita_dt
            cita.motivo         = motivo
            cita.estatus        = estatus
            cita.servicio       = ser_obj
            cita.save()
            messages.success(request, "La cita se actualizó correctamente.")
        else: # Crear
            CITA_VETERINARIA.objects.create(
                nombre_dueño=nombre_dueño,
                nombre_mascota=nombre_mascota,
                especie=especie_final,
                fecha_cita=fecha_cita_dt,
                motivo=motivo,
                estatus="Pendiente",
                servicio=ser_obj,
            )
            messages.success(request, "La cita se registró correctamente.")

        return redirect("citas")

    citas = CITA_VETERINARIA.objects.all()
    ctx = {
        "citas": citas,
        "cita": cita,
        "editando": bool(cita),
        "servicios": servicios,
    }
    return render(request, "citas.html", ctx)

@login_required
def eliminar_cita(request, id):
    cita = get_object_or_404(CITA_VETERINARIA, id=id)
    cita.delete()
    messages.error(request, "Se eliminó correctamente la cita.")
    return redirect('citas')

def index(request):
    servicios = SERVICIO.objects.all().order_by('nombre')
    return render(request, 'index.html', {'servicios': servicios})
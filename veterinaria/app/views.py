from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
import unicodedata

from .models import SERVICIO, CITA_VETERINARIA

# Grupos para los roles
def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Administrador').exists()

def is_employee_or_admin(user):
    return user.is_superuser or user.groups.filter(name__in=['Administrador', 'Empleado']).exists()

# Helpers de tiempo para el select de las horas cada media.
def build_half_hour_slots(start="08:00", end="18:00"):
    t0 = datetime.strptime(start, "%H:%M")
    t1 = datetime.strptime(end, "%H:%M")
    out = []
    t = t0
    while t <= t1:
        out.append(t.strftime("%H:%M"))
        t += timedelta(minutes=30)
    return out

def floor_to_half_hour(dt):
    minute = 0 if dt.minute < 30 else 30
    return dt.replace(minute=minute, second=0, microsecond=0)

def ceil_to_half_hour(dt):
    m = dt.minute
    if m in (0, 30):
        return dt.replace(second=0, microsecond=0)
    if m < 30:
        return dt.replace(minute=30, second=0, microsecond=0)
    return (dt + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

# Helper para filtrar
def strip_accents(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text

# Log in 
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
    servicios = SERVICIO.objects.all().order_by('nombre')
    return render(request, 'index.html', {'servicios': servicios})

# Servicios
@login_required
@user_passes_test(is_employee_or_admin)
def servicios_panel(request, id=None):
    es_admin = is_admin(request.user)
    servicio = get_object_or_404(SERVICIO, id=id) if id else None

    if request.method == "POST" and not es_admin:
        messages.error(request, "No tienes permisos para modificar servicios.")
        return redirect("servicios")
        
    nombre = request.POST.get("nombre", "").strip().capitalize()
    precio = request.POST.get("precio", "").strip()
    descripcion = request.POST.get("descripcion", "").strip().capitalize()
    # No aceptar duplicados nombre o descripcion
    duplicate_query = Q(nombre=nombre) | Q(descripcion=descripcion)
    if servicio:  # editar
        # Buscamos si existe otro servicio (excluyendo el actual) que coincida
        if SERVICIO.objects.filter(duplicate_query).exclude(id=servicio.id).exists():
            messages.error(request, "Ya existe OTRO servicio con ese nombre o descripción.")
        else:
            servicio.nombre = nombre
            servicio.precio = precio or 0
            servicio.descripcion = descripcion
            servicio.save()
            messages.success(request, "Servicio actualizado correctamente.")
            return redirect("servicios") # <-- Se mueve aquí
    else:
        # Buscamos si existe otro servicio (excluyendo el actual) que coincida
        if SERVICIO.objects.filter(duplicate_query).exists():
            messages.error(request, "Ya existe un servicio con ese nombre o descripción.")
        else:
            SERVICIO.objects.create(
                nombre=nombre,
                precio=precio or 0,
                descripcion=descripcion
            )
            messages.success(request, "Servicio creado correctamente.")
            return redirect("servicios") # <-- Se mueve aquí

    # 1. Obtener el término de búsqueda (q) de la URL
    q = request.GET.get('q', '').strip()
    qs = SERVICIO.objects.all().order_by("nombre")

    if q:
        # Normalizar el término de búsqueda (minúsculas y sin acentos)
        q_normal = strip_accents(q.lower())
        
        servicios_filtrados = []
        for s in qs:
            # Normalizar los campos del modelo para comparar
            nombre_normal = strip_accents(s.nombre.lower())
            desc_normal = strip_accents(s.descripcion.lower())
            
            # Comprobar si el término de búsqueda está en los campos normalizados
            if q_normal in nombre_normal or q_normal in desc_normal:
                servicios_filtrados.append(s)
        
        servicios = servicios_filtrados 
    else:
        servicios = qs 
        
    ctx = {
        "servicios": servicios, 
        "servicio": servicio, 
        "editando": bool(servicio),
        "form_data": request.POST if request.method == "POST" else {}, # Para que no se borre el formulario en caso de error
        "q": q,
        "es_admin": es_admin,
    }
    return render(request, "servicios.html", ctx)

@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_employee_or_admin)
def citas_panel(request, id=None):
    es_admin = is_admin(request.user)

    cita = get_object_or_404(CITA_VETERINARIA, pk=id) if id else None
    servicios = SERVICIO.objects.all()
    ahora_local = timezone.localtime()

    # Slots de 30 min de 8 am a 6 pm
    slots = build_half_hour_slots("08:00", "18:00")

    # Valores por defecto para date+select
    if cita:
        sel_hora = timezone.localtime(cita.fecha_cita).strftime("%H:%M")
        sel_fecha = timezone.localtime(cita.fecha_cita).strftime("%Y-%m-%d")
    else:
        next_slot = ceil_to_half_hour(ahora_local)
        sel_hora = next_slot.strftime("%H:%M")
        sel_fecha = next_slot.strftime("%Y-%m-%d")

    # --- Flags de estado de la cita ---
    cita_pasada_bool = bool(cita and timezone.localtime(cita.fecha_cita) <= ahora_local)
    # Completada o Cancelada = bloqueada total para TODOS
    bloqueada_total = bool(cita and cita.estatus in ["Completada", "Cancelada"])
    # Solo estatus por fecha (ya pasó) para admin
    solo_estatus_fecha = bool(cita and cita_pasada_bool and not bloqueada_total)
    # Solo estatus por rol (empleado nunca edita campos, solo estatus)
    solo_estatus_rol = bool(cita and (not es_admin) and not bloqueada_total)
    # Flag global para template
    solo_estatus = solo_estatus_fecha or solo_estatus_rol

    # Crear y editar
    if request.method == "POST":
        estatus_post = (request.POST.get("estatus") or "").strip().capitalize()

        # Si está Completada o Cancelada nadie puede editar nada
        if cita and bloqueada_total:
            messages.error(request, "Esta cita ya está cerrada (Completada o Cancelada) y no puede editarse.")
            return redirect("citas")

        # Empleado solo cambia estatus
        if not es_admin:
            if not cita:
                messages.error(request, "No tienes permisos para crear citas.")
                return redirect("citas")

            cita_pasada = cita_pasada_bool

            if cita_pasada:
                permitidos = ["Completada", "No asistió"]
                msg_regla = "La cita ya pasó: solo puedes marcar Completada o No asistió."
            else:
                permitidos = ["Pendiente", "Cancelada"]
                msg_regla = "La cita aún no ocurre: solo puedes alternar entre Pendiente y Cancelada."

            if estatus_post not in permitidos:
                messages.error(request, msg_regla)
                return redirect("citas")

            cita.estatus = estatus_post
            cita.save()
            messages.success(request, "Estatus actualizado.")
            return redirect("citas")

        # Solo admin todo lo que sigue
        # Recuperar la fecha/hora enviada
        fecha_cita_raw = ""
        vals_fc = request.POST.getlist("fecha_cita")
        if vals_fc:
            for v in reversed(vals_fc):
                if "T" in v:
                    fecha_cita_raw = v.strip()
                    break
            if not fecha_cita_raw:
                fecha_cita_raw = f"{vals_fc[-1].strip()}T{(request.POST.get('hora_cita') or '00:00').strip()}"
        else:
            dia = (request.POST.get("fecha_dia") or request.POST.get("fecha_cita") or "").strip()
            hora = (request.POST.get("hora_cita") or "").strip()
            if dia and hora:
                fecha_cita_raw = f"{dia}T{hora}"

        # ADMIN con cita pasada solo modifica el estatus
        if cita and cita_pasada_bool:
            permitidos = ["Completada", "No asistió"]
            if estatus_post not in permitidos:
                messages.error(request, "La cita ya pasó: solo puedes elegir 'Completada' o 'No asistió'.")
                return redirect("citas")
            cita.estatus = estatus_post
            cita.save()
            messages.success(request, "Estatus actualizado.")
            return redirect("citas")

        nombre_dueño   = (request.POST.get("nombre_dueño") or "").strip().title()
        nombre_mascota = (request.POST.get("nombre_mascota") or "").strip().title()
        motivo         = (request.POST.get("motivo") or "").strip().capitalize()
        servicio_id    = (request.POST.get("servicio") or "").strip()

        # especie
        especie_select = (request.POST.get("especie_select") or "").strip()
        especie_otro   = (request.POST.get("especie_otro") or "").strip()
        if not especie_select:
            messages.error(request, "Selecciona una especie.")
            if fecha_cita_raw:
                try_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M")
                sel_fecha = try_dt.strftime("%Y-%m-%d")
                sel_hora  = try_dt.strftime("%H:%M")
            return render(request, "citas.html", {
                "citas": CITA_VETERINARIA.objects.all(),
                "cita": cita,
                "editando": bool(cita),
                "servicios": servicios,
                "slots": slots, "sel_hora": sel_hora, "sel_fecha": sel_fecha,
                "min_fecha": ahora_local.strftime("%Y-%m-%d"),
                "cita_pasada": cita_pasada_bool,
                "bloqueada_total": bloqueada_total,
                "solo_estatus": solo_estatus,
                "es_admin": es_admin,
                "form_data": request.POST,  
            })
        elif especie_select == "Otro":
            if not especie_otro:
                messages.error(request, "Indica la especie en el campo 'Especifique la especie'.")
                if fecha_cita_raw:
                    try_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M")
                    sel_fecha = try_dt.strftime("%Y-%m-%d")
                    sel_hora  = try_dt.strftime("%H:%M")
                return render(request, "citas.html", {
                    "citas": CITA_VETERINARIA.objects.all(),
                    "cita": cita,
                    "editando": bool(cita),
                    "servicios": servicios,
                    "slots": slots, "sel_hora": sel_hora, "sel_fecha": sel_fecha,
                    "min_fecha": ahora_local.strftime("%Y-%m-%d"),
                    "cita_pasada": cita_pasada_bool,
                    "bloqueada_total": bloqueada_total,
                    "solo_estatus": solo_estatus,
                    "es_admin": es_admin,
                    "form_data": request.POST,  
                })
            especie_final = especie_otro.capitalize()
        else:
            especie_final = especie_select.capitalize()

        if not servicio_id:
            messages.error(request, "Selecciona un servicio.")
            if fecha_cita_raw:
                try_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M")
                sel_fecha = try_dt.strftime("%Y-%m-%d")
                sel_hora  = try_dt.strftime("%H:%M")
            return render(request, "citas.html", {
                "citas": CITA_VETERINARIA.objects.all(),
                "cita": cita,
                "editando": bool(cita),
                "servicios": servicios,
                "slots": slots, "sel_hora": sel_hora, "sel_fecha": sel_fecha,
                "min_fecha": ahora_local.strftime("%Y-%m-%d"),
                "cita_pasada": cita_pasada_bool,
                "bloqueada_total": bloqueada_total,
                "solo_estatus": solo_estatus,
                "es_admin": es_admin,
                "form_data": request.POST,  
            })

        ser_obj = get_object_or_404(SERVICIO, pk=servicio_id)

        # Parseo fecha
        try:
            fecha_cita_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M")
        except Exception:
            messages.error(request, "Formato de fecha inválido.")
            return redirect("citas")

        if timezone.is_naive(fecha_cita_dt):
            fecha_cita_dt = timezone.make_aware(fecha_cita_dt, timezone.get_current_timezone())

        # Crear: no permitir pasada o igual al "ahora"
        if not cita and fecha_cita_dt <= ahora_local:
            messages.error(request, "La fecha y hora de la cita debe ser en el futuro.")
            if fecha_cita_raw:
                try_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M")
                sel_fecha = try_dt.strftime("%Y-%m-%d")
                sel_hora  = try_dt.strftime("%H:%M")
            return render(request, "citas.html", {
                "citas": CITA_VETERINARIA.objects.all(),
                "cita": cita,
                "editando": bool(cita),
                "servicios": servicios,
                "slots": slots, "sel_hora": sel_hora, "sel_fecha": sel_fecha,
                "min_fecha": ahora_local.strftime("%Y-%m-%d"),
                "cita_pasada": cita_pasada_bool,
                "bloqueada_total": bloqueada_total,
                "solo_estatus": solo_estatus,
                "es_admin": es_admin,
            })

        # Validación de estatus coherente a la fecha para admin
        if fecha_cita_dt <= ahora_local:
            permitidos = ["Completada", "No asistió"]
            msg_regla = "Solo puedes elegir 'Completada' o 'No asistió' (la cita ya pasó)."
        else:
            permitidos = ["Pendiente", "Cancelada"]
            msg_regla = "Solo puedes elegir 'Pendiente' o 'Cancelada' (la cita aún no ocurre)."

        # Al crear, forzar 'Pendiente'
        estatus_final = "Pendiente" if not cita else estatus_post
        if cita and estatus_final not in permitidos:
            messages.error(request, msg_regla)
            if fecha_cita_raw:
                try_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M")
                sel_fecha = try_dt.strftime("%Y-%m-%d")
                sel_hora  = try_dt.strftime("%H:%M")
            return render(request, "citas.html", {
                "citas": CITA_VETERINARIA.objects.all(),
                "cita": cita,
                "editando": True,
                "servicios": servicios,
                "slots": slots, "sel_hora": sel_hora, "sel_fecha": sel_fecha,
                "min_fecha": ahora_local.strftime("%Y-%m-%d"),
                "cita_pasada": cita_pasada_bool,
                "bloqueada_total": bloqueada_total,
                "solo_estatus": solo_estatus,
                "es_admin": es_admin,
            })

        # Bloqueo por media hora (slot)
        slot_inicio = floor_to_half_hour(fecha_cita_dt)
        slot_fin = slot_inicio + timedelta(minutes=30)
        choque = CITA_VETERINARIA.objects.filter(
            servicio=ser_obj,
            fecha_cita__gte=slot_inicio,
            fecha_cita__lt=slot_fin,
        )
        if cita:
            choque = choque.exclude(pk=cita.pk)
        if choque.exists():
            messages.error(request, "Ya existe una cita para ese servicio en ese bloque de 30 minutos.")
            if fecha_cita_raw:
                try_dt = datetime.strptime(fecha_cita_raw, "%Y-%m-%dT%H:%M")
                sel_fecha = try_dt.strftime("%Y-%m-%d")
                sel_hora  = try_dt.strftime("%H:%M")
            return render(request, "citas.html", {
                "citas": CITA_VETERINARIA.objects.all(),
                "cita": cita,
                "editando": bool(cita),
                "servicios": servicios,
                "slots": slots, "sel_hora": sel_hora, "sel_fecha": sel_fecha,
                "min_fecha": ahora_local.strftime("%Y-%m-%d"),
                "cita_pasada": cita_pasada_bool,
                "bloqueada_total": bloqueada_total,
                "solo_estatus": solo_estatus,
                "es_admin": es_admin,
            })

        # Guardar admin
        if cita:
            cita.nombre_dueño   = nombre_dueño
            cita.nombre_mascota = nombre_mascota
            cita.especie        = especie_final
            cita.fecha_cita     = fecha_cita_dt
            cita.motivo         = motivo
            cita.estatus        = estatus_final
            cita.servicio       = ser_obj
            cita.save()
            messages.success(request, "La cita se actualizó correctamente.")
        else:
            CITA_VETERINARIA.objects.create(
                nombre_dueño=nombre_dueño,
                nombre_mascota=nombre_mascota,
                especie=especie_final,
                fecha_cita=fecha_cita_dt,
                motivo=motivo,
                estatus="Pendiente",   # siempre por defecto
                servicio=ser_obj,
            )
            messages.success(request, "La cita se registró correctamente.")
        return redirect("citas")

    # Filtrar
    qs = CITA_VETERINARIA.objects.all().select_related('servicio').order_by('fecha_cita')

    estatus_f = (request.GET.get('estatus') or '').strip()
    servicio_f = (request.GET.get('servicio') or '').strip()
    desde_f = (request.GET.get('desde') or '').strip()
    hasta_f = (request.GET.get('hasta') or '').strip()
    q = (request.GET.get('q') or '').strip()

    if estatus_f:
        qs = qs.filter(estatus__iexact=estatus_f)
    if servicio_f:
        qs = qs.filter(servicio__pk=servicio_f)
    if desde_f:
        try:
            d = datetime.strptime(desde_f, "%Y-%m-%d")
            d = timezone.make_aware(datetime(d.year, d.month, d.day, 0, 0), timezone.get_current_timezone())
            qs = qs.filter(fecha_cita__gte=d)
        except Exception:
            pass
    if hasta_f:
        try:
            h = datetime.strptime(hasta_f, "%Y-%m-%d")
            h = timezone.make_aware(datetime(h.year, h.month, h.day, 23, 59, 59), timezone.get_current_timezone())
            qs = qs.filter(fecha_cita__lte=h)
        except Exception:
            pass
    if q:
        qs = qs.filter(
            Q(nombre_dueño__icontains=q) |
            Q(nombre_mascota__icontains=q) |
            Q(motivo__icontains=q)
        )

    ctx = {
        "citas": qs,
        "cita": cita,
        "editando": bool(cita),
        "servicios": servicios,
        "slots": slots,
        "sel_hora": sel_hora,
        "sel_fecha": sel_fecha,
        "min_fecha": ahora_local.strftime("%Y-%m-%d"),
        "ahora_str": ahora_local.strftime("%Y-%m-%dT%H:%M"),
        "cita_pasada": cita_pasada_bool,
        "bloqueada_total": bloqueada_total,
        "solo_estatus": solo_estatus,
        "q": q,
        "es_admin": es_admin,
        "form_data": request.POST if request.method == "POST" else {},   
    }
    return render(request, "citas.html", ctx)

# Eliminar citas
@login_required
@user_passes_test(is_admin)
def eliminar_cita(request, id):
    cita = get_object_or_404(CITA_VETERINARIA, id=id)

    if cita.estatus in ["Completada", "Cancelada"]:
        messages.error(request, "No puedes eliminar una cita Completada o Cancelada.")
        return redirect('citas')

    cita.delete()
    messages.error(request, "Se eliminó correctamente la cita.")
    return redirect('citas')

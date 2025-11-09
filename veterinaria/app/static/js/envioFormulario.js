
document.addEventListener("DOMContentLoaded", function() {

    const miFormulario = document.getElementById('formulario_datos');

    if (miFormulario) {
        miFormulario.addEventListener('submit', function(evento) {
            
            evento.preventDefault(); 
            
            const fecha = document.getElementById('campoFecha').value;
            const hoy = new Date().toISOString().split('T')[0];
            
            if (fecha < hoy) {
                alert("La fecha no puede ser anterior al día de hoy.");
                return;
            }

            alert("Datos recibidos con éxito.");
            miFormulario.reset();
        });
    }
});
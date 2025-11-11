
document.addEventListener("DOMContentLoaded", function() {

    const miFormulario = document.getElementById('formulario_datos');

    if (miFormulario) {
        miFormulario.addEventListener('submit', function(evento) {
            
            evento.preventDefault(); 
            
            alert("Datos recibidos con éxito.");
            miFormulario.reset();
        });
    }
});
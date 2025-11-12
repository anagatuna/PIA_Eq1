document.addEventListener("DOMContentLoaded", function() {

    const zoomInButton = document.getElementById('btn-zoom-in');
    const zoomOutButton = document.getElementById('btn-zoom-out');
    const zoomResetButton = document.getElementById('btn-zoom-reset');

    let currentZoomLevel = 1.0;
    const ZOOM_STEP = 0.1;
    const MAX_ZOOM = 2.0;
    const MIN_ZOOM = 1;

    function applyZoom() {
        document.body.style.zoom = currentZoomLevel;
    }

    if (zoomInButton) {
        zoomInButton.addEventListener('click', function() {
            if (currentZoomLevel < MAX_ZOOM) {
                currentZoomLevel += ZOOM_STEP;
                applyZoom();
            }
        });
    }

    if (zoomOutButton) {
        zoomOutButton.addEventListener('click', function() {
            if (currentZoomLevel > MIN_ZOOM) {
                currentZoomLevel -= ZOOM_STEP;
                applyZoom();
            }
        });
    }

    if (zoomResetButton) {
        zoomResetButton.addEventListener('click', function() {
            currentZoomLevel = 1.0;
            applyZoom();
        });
    }
});
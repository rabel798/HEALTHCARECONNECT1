document.addEventListener('DOMContentLoaded', function() {
    // Initialize map if the map element exists
    const mapElement = document.getElementById('map');
    if (mapElement) {
        initMap();
    }
});

function initMap() {
    // Clinic location coordinates for Budigere Road, Bengaluru
    const clinicLocation = [13.090580, 77.741161]; // Budigere Road, Bengaluru coordinates

    // Initialize map
    const map = L.map('map').setView(clinicLocation, 15);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Add marker for clinic location
    const clinicMarker = L.marker(clinicLocation).addTo(map);

    // Add popup to marker
    clinicMarker.bindPopup("<strong>Dr. Richa's Eye Clinic</strong><br>Your Vision, Our Priority").openPopup();

    // Add circle around the marker
    L.circle(clinicLocation, {
        color: '#007bff',
        fillColor: '#007bff',
        fillOpacity: 0.1,
        radius: 500
    }).addTo(map);
}

// Function to open Google Maps with directions from user's location to clinic
function getDirectionsToClinic() {
    // Direct Google Maps business page URL for Dr. Richa's Eye Clinic
    const clinicBusinessUrl = "https://maps.app.goo.gl/L9w8fpfiAgQ1RgTb8";

    // Always open the business page directly - this will show the clinic info
    // and Google Maps will automatically detect user's location for directions
    window.open(clinicBusinessUrl, '_blank');
}
document.addEventListener('DOMContentLoaded', function() {
    // Initialize map if the map element exists
    const mapElement = document.getElementById('map');
    if (mapElement) {
        initMap();
    }
});

function initMap() {
    // Clinic location coordinates for Budigere Road, Bengaluru
    const clinicLocation = [13.090032977903189, 77.74095051096549]; // Updated clinic coordinates

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
    // Clinic location coordinates
    const clinicLat = 13.090032977903189;
    const clinicLng = 77.74095051096549;

    // Try to get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const userLat = position.coords.latitude;
                const userLng = position.coords.longitude;

                // Open Google Maps with directions from user's location to clinic
                const directionsUrl = `https://www.google.com/maps/dir/${userLat},${userLng}/${clinicLat},${clinicLng}`;
                window.open(directionsUrl, '_blank');
            },
            // Error callback
            function() {
                // If cannot get user's location, just show directions to clinic
                const directionsUrl = `https://www.google.com/maps/dir//${clinicLat},${clinicLng}`;
                window.open(directionsUrl, '_blank');
            }
        );
    } else {
        // Geolocation not supported
        const directionsUrl = `https://www.google.com/maps/dir//${clinicLat},${clinicLng}`;
        window.open(directionsUrl, '_blank');
    }
}
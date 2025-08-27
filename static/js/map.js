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
    const clinicBusinessUrl = "https://www.google.com/maps/place/Dr+Richa's+Eye+Clinic/@13.0900245,77.7383327,858m/data=!3m2!1e3!4b1!4m6!3m5!1s0x3bae1b3fad8a8c9d:0x2ec2fa858ce9281d!8m2!3d13.0900245!4d77.7409076!16s%2Fg%2F11xv9vjd70?entry=ttu&g_ep=EgoyMDI1MDgyNC4wIKXMDSoASAFQAw%3D%3D";

    // Try to get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const userLat = position.coords.latitude;
                const userLng = position.coords.longitude;

                // Open Google Maps with directions from user's location to the clinic business page
                const directionsUrl = `https://www.google.com/maps/dir/${userLat},${userLng}/Dr+Richa's+Eye+Clinic/@13.0900245,77.7409076`;
                window.open(directionsUrl, '_blank');
            },
            // Error callback
            function() {
                // If cannot get user's location, just show the clinic business page
                window.open(clinicBusinessUrl, '_blank');
            }
        );
    } else {
        // Geolocation not supported - show clinic business page
        window.open(clinicBusinessUrl, '_blank');
    }
}
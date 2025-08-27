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
    // Use the business name and address for better Google Maps integration
    const clinicAddress = "Dr. Richa's Eye Clinic, First floor, DVR Town Centre, near IGUS private limited, Mandur, Budigere Road, Bengaluru, Karnataka 560049";
    const encodedAddress = encodeURIComponent(clinicAddress);
    
    // Try to get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const userLat = position.coords.latitude;
                const userLng = position.coords.longitude;
                
                // Open Google Maps with directions using business name and address
                const mapsUrl = `https://www.google.com/maps/dir/${userLat},${userLng}/${encodedAddress}`;
                window.open(mapsUrl, '_blank');
            },
            // Error callback
            function() {
                // If cannot get user's location, just show the clinic location with business info
                const mapsUrl = `https://www.google.com/maps/search/${encodedAddress}`;
                window.open(mapsUrl, '_blank');
            }
        );
    } else {
        // Geolocation not supported - show clinic location with business info
        const mapsUrl = `https://www.google.com/maps/search/${encodedAddress}`;
        window.open(mapsUrl, '_blank');
    }
}
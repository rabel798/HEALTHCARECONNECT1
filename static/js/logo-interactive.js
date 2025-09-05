
document.addEventListener('DOMContentLoaded', function() {
    // Check if we have an SVG logo with the right ID
    const logoContainer = document.getElementById('interactive-logo-container');
    if (!logoContainer) return;
    
    // Load the SVG file
    fetch('/static/assets/logo-interactive.svg')
        .then(response => response.text())
        .then(svgData => {
            // Insert the SVG content
            logoContainer.innerHTML = svgData;
            
            // Get the SVG document
            const svgElement = logoContainer.querySelector('svg');
            
            // Get reference to all required SVG elements
            const eyeContainer = svgElement.getElementById('eye-container');
            const pupil = svgElement.getElementById('pupil');
            const reflectionDot = svgElement.getElementById('reflectionDot');
            const topEyelid = svgElement.getElementById('topEyelid');
            const bottomEyelid = svgElement.getElementById('bottomEyelid');
            const splash = svgElement.getElementById('splash');
            const letterR = svgElement.getElementById('letter-r');
            
            if (!eyeContainer || !pupil || !reflectionDot || !topEyelid || !bottomEyelid) {
                console.error('SVG elements not found');
                return;
            }
            
            // Function to make the eye blink
            function blinkEye() {
                // Show eyelids
                topEyelid.style.display = 'block';
                bottomEyelid.style.display = 'block';
                
                // Hide pupil and reflection during blink
                pupil.style.display = 'none';
                reflectionDot.style.display = 'none';
                
                // Open eye after short delay
                setTimeout(() => {
                    topEyelid.style.display = 'none';
                    bottomEyelid.style.display = 'none';
                    pupil.style.display = 'block';
                    reflectionDot.style.display = 'block';
                }, 150);
            }
            
            // Function to animate splash
            function animateSplash() {
                if (splash) {
                    splash.style.transform = 'translate(30, 8) scale(1.2) rotate(10deg)';
                    splash.style.transition = 'transform 0.3s ease';
                    
                    setTimeout(() => {
                        splash.style.transform = 'translate(30, 8) scale(1) rotate(0deg)';
                    }, 300);
                }
            }
            
            // Handle mouse movement for pupil tracking
            document.addEventListener('mousemove', function(evt) {
                // Calculate mouse position relative to the SVG
                const rect = svgElement.getBoundingClientRect();
                const mouseX = evt.clientX - rect.left;
                const mouseY = evt.clientY - rect.top;
                
                // Move pupil slightly to follow mouse (limit movement)
                const eyeCenterX = 25; // Eye center position in the R
                const eyeCenterY = 17.5;
                
                // Calculate direction vector from eye center to mouse
                let dx = mouseX - (eyeCenterX + 10); // Adjust for logo position
                let dy = mouseY - (eyeCenterY + 5);
                
                // Limit movement to 2 units in any direction
                const maxMove = 2;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist > maxMove) {
                    dx = dx * maxMove / dist;
                    dy = dy * maxMove / dist;
                }
                
                // Apply movement to pupil
                pupil.setAttribute('cx', eyeCenterX + dx);
                pupil.setAttribute('cy', eyeCenterY + dy);
                
                // Move reflection dot opposite to pupil movement
                reflectionDot.setAttribute('cx', 26 - dx/2);
                reflectionDot.setAttribute('cy', 16.5 - dy/2);
            });
            
            // Blink when mouse enters the logo
            svgElement.addEventListener('mouseenter', function() {
                blinkEye();
                animateSplash();
            });
            
            // Add hover effect to the R letter
            if (letterR) {
                letterR.addEventListener('mouseenter', function() {
                    letterR.style.filter = 'brightness(1.1) drop-shadow(0 2px 4px rgba(0,0,0,0.2))';
                    letterR.style.transition = 'filter 0.3s ease';
                });
                
                letterR.addEventListener('mouseleave', function() {
                    letterR.style.filter = 'none';
                });
            }
            
            // Continuous blinking every 4 seconds
            setInterval(blinkEye, 4000);
            
            // Animate splash every 6 seconds
            setInterval(animateSplash, 6000);
            
            // Add click handler
            svgElement.addEventListener('click', function() {
                // Trigger a blink and splash animation
                blinkEye();
                animateSplash();
                
                // If the logo should link to the homepage or admin login
                // We already have this handled in layout.html
            });
        })
        .catch(error => {
            console.error('Error loading interactive logo:', error);
        });
});

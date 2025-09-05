
document.addEventListener('DOMContentLoaded', function() {
    // Check if we have an SVG logo container
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
                
                // Hide eyelids after 150ms
                setTimeout(() => {
                    topEyelid.style.display = 'none';
                    bottomEyelid.style.display = 'none';
                }, 150);
            }
            
            // Function to animate the splash
            function animateSplash() {
                if (splash) {
                    splash.style.opacity = '1';
                    splash.style.transform = 'scale(1.2) rotate(10deg)';
                    splash.style.transition = 'all 0.4s ease-out';
                    
                    setTimeout(() => {
                        splash.style.opacity = '0';
                        splash.style.transform = 'scale(1) rotate(0deg)';
                    }, 600);
                }
            }
            
            // Mouse tracking for pupil movement
            svgElement.addEventListener('mousemove', function(e) {
                const rect = svgElement.getBoundingClientRect();
                const mouseX = (e.clientX - rect.left) * (120 / rect.width); // Scale to SVG coordinates
                const mouseY = (e.clientY - rect.top) * (60 / rect.height);
                
                // Eye center position (updated for new logo)
                const eyeCenterX = 38;
                const eyeCenterY = 22;
                
                // Calculate direction vector from eye center to mouse
                let dx = mouseX - eyeCenterX;
                let dy = mouseY - eyeCenterY;
                
                // Limit movement to 1.8 units in any direction
                const maxMove = 1.8;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist > maxMove) {
                    dx = dx * maxMove / dist;
                    dy = dy * maxMove / dist;
                }
                
                // Apply movement to pupil
                pupil.setAttribute('cx', eyeCenterX + dx);
                pupil.setAttribute('cy', eyeCenterY + dy);
                
                // Move reflection dot slightly opposite to pupil movement
                reflectionDot.setAttribute('cx', 39.5 - dx/3);
                reflectionDot.setAttribute('cy', 20.5 - dy/3);
            });
            
            // Blink when mouse enters the logo
            svgElement.addEventListener('mouseenter', function() {
                blinkEye();
                animateSplash();
            });
            
            // Add hover effect to the R letter
            if (letterR) {
                letterR.addEventListener('mouseenter', function() {
                    letterR.style.filter = 'brightness(1.15) drop-shadow(0 3px 6px rgba(0,0,0,0.3))';
                    letterR.style.transition = 'filter 0.3s ease';
                });
                
                letterR.addEventListener('mouseleave', function() {
                    letterR.style.filter = 'none';
                });
            }
            
            // Continuous blinking every 5 seconds
            setInterval(blinkEye, 5000);
            
            // Animate splash every 8 seconds
            setInterval(animateSplash, 8000);
            
            // Add click handler
            svgElement.addEventListener('click', function() {
                // Trigger a blink and splash animation
                blinkEye();
                animateSplash();
                
                // Add a small pulse effect
                svgElement.style.transform = 'scale(1.05)';
                svgElement.style.transition = 'transform 0.2s ease';
                
                setTimeout(() => {
                    svgElement.style.transform = 'scale(1)';
                }, 200);
            });
        })
        .catch(error => {
            console.error('Error loading interactive logo:', error);
        });
});

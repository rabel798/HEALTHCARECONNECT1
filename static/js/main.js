
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Enhanced scroll animations with performance optimizations
    function initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    // Stop observing once animation is triggered for performance
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe all animation elements
        const animationElements = document.querySelectorAll('.fade-in, .slide-up, .slide-up-delayed, .scale-in');
        animationElements.forEach(el => observer.observe(el));

        // Stagger animation for grouped elements
        const staggerElements = document.querySelectorAll('.slide-up-stagger');
        staggerElements.forEach((element, index) => {
            element.style.transitionDelay = `${index * 0.1}s`;
            observer.observe(element);
        });

        // Ensure doctor image container is observed for fade-in animation
        const doctorImageContainer = document.querySelector('.doctor-image');
        if (doctorImageContainer) {
            // Add fade-in class if it doesn't exist
            if (!doctorImageContainer.classList.contains('fade-in')) {
                doctorImageContainer.classList.add('fade-in');
                observer.observe(doctorImageContainer);
            }
        }
    }

    // Initialize scroll animations
    initScrollAnimations();

    // Payment method selection
    const paymentMethods = document.querySelectorAll('.payment-method-card');
    if (paymentMethods.length > 0) {
        paymentMethods.forEach(method => {
            method.addEventListener('click', function() {
                // Remove selected class from all methods
                paymentMethods.forEach(m => m.classList.remove('selected'));

                // Add selected class to clicked method
                this.classList.add('selected');

                // Set the value in the hidden input
                const methodValue = this.dataset.method;
                const paymentMethodInput = document.getElementById('payment_method');
                if (paymentMethodInput) {
                    paymentMethodInput.value = methodValue;
                }
            });
        });
    }

    // Appointment date picker functionality
    const appointmentDateInput = document.getElementById('appointment_date');
    const calendarTrigger = document.getElementById('calendar-trigger');
    
    if (appointmentDateInput && calendarTrigger) {
        calendarTrigger.addEventListener('click', function() {
            appointmentDateInput.focus();
            appointmentDateInput.click();
        });

        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        appointmentDateInput.setAttribute('min', today);

        // Handle date change for time slot loading
        appointmentDateInput.addEventListener('change', function() {
            loadTimeSlots(this.value);
        });
    }

    // Time slot selection
    function loadTimeSlots(selectedDate) {
        const timeSlotsContainer = document.getElementById('time-slots-container');
        if (!timeSlotsContainer) return;

        // Show loading
        timeSlotsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading available times...</div>';

        // Simulate API call (replace with actual endpoint)
        setTimeout(() => {
            const timeSlots = generateTimeSlots(selectedDate);
            renderTimeSlots(timeSlots);
        }, 500);
    }

    function generateTimeSlots(date) {
        const selectedDate = new Date(date);
        const dayOfWeek = selectedDate.getDay();
        
        // Sunday (0) has different hours: 10:00 AM - 1:00 PM
        // Monday-Saturday (1-6): 5:00 PM - 8:00 PM
        
        let slots = [];
        if (dayOfWeek === 0) {
            // Sunday slots
            slots = ['10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM'];
        } else {
            // Weekday slots
            slots = ['5:00 PM', '5:30 PM', '6:00 PM', '6:30 PM', '7:00 PM', '7:30 PM'];
        }

        // Mark some slots as unavailable (example logic)
        return slots.map(slot => ({
            time: slot,
            available: Math.random() > 0.3 // Random availability for demo
        }));
    }

    function renderTimeSlots(slots) {
        const timeSlotsContainer = document.getElementById('time-slots-container');
        if (!timeSlotsContainer) return;

        const slotsHtml = slots.map(slot => `
            <button type="button" class="time-slot ${!slot.available ? 'disabled' : ''}" 
                    data-time="${slot.time}" ${!slot.available ? 'disabled' : ''}>
                ${slot.time}
            </button>
        `).join('');

        timeSlotsContainer.innerHTML = `
            <div class="time-slots">
                ${slotsHtml}
            </div>
        `;

        // Add click handlers to time slots
        document.querySelectorAll('.time-slot:not(.disabled)').forEach(slot => {
            slot.addEventListener('click', function() {
                // Remove selected class from all slots
                document.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
                
                // Add selected class to clicked slot
                this.classList.add('selected');
                
                // Set the value in the hidden input
                const timeInput = document.getElementById('appointment_time');
                if (timeInput) {
                    timeInput.value = this.dataset.time;
                }
            });
        });
    }

    // Star rating functionality
    const starButtons = document.querySelectorAll('.star-btn');
    const ratingInput = document.getElementById('rating');
    
    if (starButtons.length > 0 && ratingInput) {
        starButtons.forEach((star, index) => {
            star.addEventListener('click', function() {
                const rating = index + 1;
                ratingInput.value = rating;
                
                // Update star display
                starButtons.forEach((s, i) => {
                    const starIcon = s.querySelector('i');
                    if (i < rating) {
                        starIcon.className = 'fas fa-star text-warning';
                    } else {
                        starIcon.className = 'far fa-star text-muted';
                    }
                });
                
                // Remove any existing validation error
                const errorElement = document.getElementById('rating-error');
                if (errorElement) {
                    errorElement.style.display = 'none';
                }
            });
            
            // Hover effect
            star.addEventListener('mouseenter', function() {
                const hoverRating = index + 1;
                starButtons.forEach((s, i) => {
                    const starIcon = s.querySelector('i');
                    if (i < hoverRating) {
                        starIcon.className = 'fas fa-star text-warning';
                    } else {
                        starIcon.className = 'far fa-star text-muted';
                    }
                });
            });
        });
        
        // Reset to actual rating on mouse leave
        const starContainer = document.querySelector('.star-rating');
        if (starContainer) {
            starContainer.addEventListener('mouseleave', function() {
                const currentRating = parseInt(ratingInput.value) || 0;
                starButtons.forEach((s, i) => {
                    const starIcon = s.querySelector('i');
                    if (i < currentRating) {
                        starIcon.className = 'fas fa-star text-warning';
                    } else {
                        starIcon.className = 'far fa-star text-muted';
                    }
                });
            });
        }
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Check star rating specifically
                const ratingInput = form.querySelector('#rating');
                if (ratingInput && !ratingInput.value) {
                    const errorElement = document.getElementById('rating-error');
                    if (errorElement) {
                        errorElement.style.display = 'block';
                        errorElement.textContent = 'Please select a rating';
                    }
                }
            }
            form.classList.add('was-validated');
        });
    });

    // Dark mode toggle
    const darkModeToggle = document.querySelector('.dark-mode-toggle');
    if (darkModeToggle) {
        // Check for saved theme preference or default to light mode
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);

        darkModeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // Navbar hide/show on scroll
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Scrolling down & past 100px
                navbar.classList.add('navbar-hidden');
            } else {
                // Scrolling up
                navbar.classList.remove('navbar-hidden');
            }
            
            lastScrollTop = scrollTop;
        }, { passive: true });
    }

    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Emergency ticker pause on mobile touch
    const emergencyTicker = document.querySelector('.emergency-ticker-content');
    if (emergencyTicker) {
        let touchStartX = 0;
        
        emergencyTicker.addEventListener('touchstart', function(e) {
            touchStartX = e.touches[0].clientX;
            this.style.animationPlayState = 'paused';
        }, { passive: true });
        
        emergencyTicker.addEventListener('touchend', function() {
            this.style.animationPlayState = 'running';
        }, { passive: true });
    }
});

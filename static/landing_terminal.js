// Terminal Landing Page JavaScript

// Update time display
function updateTime() {
    const timeDisplay = document.getElementById('timeDisplay');
    if (timeDisplay) {
        const now = new Date();
        const hours = String(now.getUTCHours()).padStart(2, '0');
        const minutes = String(now.getUTCMinutes()).padStart(2, '0');
        const seconds = String(now.getUTCSeconds()).padStart(2, '0');
        timeDisplay.textContent = `${hours}:${minutes}:${seconds} UTC`;
    }
}

// Typing effect
function typeText() {
    const typedTextElement = document.getElementById('typedText');
    if (!typedTextElement) return;
    
    const fullText = 'NEXT_GENERATION_SECURITY_TRAINING';
    let currentIndex = 0;
    
    function type() {
        if (currentIndex <= fullText.length) {
            typedTextElement.textContent = fullText.slice(0, currentIndex);
            currentIndex++;
            setTimeout(type, 100);
        }
    }
    
    type();
}

// Smooth scroll
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Scroll indicator visibility
function handleScrollIndicator() {
    const scrollIndicator = document.querySelector('.scroll-indicator');
    if (!scrollIndicator) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 200) {
            scrollIndicator.style.opacity = '0';
        } else {
            scrollIndicator.style.opacity = '0.6';
        }
    });
}

// Navigation scroll effect
function handleNavScroll() {
    const nav = document.querySelector('.terminal-nav');
    if (!nav) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            nav.style.background = 'rgba(0, 0, 0, 0.9)';
        } else {
            nav.style.background = 'rgba(0, 0, 0, 0.5)';
        }
    });
}

// Animate elements on scroll
function animateOnScroll() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe phase cards
    document.querySelectorAll('.phase-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // Observe enterprise cards
    document.querySelectorAll('.enterprise-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

// Initialize all functions
function init() {
    // Start time updates
    updateTime();
    setInterval(updateTime, 1000);
    
    // Start typing effect
    setTimeout(typeText, 1000);
    
    // Setup smooth scrolling
    setupSmoothScroll();
    
    // Handle scroll indicator
    handleScrollIndicator();
    
    // Handle nav scroll effect
    handleNavScroll();
    
    // Animate on scroll
    animateOnScroll();
    
    // Log initialization
    console.log('%c[CYBERVANTAGE]%c System initialized', 
                'color: #00d9ff; font-weight: bold;', 
                'color: #00ff41;');
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Easter egg: Konami code
(function() {
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;
    
    document.addEventListener('keydown', (e) => {
        if (e.key === konamiCode[konamiIndex]) {
            konamiIndex++;
            if (konamiIndex === konamiCode.length) {
                console.log('%c[SYSTEM]%c Access granted. Welcome, operator.', 
                           'color: #00ff41; font-weight: bold;', 
                           'color: #00d9ff;');
                konamiIndex = 0;
                // Add some visual feedback
                document.body.style.animation = 'flicker 0.5s';
                setTimeout(() => {
                    document.body.style.animation = '';
                }, 500);
            }
        } else {
            konamiIndex = 0;
        }
    });
})();

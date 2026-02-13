// ===== CUSTOM CURSOR =====
const cursor = document.querySelector('.custom-cursor');
const cursorDot = document.querySelector('.cursor-dot');

document.addEventListener('mousemove', (e) => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
    
    cursorDot.style.left = e.clientX + 'px';
    cursorDot.style.top = e.clientY + 'px';
});

// Hover effect on interactive elements
const interactiveElements = document.querySelectorAll('a, button, .glass-panel, .phase-card, .glass-card-3d');
interactiveElements.forEach(el => {
    el.addEventListener('mouseenter', () => {
        cursor.classList.add('hover');
    });
    el.addEventListener('mouseleave', () => {
        cursor.classList.remove('hover');
    });
});

// ===== NAVIGATION SCROLL EFFECT =====
const nav = document.querySelector('.glass-nav');
window.addEventListener('scroll', () => {
    if (window.scrollY > 100) {
        nav.classList.add('scrolled');
    } else {
        nav.classList.remove('scrolled');
    }
});

// ===== 3D SHIELD TILT EFFECT =====
const cyberShield = document.getElementById('cyberShield');

if (cyberShield) {
    cyberShield.addEventListener('mousemove', (e) => {
        const rect = cyberShield.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 15;
        const rotateY = (centerX - x) / 15;
        
        cyberShield.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
    });
    
    cyberShield.addEventListener('mouseleave', () => {
        cyberShield.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
    });
}

// ===== MAGNETIC BUTTONS =====
const magneticButtons = document.querySelectorAll('.btn-glass, .btn-outline, .btn-primary');

magneticButtons.forEach(button => {
    button.addEventListener('mousemove', (e) => {
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        
        const distance = Math.sqrt(x * x + y * y);
        const maxDistance = 80;
        
        if (distance < maxDistance) {
            const moveX = (x / maxDistance) * 15;
            const moveY = (y / maxDistance) * 15;
            button.style.transform = `translate(${moveX}px, ${moveY}px) translateY(-5px) scale(1.05)`;
        }
    });
    
    button.addEventListener('mouseleave', () => {
        button.style.transform = '';
    });
});

// ===== APPLE-STYLE SMOOTH SCROLL ANIMATIONS =====
const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            // Only observe once for smoother experience
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all sections with staggered animations
const sections = document.querySelectorAll('section');
sections.forEach(section => {
    observer.observe(section);
});

// ===== PHASE CARDS SMOOTH STAGGER ANIMATION =====
const phaseCards = document.querySelectorAll('.phase-card');
const cardObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const cards = entry.target.querySelectorAll('.phase-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 200); // Longer delay for smoother effect
            });
            cardObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

const phasesSection = document.querySelector('.phases-section');
if (phasesSection) {
    phaseCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(60px)';
        card.style.transition = 'all 1s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
    });
    cardObserver.observe(phasesSection);
}

// ===== GLASS PANELS SMOOTH REVEAL =====
const glassPanelsSection = document.querySelector('.features');
const panelObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const panels = entry.target.querySelectorAll('.glass-panel');
            panels.forEach((panel, index) => {
                setTimeout(() => {
                    panel.style.opacity = '1';
                    panel.style.transform = 'translateY(0)';
                }, index * 200);
            });
            panelObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

if (glassPanelsSection) {
    const panels = glassPanelsSection.querySelectorAll('.glass-panel');
    panels.forEach(panel => {
        panel.style.opacity = '0';
        panel.style.transform = 'translateY(60px)';
        panel.style.transition = 'all 1s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
    });
    panelObserver.observe(glassPanelsSection);
}

// ===== SMOOTH PARALLAX ON PHASE CARDS =====
phaseCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 30;
        const rotateY = (centerX - x) / 30;
        
        card.style.transition = 'border-color 0.3s ease, box-shadow 0.3s ease';
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-15px) scale(1.02)`;
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        card.style.transform = '';
    });
});

// ===== SMOOTH PARALLAX ON GLASS PANELS =====
const glassPanels = document.querySelectorAll('.glass-panel');
glassPanels.forEach(panel => {
    panel.addEventListener('mousemove', (e) => {
        const rect = panel.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 40;
        const rotateY = (centerX - x) / 40;
        
        panel.style.transition = 'border-color 0.3s ease, box-shadow 0.3s ease';
        panel.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-10px) scale(1.03)`;
    });
    
    panel.addEventListener('mouseleave', () => {
        panel.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        panel.style.transform = '';
    });
});

// ===== SMOOTH SCROLL =====
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

// ===== SMOOTH PARALLAX GRADIENT MESH =====
const meshGradients = document.querySelectorAll('.mesh-gradient');
let ticking = false;

window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(() => {
            const scrolled = window.pageYOffset;
            meshGradients.forEach((mesh, index) => {
                const speed = 0.2 + (index * 0.05); // Slower, more subtle
                mesh.style.transform = `translateY(${scrolled * speed}px)`;
            });
            ticking = false;
        });
        ticking = true;
    }
}, { passive: true });

// ===== PERFORMANCE: Reduce animations on slower devices =====
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (prefersReducedMotion) {
    document.body.style.setProperty('--animation-duration', '0s');
}

// ===== LOADING ANIMATION =====
window.addEventListener('load', () => {
    document.body.style.opacity = '1';
});

// ===== WORD REVEAL ANIMATION =====
function wrapWords() {
    const titleSpans = document.querySelectorAll('.hero-title .reveal-text');
    titleSpans.forEach(span => {
        const text = span.textContent;
        span.innerHTML = '';
        const words = text.trim().split(' ');
        words.forEach(word => {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'word';
            wordSpan.textContent = word + ' ';
            span.appendChild(wordSpan);
        });
    });
}

wrapWords();

// ===== PERFORMANCE OPTIMIZATIONS =====
// Debounce scroll events
let scrollTimeout;
window.addEventListener('scroll', () => {
    if (scrollTimeout) {
        window.cancelAnimationFrame(scrollTimeout);
    }
    scrollTimeout = window.requestAnimationFrame(() => {
        // Scroll-dependent animations here
    });
}, { passive: true });

// ===== MOBILE TOUCH SUPPORT =====
if ('ontouchstart' in window) {
    document.body.classList.add('touch-device');
    // Disable cursor on touch devices
    cursor.style.display = 'none';
    cursorDot.style.display = 'none';
}

console.log('%c🚀 CyberVantage 2026 - Modern Design Loaded', 'color: #00f2ff; font-size: 16px; font-weight: bold;');

document.addEventListener('DOMContentLoaded', () => {
    const cursor = document.querySelector('.custom-cursor');
    const cursorDot = document.querySelector('.cursor-dot');
    const isTouch = window.matchMedia('(pointer: coarse)').matches;

    if (cursor && cursorDot && !isTouch) {
        let mouseX = 0;
        let mouseY = 0;
        let cursorX = 0;
        let cursorY = 0;
        let dotX = 0;
        let dotY = 0;

        document.addEventListener('mousemove', (event) => {
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        function animateCursor() {
            // Smooth cursor movement
            cursorX += (mouseX - cursorX) * 0.2;
            cursorY += (mouseY - cursorY) * 0.2;
            dotX += (mouseX - dotX) * 0.5;
            dotY += (mouseY - dotY) * 0.5;

            cursor.style.left = `${cursorX}px`;
            cursor.style.top = `${cursorY}px`;
            cursorDot.style.left = `${dotX}px`;
            cursorDot.style.top = `${dotY}px`;

            requestAnimationFrame(animateCursor);
        }

        animateCursor();

        const interactiveElements = document.querySelectorAll('a, button, .tilt-card, .hero-visual, .phase-card, .glass-panel, .essential-card, .magnetic');
        interactiveElements.forEach((element) => {
            element.addEventListener('mouseenter', () => cursor.classList.add('hover'));
            element.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
        });
    }

    const revealItems = document.querySelectorAll('.reveal');
    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) {
                return;
            }

            const delay = Number(entry.target.dataset.delay || 0);
            window.setTimeout(() => {
                entry.target.classList.add('visible');
            }, delay);

            observer.unobserve(entry.target);
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    });

    revealItems.forEach((item) => revealObserver.observe(item));

    const tiltElements = document.querySelectorAll('.tilt-card, .hero-visual');
    tiltElements.forEach((element) => {
        element.addEventListener('mousemove', (event) => {
            if (isTouch) {
                return;
            }

            const rect = element.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 30;
            const rotateY = (centerX - x) / 30;

            element.style.transition = 'border-color 0.3s ease, box-shadow 0.3s ease';
            element.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-10px) scale(1.02)`;
        });

        element.addEventListener('mouseleave', () => {
            element.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            element.style.transform = '';
        });
    });

    const magneticButtons = document.querySelectorAll('.magnetic, .btn-primary, .btn-glass');
    magneticButtons.forEach((button) => {
        button.addEventListener('mousemove', (event) => {
            if (isTouch) {
                return;
            }

            const rect = button.getBoundingClientRect();
            const x = event.clientX - rect.left - rect.width / 2;
            const y = event.clientY - rect.top - rect.height / 2;
            const distance = Math.sqrt((x * x) + (y * y));
            const maxDistance = 80;

            if (distance < maxDistance) {
                const moveX = (x / maxDistance) * 15;
                const moveY = (y / maxDistance) * 15;
                button.style.transition = 'box-shadow 0.3s ease';
                button.style.transform = `translate(${moveX}px, ${moveY}px) translateY(-5px) scale(1.05)`;
            }
        });

        button.addEventListener('mouseleave', () => {
            button.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            button.style.transform = '';
        });
    });

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', (event) => {
            const href = anchor.getAttribute('href');
            if (!href || href === '#') {
                return;
            }

            const target = document.querySelector(href);
            if (!target) {
                return;
            }

            event.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        });
    });
});
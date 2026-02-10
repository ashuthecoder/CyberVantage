document.addEventListener('DOMContentLoaded', () => {

    // Mouse follower effect
    const cursorGlow = document.querySelector('.cursor-glow');

    document.addEventListener('mousemove', (e) => {
        const x = e.clientX;
        const y = e.clientY;

        cursorGlow.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
    });

    // Parallax effect for orbs
    document.addEventListener('mousemove', (e) => {
        const x = (window.innerWidth - e.pageX * 2) / 100;
        const y = (window.innerHeight - e.pageY * 2) / 100;

        const orbs = document.querySelectorAll('.liquid-orb');
        orbs.forEach((orb, index) => {
            const speed = (index + 1) * 2;
            orb.style.transform = `translate(${x * speed}px, ${y * speed}px)`;
        });
    });

    // Text Reveal Animation
    const headings = document.querySelectorAll('.hero-title .reveal-text');

    headings.forEach(heading => {
        const text = heading.textContent;
        heading.innerHTML = '';
        heading.classList.add('title-line'); // Add wrapper class for overflow hidden

        // Split text into characters
        [...text].forEach((char, index) => {
            const span = document.createElement('span');
            span.textContent = char === ' ' ? '\u00A0' : char; // Preserve spaces
            span.classList.add('char');
            span.style.animationDelay = `${index * 0.05}s`;
            heading.appendChild(span);
        });
    });

    // Glass card 3D tilt effect
    const card = document.querySelector('.glass-card-mockup');

    if (card) {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -10; // Invert to tilt towards mouse
            const rotateY = ((x - centerX) / centerX) * 10;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(5deg) rotateY(-15deg)'; // Return to initial state
        });
    }
});

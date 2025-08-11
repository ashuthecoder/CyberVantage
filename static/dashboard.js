document.addEventListener('DOMContentLoaded', function() {
    // Update username if available from session/local storage
    const username = localStorage.getItem('username') || sessionStorage.getItem('username');
    if (username) {
        document.getElementById('username').textContent = `Welcome, ${username}`;
    }
    
    // Add active state for buttons when pressed
    const sectionCards = document.querySelectorAll('.section-card');
    
    sectionCards.forEach(card => {
        card.addEventListener('mousedown', function() {
            this.style.transform = 'scale(0.98)';
        });
        
        card.addEventListener('mouseup', function() {
            this.style.transform = '';
        });
        
        // Optional: Add analytics tracking
        card.addEventListener('click', function() {
            const sectionId = this.id;
            // You can implement analytics tracking here
            console.log(`User clicked on ${sectionId}`);
        });
    });
});
document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Custom Cursor Follower
    const cursorGlow = document.getElementById('cursor-glow');
    
    document.addEventListener('mousemove', (e) => {
        if (cursorGlow) {
            cursorGlow.style.left = e.clientX + 'px';
            cursorGlow.style.top = e.clientY + 'px';
        }
    });

    // Handle interactive hover states (grow custom cursor on clickable items)
    const interactables = document.querySelectorAll('a, button, .solution-card');
    interactables.forEach(item => {
        item.addEventListener('mouseenter', () => {
            if (cursorGlow) {
                cursorGlow.style.transform = 'translate(-50%, -50%) scale(1.5)';
                cursorGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.06) 0%, rgba(0,0,0,0) 60%)';
            }
        });
        item.addEventListener('mouseleave', () => {
            if (cursorGlow) {
                cursorGlow.style.transform = 'translate(-50%, -50%) scale(1)';
                cursorGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.03) 0%, rgba(0,0,0,0) 60%)';
            }
        });
    });

    // 2. Scroll Reveal Animations (Intersection Observer Core)
    const observerOptions = {
        threshold: 0.05,            // Triggers quickly as soon as the card top cuts into view
        rootMargin: "0px 0px -40px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed'); // Toggles performance class safely
                observer.unobserve(entry.target);      // Disconnects observer to free memory
            }
        });
    }, observerOptions);

    const cards = document.querySelectorAll('.solution-card');
    cards.forEach((card, index) => {
        // Apply staggering delay directly via inline layout values
        card.style.transitionDelay = `${index * 0.12}s`;
        observer.observe(card);
    });

    // 3. Subtle Parallax for Background Orbs based on scroll
    const orbs = document.querySelectorAll('.bg-glow');
    if (orbs.length > 0) {
        window.addEventListener('scroll', () => {
            const scrolled = window.scrollY;
            orbs.forEach((orb, i) => {
                const speed = (i + 1) * 0.15;
                orb.style.transform = `translateY(${scrolled * speed}px)`;
            });
        }, { passive: true }); // Optimized scroll performance loop
    }
});
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
            cursorGlow.style.transform = 'translate(-50%, -50%) scale(1.5)';
            cursorGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.06) 0%, rgba(0,0,0,0) 60%)';
        });
        item.addEventListener('mouseleave', () => {
            cursorGlow.style.transform = 'translate(-50%, -50%) scale(1)';
            cursorGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.03) 0%, rgba(0,0,0,0) 60%)';
        });
    });

    // 2. Scroll Reveal Animations (Intersection Observer)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const cards = document.querySelectorAll('.solution-card');
    cards.forEach((card, index) => {
        // Initial state before reveal
        card.style.opacity = "0";
        card.style.transform = "translateY(40px)";
        card.style.transition = `all 0.6s cubic-bezier(0.22, 1, 0.36, 1) ${index * 0.15}s`;
        
        observer.observe(card);
    });

    // 3. Optional: Subtle Parallax for Background Orbs based on scroll
    const orbs = document.querySelectorAll('.bg-glow');
    if (orbs.length > 0) {
        window.addEventListener('scroll', () => {
            const scrolled = window.scrollY;
            orbs.forEach((orb, i) => {
                const speed = (i + 1) * 0.2;
                orb.style.transform = `translateY(${scrolled * speed}px)`;
            });
        });
    }
});

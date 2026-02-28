window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        setTimeout(() => {
            preloader.classList.add('hidden');
        }, 800); // 800ms minimum display for a smooth intro effect
    }
});

document.addEventListener('DOMContentLoaded', () => {

    // Navbar Scroll Effect
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Intersection Observer for Fade-Up Animations
    const fadeElements = document.querySelectorAll('.fade-up');

    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.15 // trigger when 15% visible
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Play animation only once
            }
        });
    }, observerOptions);

    fadeElements.forEach(el => {
        observer.observe(el);
    });

    // Immediately reveal hero elements that are in viewport on load
    const heroTextBlock = document.querySelector('.hero-text-block');
    const heroArcVisual = document.querySelector('.hero-arc-visual');
    if (heroTextBlock) heroTextBlock.classList.add('visible');
    if (heroArcVisual) heroArcVisual.classList.add('visible');

    // Hero Text Reveal Animation
    if (typeof gsap !== 'undefined') {
        gsap.fromTo('.reveal-text',
            { y: '100%', opacity: 0 },
            {
                y: '0%',
                opacity: 1,
                duration: 1.4,
                stagger: 0.2,
                ease: 'power4.out',
                delay: 0.8
            }
        );
    }

    // Subtle Parallax for hero particles
    const particles = document.getElementById('particles');
    window.addEventListener('scroll', () => {
        if (window.scrollY < window.innerHeight) {
            const val = window.scrollY * 0.4;
            particles.style.transform = `translateY(${val}px)`;
        }
    });

    // Generate floating spice particles (very minimal)
    const particleCount = 15;
    for (let i = 0; i < particleCount; i++) {
        let p = document.createElement('div');
        p.className = 'particle';

        let size = Math.random() * 6 + 2; // 2px to 8px
        p.style.width = size + 'px';
        p.style.height = size + 'px';

        let x = Math.random() * 100; // 0 to 100vw
        let y = Math.random() * 100; // 0 to 100vh

        p.style.left = x + '%';
        p.style.top = y + '%';

        // Random drift duration between 15s and 30s
        let duration = Math.random() * 15 + 15;
        p.style.animationDuration = duration + 's';

        // Random delay
        let delay = Math.random() * 5;
        p.style.animationDelay = delay + 's';

        particles.appendChild(p);
    }

    // Interactive Arc Carousel with GSAP
    if (typeof gsap !== 'undefined') {
        const satellites = document.querySelectorAll('.orbit-item');
        const mainPlate = document.getElementById('main-plate-img');
        const titleEl = document.getElementById('hero-title');
        const descEl = document.getElementById('hero-desc');
        const staggeredEls = document.querySelectorAll('.staggered-text');

        if (satellites.length > 0) {
            let currentIndex = 0;
            const totalItems = satellites.length;
            const angleStep = 360 / totalItems;

            // Proxy object for GSAP to tween smoothly
            let circleProxy = { rotation: 0 };
            const radius = 250;

            // Center of the orbit relative to .orbit-satellites container (600x300)
            const centerX = 300;
            const centerY = 300;

            function updatePositions() {
                satellites.forEach((sat, i) => {
                    let angleDeg = -90 + (i * angleStep) + circleProxy.rotation;
                    let rad = angleDeg * (Math.PI / 180);

                    let x = centerX + Math.cos(rad) * radius;
                    let y = centerY + Math.sin(rad) * radius;

                    sat.style.left = `${x}px`;
                    sat.style.top = `${y}px`;
                });
            }

            updatePositions();
            satellites[0].classList.add('active');

            // Ensure hero text is visible on initial load
            if (staggeredEls.length > 0) {
                gsap.set(staggeredEls, { y: 0, opacity: 1 });
            }

            function updateContent(index) {
                const sat = satellites[index];

                // Staggered text exit (only if elements exist)
                if (staggeredEls.length > 0) {
                    gsap.to(staggeredEls, {
                        y: 20,
                        opacity: 0,
                        duration: 0.3,
                        stagger: 0.05,
                        ease: "power2.in",
                        onComplete: () => {
                            // Update text
                            if (titleEl) titleEl.innerText = sat.getAttribute('data-title');
                            if (descEl) descEl.innerText = sat.getAttribute('data-desc');

                            // Staggered text enter
                            gsap.to(staggeredEls, {
                                y: 0,
                                opacity: 1,
                                duration: 0.5,
                                stagger: 0.08,
                                ease: "power2.out"
                            });
                        }
                    });
                }

                // Main plate transform transition
                gsap.to(mainPlate, {
                    scale: 0.85,
                    opacity: 0.2,
                    duration: 0.4,
                    ease: "power2.inOut",
                    onComplete: () => {
                        mainPlate.src = sat.getAttribute('data-img');
                        gsap.to(mainPlate, {
                            scale: 1,
                            opacity: 1,
                            duration: 0.6,
                            ease: "back.out(1.5)"
                        });
                    }
                });

                satellites.forEach(s => s.classList.remove('active'));
                satellites[index].classList.add('active');
            }

            function rotateWheel(direction) {
                if (gsap.isTweening(circleProxy)) return;

                if (direction === 'next') {
                    currentIndex = (currentIndex + 1) % totalItems;
                    gsap.to(circleProxy, {
                        rotation: circleProxy.rotation - angleStep,
                        duration: 1,
                        ease: "power3.inOut",
                        onUpdate: updatePositions
                    });
                } else {
                    currentIndex = (currentIndex - 1 + totalItems) % totalItems;
                    gsap.to(circleProxy, {
                        rotation: circleProxy.rotation + angleStep,
                        duration: 1,
                        ease: "power3.inOut",
                        onUpdate: updatePositions
                    });
                }
                updateContent(currentIndex);
            }

            let autoRotate = setInterval(() => {
                rotateWheel('next');
            }, 2500);

            const orbitContainer = document.querySelector('.hero-arc-visual');
            if (orbitContainer) {
                orbitContainer.addEventListener('mouseenter', () => clearInterval(autoRotate));
                orbitContainer.addEventListener('mouseleave', () => {
                    clearInterval(autoRotate);
                    autoRotate = setInterval(() => rotateWheel('next'), 2500);
                });
            }

            satellites.forEach((sat, index) => {
                sat.addEventListener('click', () => {
                    if (index === currentIndex || gsap.isTweening(circleProxy)) return;

                    let diff = currentIndex - index;
                    // optimize so it takes the shortest rotation path
                    if (diff > totalItems / 2) diff -= totalItems;
                    if (diff < -totalItems / 2) diff += totalItems;

                    currentIndex = index;
                    gsap.to(circleProxy, {
                        rotation: circleProxy.rotation + (diff * angleStep),
                        duration: 1,
                        ease: "power3.inOut",
                        onUpdate: updatePositions
                    });

                    updateContent(currentIndex);
                });
            });
        }
    }
});

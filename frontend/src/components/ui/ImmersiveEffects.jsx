import { useEffect, useRef } from 'react';

const REVEAL_SELECTORS = [
  "main [class*='rounded'][class*='border']",
  "main [class*='rounded-2xl'][class*='border'][class*='p-']",
  "main [class*='rounded-3xl'][class*='border'][class*='p-']",
  "main [class*='rounded-xl'][class*='border'][class*='p-']",
  '.card-hover',
  '.glass',
  '.btn-primary',
  "button[class*='bg-gradient']",
  "a[class*='bg-gradient']",
].join(', ');

export default function ImmersiveEffects() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.add('immersive-ready');

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const observed = new WeakSet();
    const revealTargets = new Set();

    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
          }
        });
      },
      { threshold: 0.14 }
    );

    const hydrateRevealTargets = () => {
      const targets = Array.from(document.querySelectorAll(REVEAL_SELECTORS));
      targets.forEach((el) => {
        if (observed.has(el)) return;
        observed.add(el);
        revealTargets.add(el);
        el.classList.add('ui-reveal-target');
        el.style.setProperty('--stagger', `${(revealTargets.size % 7) * 65}ms`);
        revealObserver.observe(el);
      });
    };

    hydrateRevealTargets();

    let mutationRaf = null;
    const mutationObserver = new MutationObserver(() => {
      if (mutationRaf) return;
      mutationRaf = window.requestAnimationFrame(() => {
        hydrateRevealTargets();
        mutationRaf = null;
      });
    });

    mutationObserver.observe(document.body, {
      childList: true,
      subtree: true,
    });

    if (prefersReducedMotion) {
      return () => {
        revealObserver.disconnect();
        mutationObserver.disconnect();
        if (mutationRaf) window.cancelAnimationFrame(mutationRaf);
      };
    }

    const pointer = { x: window.innerWidth * 0.5, y: window.innerHeight * 0.25 };

    const onPointerMove = (event) => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });

    const canvas = canvasRef.current;
    const context = canvas?.getContext('2d');
    let particles = [];
    let width = 0;
    let height = 0;
    let frameId = null;

    const resize = () => {
      if (!canvas || !context) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);

      const count = Math.max(36, Math.min(92, Math.floor((width * height) / 22000)));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.22,
        vy: (Math.random() - 0.5) * 0.22,
        r: 1.1 + Math.random() * 1.8,
      }));
    };

    const draw = () => {
      if (!context) return;
      context.clearRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        const dx = p.x - pointer.x;
        const dy = p.y - pointer.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 20000 && d2 > 0.001) {
          const boost = 0.16 / (d2 / 9000);
          const dist = Math.sqrt(d2);
          p.vx += (dx / dist) * boost;
          p.vy += (dy / dist) * boost;
        }

        p.vx *= 0.992;
        p.vy *= 0.992;

        context.beginPath();
        context.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        context.fillStyle = 'rgba(0, 73, 144, 0.44)';
        context.fill();
      }

      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 145) {
            context.strokeStyle = `rgba(56, 189, 248, ${0.2 * (1 - dist / 145)})`;
            context.lineWidth = 1;
            context.beginPath();
            context.moveTo(a.x, a.y);
            context.lineTo(b.x, b.y);
            context.stroke();
          }
        }
      }

      frameId = window.requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener('resize', resize, { passive: true });

    return () => {
      revealObserver.disconnect();
      mutationObserver.disconnect();
      window.removeEventListener('resize', resize);
      window.removeEventListener('pointermove', onPointerMove);
      if (frameId) window.cancelAnimationFrame(frameId);
      if (mutationRaf) window.cancelAnimationFrame(mutationRaf);
    };
  }, []);

  return (
    <>
      <canvas ref={canvasRef} className="immersive-canvas" aria-hidden="true" />
    </>
  );
}

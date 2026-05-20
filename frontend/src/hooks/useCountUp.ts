import { useEffect, useRef, useState } from "react";

export function useCountUp(target: number, duration = 1400): [number, (el: Element | null) => void] {
  const [count, setCount] = useState(0);
  const [inView, setInView] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const rafRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const hasRun = useRef(false);

  const ref = (el: Element | null) => {
    if (observerRef.current) observerRef.current.disconnect();
    if (!el) return;
    observerRef.current = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setInView(true); },
      { threshold: 0.3 }
    );
    observerRef.current.observe(el);
  };

  useEffect(() => {
    if (!inView || hasRun.current || target === 0) {
      if (target === 0) setCount(0);
      return;
    }
    hasRun.current = true;
    startTimeRef.current = null;

    const tick = (ts: number) => {
      if (!startTimeRef.current) startTimeRef.current = ts;
      const progress = Math.min((ts - startTimeRef.current) / duration, 1);
      // ease out expo
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setCount(Math.round(eased * target));
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [inView, target, duration]);

  return [count, ref];
}

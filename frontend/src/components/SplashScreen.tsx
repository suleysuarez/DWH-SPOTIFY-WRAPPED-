import { useEffect, useRef } from "react";
import gsap from "gsap";

interface SplashScreenProps {
  onComplete: () => void;
}

export default function SplashScreen({ onComplete }: SplashScreenProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<SVGSVGElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const barRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const tl = gsap.timeline({
      onComplete: () => {
        gsap.to(containerRef.current, {
          opacity: 0,
          duration: 0.5,
          ease: "power2.inOut",
          onComplete,
        });
      },
    });

    // Initial state
    gsap.set([logoRef.current, titleRef.current, subtitleRef.current], {
      opacity: 0,
      y: 30,
    });
    gsap.set(barRefs.current, { scaleY: 0, transformOrigin: "bottom" });

    tl
      .to(logoRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6,
        ease: "back.out(1.7)",
      })
      .to(
        titleRef.current,
        { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" },
        "-=0.3"
      )
      .to(
        subtitleRef.current,
        { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" },
        "-=0.2"
      )
      .to(
        barRefs.current,
        {
          scaleY: 1,
          duration: 0.4,
          stagger: 0.08,
          ease: "elastic.out(1, 0.5)",
        },
        "-=0.1"
      )
      // Glow pulse on logo
      .to(
        logoRef.current,
        {
          filter: "drop-shadow(0 0 18px #1DB954) drop-shadow(0 0 40px #1DB95466)",
          duration: 0.5,
          ease: "power2.inOut",
          yoyo: true,
          repeat: 1,
        },
        "-=0.3"
      )
      // Hold for a moment then fade out
      .to({}, { duration: 0.6 });

    return () => {
      tl.kill();
    };
  }, [onComplete]);

  const barHeights = [40, 60, 80, 55, 70, 45, 65, 50];

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center"
      style={{ background: "#121212" }}
    >
      <img
        ref={logoRef as React.RefObject<HTMLImageElement>}
        src="/images/logo_spotify.png"
        alt="Spotify"
        width={80}
        height={80}
        style={{ objectFit: "contain", opacity: 0 }}
      />

      <h1
        ref={titleRef}
        className="mt-6 text-3xl font-bold tracking-tight"
        style={{ color: "#fff", opacity: 0 }}
      >
        Spotify Wrapped{" "}
        <span style={{ color: "#1DB954" }}>DWH</span>
      </h1>

      <p
        ref={subtitleRef}
        className="mt-2 text-sm"
        style={{ color: "rgba(255,255,255,0.45)", opacity: 0 }}
      >
        Tu historial musical, analizado
      </p>

      {/* Equalizer bars */}
      <div className="mt-10 flex items-end gap-1" style={{ height: 80 }}>
        {barHeights.map((h, i) => (
          <div
            key={i}
            ref={(el) => { barRefs.current[i] = el; }}
            style={{
              width: 6,
              height: h,
              background: "#1DB954",
              borderRadius: 3,
              opacity: 0.85,
            }}
          />
        ))}
      </div>
    </div>
  );
}

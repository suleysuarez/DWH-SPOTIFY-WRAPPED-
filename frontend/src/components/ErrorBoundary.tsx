import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  showStack: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, showStack: false };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      const { error, showStack } = this.state;
      return (
        <div style={{
          minHeight: "100vh", background: "#121212", display: "flex",
          alignItems: "center", justifyContent: "center",
          position: "relative", overflow: "hidden", fontFamily: "DM Sans, sans-serif",
        }}>
          {/* Grid de fondo */}
          <div style={{
            position: "absolute", inset: 0, pointerEvents: "none",
            backgroundImage: `linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
            maskImage: `radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%)`,
          }} />

          {/* Glow rojo pulsante */}
          <div style={{
            position: "absolute", width: 600, height: 600, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(239,68,68,0.15) 0%, transparent 65%)",
            filter: "blur(55px)", pointerEvents: "none",
          }} />

          <div style={{
            position: "relative", zIndex: 1, width: "100%", maxWidth: 680,
            padding: "48px 32px", display: "flex", flexDirection: "column", alignItems: "center",
          }}>
            {/* Logo */}
            <img src="/images/logo_spotify.png" alt="Spotify"
              style={{ width: 34, height: 34, objectFit: "contain", opacity: 0.45, marginBottom: 32 }} />

            {/* Icono de error */}
            <div style={{
              width: 72, height: 72, borderRadius: "50%",
              background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)",
              display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24,
            }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>

            {/* Título */}
            <h1 style={{ fontSize: "clamp(1.6rem,3vw,2.2rem)", fontWeight: 900, color: "#fff", marginBottom: 8, textAlign: "center" }}>
              Algo salió mal
            </h1>
            <p style={{ fontSize: 15, color: "rgba(255,255,255,0.4)", marginBottom: 32, textAlign: "center", lineHeight: 1.7, maxWidth: 400 }}>
              {error?.message ?? "Se produjo un error inesperado en la aplicación."}
            </p>

            {/* Acciones */}
            <div style={{ display: "flex", gap: 12, marginBottom: 28, flexWrap: "wrap", justifyContent: "center" }}>
              <button
                type="button"
                onClick={() => window.location.reload()}
                style={{
                  display: "inline-flex", alignItems: "center", gap: 8,
                  background: "linear-gradient(135deg, #EF4444, #EF4444cc)",
                  color: "#fff", fontWeight: 800, borderRadius: 9999,
                  padding: "11px 28px", fontSize: 13, border: "none", cursor: "pointer",
                  boxShadow: "0 4px 24px rgba(239,68,68,0.4)", letterSpacing: "0.04em",
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 102.13-9.36L1 10" />
                </svg>
                RECARGAR PÁGINA
              </button>

              <button
                type="button"
                onClick={() => (window.location.href = "/")}
                style={{
                  display: "inline-flex", alignItems: "center", gap: 8,
                  background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.15)",
                  color: "rgba(255,255,255,0.7)", fontWeight: 700, borderRadius: 9999,
                  padding: "11px 28px", fontSize: 13, cursor: "pointer", letterSpacing: "0.04em",
                }}
              >
                IR AL INICIO
              </button>
            </div>

            {/* Stack trace colapsable */}
            <button
              type="button"
              onClick={() => this.setState(s => ({ showStack: !s.showStack }))}
              style={{
                background: "none", border: "none", cursor: "pointer",
                color: "rgba(255,255,255,0.25)", fontSize: 12, marginBottom: 12,
                display: "flex", alignItems: "center", gap: 6, letterSpacing: "0.05em",
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                style={{ transform: showStack ? "rotate(90deg)" : "none", transition: "transform 0.2s" }}>
                <polyline points="9 18 15 12 9 6" />
              </svg>
              {showStack ? "OCULTAR" : "VER"} DETALLES TÉCNICOS
            </button>

            {showStack && (
              <div style={{
                width: "100%", background: "rgba(0,0,0,0.5)", border: "1px solid rgba(239,68,68,0.15)",
                borderRadius: 12, padding: "16px 20px", maxHeight: 240, overflowY: "auto",
              }}>
                <pre style={{
                  margin: 0, fontSize: 11, lineHeight: 1.7,
                  color: "rgba(255,255,255,0.45)", whiteSpace: "pre-wrap", wordBreak: "break-all",
                }}>
                  {error?.stack}
                </pre>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

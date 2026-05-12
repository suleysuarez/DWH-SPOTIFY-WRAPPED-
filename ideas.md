# Ideas de Diseño — Mi Spotify Wrapped DWH

<response>
<text>
**Opción A — Data Noir / Terminal Analítico**
- **Design Movement**: Neo-brutalism oscuro + estética de terminal
- **Core Principles**: Contraste extremo, tipografía monoespaciada para datos, jerarquía mediante tamaño, crudeza funcional
- **Color Philosophy**: Negro puro (#0A0A0A) con verde Spotify (#1DB954) como único acento; texto blanco roto (#E8E8E8); rojo error (#FF4444)
- **Layout Paradigm**: Columnas asimétricas tipo periódico; sidebar fijo de 240px; contenido principal con grilla de 12 columnas
- **Signature Elements**: Bordes de 1px verde en cards activos; números de datos en Fira Code; separadores horizontales finos
- **Interaction Philosophy**: Hover revela información adicional con transición de 150ms; clicks producen feedback inmediato
- **Animation**: Entrada de datos con counter-up; barras de progreso con ease-out; skeleton loaders con shimmer
- **Typography System**: JetBrains Mono para datos/código; Inter para UI; escala modular 1.25
</text>
<probability>0.08</probability>
</response>

<response>
<text>
**Opción B — Glassmorphism Premium Dark (SELECCIONADA)**
- **Design Movement**: Glassmorphism + Material Design 3 oscuro
- **Core Principles**: Profundidad mediante capas de vidrio, luz ambiental verde, espaciado generoso, jerarquía visual clara
- **Color Philosophy**: Fondo #121212 con capas de vidrio semitransparente; verde Spotify como luz de acento; gradientes sutiles de #1DB954 a transparente
- **Layout Paradigm**: Sidebar fijo con blur + área de contenido fluida; cards flotantes con sombra de color; grid responsivo de 3 columnas en dashboard
- **Signature Elements**: Cards con `backdrop-blur` y borde `rgba(255,255,255,0.08)`; glow verde en elementos activos; avatares con ring verde
- **Interaction Philosophy**: Hover eleva cards con `translateY(-2px)` y aumenta el glow; estados de carga con skeleton glassmorphism
- **Animation**: Framer Motion para transiciones de página (fade+slide 300ms); stagger en listas de artistas/tracks; contador animado en KPIs
- **Typography System**: Circular Std (via Google Fonts alternativa: Nunito) para headings; Inter para body; peso 700 para números grandes
</text>
<probability>0.09</probability>
</response>

<response>
<text>
**Opción C — Spotify Clone Fiel + Analítica Elevada**
- **Design Movement**: Diseño de producto Spotify + dashboard de BI
- **Core Principles**: Fidelidad a la marca Spotify, densidad de información alta, navegación familiar, datos como protagonistas
- **Color Philosophy**: Paleta exacta de Spotify; verde como CTA y acento; grises escalonados para jerarquía de contenido
- **Layout Paradigm**: Top navbar + sidebar colapsable; contenido en scroll vertical; secciones con títulos grandes al estilo Spotify
- **Signature Elements**: Gradientes de portada de álbum; hover con overlay verde; tipografía bold al estilo Spotify
- **Interaction Philosophy**: Interacciones familiares para usuarios de Spotify; feedback visual inmediato
- **Animation**: Transiciones suaves entre rutas; animaciones de carga tipo Spotify
- **Typography System**: Circular Std / Nunito Bold para títulos; Inter Regular para body
</text>
<probability>0.07</probability>
</response>

---

## Decisión Final: **Opción B — Glassmorphism Premium Dark**

Filosofía elegida: capas de vidrio oscuro con luz ambiental verde Spotify, profundidad visual mediante blur y sombras de color, animaciones físicamente intuitivas con Framer Motion, tipografía Nunito para headings e Inter para body.

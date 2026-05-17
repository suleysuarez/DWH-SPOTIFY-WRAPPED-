/**
 * main.tsx — Punto de entrada de la aplicación React.
 * Monta <App /> en el elemento #root del HTML y carga los estilos globales (index.css).
 */

import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);

/**
 * vite.config.ts — Configuración de Vite para el proyecto.
 *
 * Root: frontend/ — el build se genera en dist/public/.
 * Aliases: @ → frontend/src, @shared → shared/, @assets → attached_assets/
 * envDir apunta a la raíz del monorepo (lee .env / .env.local allí).
 *
 * Plugins activos:
 *   - @vitejs/plugin-react (JSX + Fast Refresh)
 *   - @tailwindcss/vite (Tailwind CSS 4 via Vite)
 */

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

const plugins = [react(), tailwindcss()];

export default defineConfig({
  plugins,
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "frontend", "src"),
      "@shared": path.resolve(import.meta.dirname, "shared"),
      "@assets": path.resolve(import.meta.dirname, "attached_assets"),
    },
  },
  envDir: path.resolve(import.meta.dirname),
  root: path.resolve(import.meta.dirname, "frontend"),
  build: {
    outDir: path.resolve(import.meta.dirname, "dist/public"),
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    strictPort: false, // Will find next available port if 3000 is busy
    host: "127.0.0.1",
    allowedHosts: ["localhost", "127.0.0.1"],
    fs: {
      strict: true,
      deny: ["**/.*"],
    },
  },
});

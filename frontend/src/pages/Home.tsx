/**
 * Home.tsx — Página de ejemplo / placeholder (no está en el router activo).
 *
 * ⚠️  Esta página NO está registrada en App.tsx. Es una plantilla generada
 * automáticamente por el scaffolding de Manus con ejemplos de uso de componentes.
 * No tiene función en el flujo del DWH; se conserva como referencia.
 */
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { Streamdown } from 'streamdown';
export default function Home() {
  // If theme is switchable in App.tsx, we can implement theme toggling like this:
  // const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex flex-col">
      <main>
        {/* Example: lucide-react for icons */}
        <Loader2 className="animate-spin" />
        Example Page
        {/* Example: Streamdown for markdown rendering */}
        <Streamdown>Any **markdown** content</Streamdown>
        <Button variant="default">Example Button</Button>
      </main>
    </div>
  );
}

import ErrorPage from "@/components/ui/ErrorPage";
import { useLocation } from "wouter";

export default function ServerError() {
  const [, setLocation] = useLocation();

  return (
    <ErrorPage
      code="500"
      title="Algo salió mal"
      description="El servidor encontró un error inesperado. Intenta de nuevo en unos momentos."
      accentColor="#EF4444"
      actionLabel="Reintentar"
      onAction={() => setLocation("/")}
    />
  );
}

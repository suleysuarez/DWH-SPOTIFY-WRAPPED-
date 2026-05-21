import ErrorPage from "@/components/ui/ErrorPage";

export default function Unauthorized() {
  return (
    <ErrorPage
      code="401"
      title="Sesión expirada"
      description="Tu sesión ha expirado o no tienes permiso para acceder a esta página. Inicia sesión de nuevo."
      accentColor="#F59E0B"
      actionLabel="Iniciar sesión"
      actionHref="/login"
    />
  );
}

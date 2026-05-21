import ErrorPage from "@/components/ui/ErrorPage";

export default function NotFound() {
  return (
    <ErrorPage
      code="404"
      title="Esta pista no existe"
      description="La página que buscas no está disponible o fue removida del servidor."
      accentColor="#1DB954"
      actionLabel="Volver al inicio"
      actionHref="/"
    />
  );
}

import { useParams, Navigate } from "react-router-dom";
import { ragConfigs } from "./rag.config";

export default function RagPage() {
  const { type } = useParams<{ type: string }>();
  const config = type ? ragConfigs[type] : undefined;

  if (!config) {
    return <Navigate to="/chat" replace />;
  }

  return (
    <div className="flex h-full flex-col gap-2 p-6">
      <h1 className="text-2xl font-semibold">{config.title}</h1>
      <p className="text-muted-foreground">{config.description}</p>
    </div>
  );
}

import { NotFoundView } from "@/features/error/components/not-found-view";
import { useNotFoundViewModel } from "@/features/error/hooks/use-not-found-view-model";

export default function NotFoundPage() {
  const viewModel = useNotFoundViewModel();

  return (
    <NotFoundView viewModel={viewModel} />
  );
}

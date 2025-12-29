import { ToolsView } from "@/features/tools/components/tools-view";
import { useToolsViewModel } from "@/features/tools/hooks/use-tools-view-model";

export default function ToolsPage() {
  const viewModel = useToolsViewModel();

  return (
    <ToolsView viewModel={viewModel} />
  );
}

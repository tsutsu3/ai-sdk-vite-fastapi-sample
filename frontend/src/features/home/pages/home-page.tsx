import { HomeView } from "@/features/home/components/home-view";
import { useHomeViewModel } from "@/features/home/hooks/use-home-view-model";

export default function HomePage() {
  const viewModel = useHomeViewModel();

  return (
    <HomeView viewModel={viewModel} />
  );
}

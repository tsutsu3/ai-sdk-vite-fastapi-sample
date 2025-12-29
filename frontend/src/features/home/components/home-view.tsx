export type HomeViewModel = {};

export type HomeViewProps = {
  viewModel: HomeViewModel;
};

export const HomeView = (_props: HomeViewProps) => (
  <div className="flex flex-col gap-8 p-6">
    {/* Header */}
    <header className="space-y-1">
      <h1 className="text-2xl font-semibold tracking-tight">Home</h1>
      <p className="text-muted-foreground text-sm">
        Welcome back. Choose what you want to work on.
      </p>
    </header>
    {/* Main entry points */}
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"></section>
  </div>
);

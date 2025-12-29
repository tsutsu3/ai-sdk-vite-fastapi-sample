import { Link } from "react-router";
import { cn } from "@/lib/utils";

export type NotFoundViewModel = {
  t: (key: string) => string;
};

export type NotFoundViewProps = {
  viewModel: NotFoundViewModel;
};

export const NotFoundView = ({ viewModel }: NotFoundViewProps) => (
  <div
    className={cn(
      "bg-background flex min-h-[calc(100vh-56px-32px-32px)] flex-col items-center justify-center px-4 py-12 sm:px-6 lg:px-8",
    )}
  >
    <div className="mx-auto max-w-md text-center">
      <div className="inline-flex items-center rounded-lg pb-4 text-6xl font-bold">
        404
      </div>
      <h1 className="text-foregroundl mt-6 text-4xl font-bold tracking-tight">
        {viewModel.t("pageNotFound")}
      </h1>
      <p className="text-muted-foreground mt-4">
        {viewModel.t("pageNotFoundMessage")}
      </p>
      <div className="mt-6">
        <Link
          to="/"
          className="bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-primary inline-flex items-center rounded-md px-4 py-2 text-sm font-medium shadow-sm transition-colors focus:ring-2 focus:ring-offset-2 focus:outline-none"
        >
          {viewModel.t("goToHome")}
        </Link>
      </div>
    </div>
  </div>
);

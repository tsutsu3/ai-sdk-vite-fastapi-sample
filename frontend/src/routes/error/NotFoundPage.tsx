import { Link } from "react-router";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";

export default function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <div
      className={cn(
        "flex min-h-[calc(100vh-56px-32px-32px)] flex-col items-center justify-center bg-background px-4 py-12 sm:px-6 lg:px-8"
      )}
    >
      <div className="mx-auto max-w-md text-center">
        <div className="inline-flex items-center rounded-lg pb-4 text-6xl font-bold">
          404
        </div>
        <h1 className="mt-6 text-4xl font-bold tracking-tight text-foregroundl">
          {t("pageNotFound")}
        </h1>
        <p className="mt-4 text-muted-foreground">{t("pageNotFoundMessage")}</p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            {t("goToHome")}
          </Link>
        </div>
      </div>
    </div>
  );
}

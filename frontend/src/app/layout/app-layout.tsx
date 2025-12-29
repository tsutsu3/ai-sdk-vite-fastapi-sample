import { AppSidebar } from "@/components/app/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Outlet } from "react-router";
import { Fragment } from "react";
import { useAppLayoutViewModel } from "./use-app-layout-view-model";

type AppLayoutViewProps = {
  viewModel: ReturnType<typeof useAppLayoutViewModel>;
};

const AppLayoutView = ({ viewModel }: AppLayoutViewProps) => {
  const { breadcrumbs, sidebar } = viewModel;

  return (
    <>
      <AppSidebar viewModel={sidebar} />
      <SidebarInset className="flex h-screen min-h-0 min-w-0 flex-col">
        {/* Navbar / Header */}
        <header className="bg-background sticky top-0 z-10 flex h-16 items-center gap-2 border-b">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator
              orientation="vertical"
              className="mr-2 data-[orientation=vertical]:h-4"
            />
            <Breadcrumb>
              <BreadcrumbList>
                {breadcrumbs.map((label, index) => {
                  const isLast = index === breadcrumbs.length - 1;
                  return (
                    <Fragment key={index}>
                      <BreadcrumbItem>
                        <BreadcrumbPage>{label}</BreadcrumbPage>
                      </BreadcrumbItem>
                      {!isLast && <BreadcrumbSeparator />}
                    </Fragment>
                  );
                })}
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>
        {/* Main content (scrollable) */}
        <main className="min-h-0 flex-1 overflow-hidden">
          <div className="h-full min-h-0 w-full pb-0">
            <Outlet />
          </div>
        </main>
      </SidebarInset>
    </>
  );
};

const AppLayoutViewModel = () => {
  const viewModel = useAppLayoutViewModel();
  return <AppLayoutView viewModel={viewModel} />;
};

export const AppLayout = () => {
  return (
    <SidebarProvider>
      <AppLayoutViewModel />
    </SidebarProvider>
  );
}

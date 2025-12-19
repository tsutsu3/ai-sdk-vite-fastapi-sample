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
import { Outlet, useLocation } from "react-router";
import { Fragment } from "react";

export default function AppLayout() {
  const location = useLocation();

  const segments = location.pathname.split("/").filter(Boolean);
  const breadcrumbs = ["Home", ...segments];

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex flex-col">
        {/* Navbar / Header */}
        <header className="sticky top-0 z-10 flex h-16 items-center gap-2 border-b bg-background">
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
        <main className="flex-1 overflow-hidden px-4">
          <div className="mx-auto w-full max-w-5xl py-6 h-full">
            <Outlet />
          </div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}

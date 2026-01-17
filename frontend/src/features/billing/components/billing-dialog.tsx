import {
  Bar,
  BarChart,
  CartesianGrid,
  YAxis,
} from "recharts";
import { Circle, CreditCard, Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ButtonGroup,
  ButtonGroupSeparator,
} from "@/components/ui/button-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { cn } from "@/lib/utils";
import {
  billingItems,
  type BillingScope,
  useBillingDialogViewModel,
} from "@/features/billing/hooks/use-billing-dialog-view-model";

const scopeOptions: Array<{ id: BillingScope; label: string }> = [
  { id: "personal", label: "Personal" },
  { id: "tenant", label: "Tenant" },
  { id: "tool", label: "Tool" },
];

const chartConfig = {
  ai: { label: "AI", color: "hsl(var(--chart-1))" },
  files: { label: "File Storage", color: "hsl(var(--chart-2))" },
  history: { label: "Conversation History", color: "hsl(var(--chart-3))" },
  search: { label: "Vector Search", color: "hsl(var(--chart-4))" },
};

export type BillingDialogViewModel = ReturnType<
  typeof useBillingDialogViewModel
>;

export type BillingDialogViewProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  viewModel: BillingDialogViewModel;
};

export const BillingDialogView = ({
  open,
  onOpenChange,
  viewModel,
}: BillingDialogViewProps) => {
  const {
    scope,
    setScope,
    tenantId,
    setTenantId,
    toolId,
    setToolId,
    month,
    setMonth,
    yesterday,
    chartData,
  } = viewModel;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background flex max-h-[90vh] flex-col overflow-hidden rounded-2xl px-0 shadow-2xl md:max-w-5xl">
        <DialogTitle className="sr-only">Billing overview</DialogTitle>
        <DialogDescription className="sr-only">
          Monthly usage and cost summary.
        </DialogDescription>

        {/* Header */}
        <div className="px-6 py-2">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="bg-muted/40 flex h-11 w-11 items-center justify-center rounded-xl border">
                <CreditCard className="text-foreground size-5" />
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Billing</p>
                <h2 className="text-lg font-semibold">Usage & Cost</h2>
                <p className="text-muted-foreground mt-1 text-xs">
                  Snapshot for {month}
                </p>
              </div>
            </div>
            <div className="text-muted-foreground flex items-center gap-2 rounded-full border px-3 py-1 text-xs">
              <Sparkles className="size-3.5" />
              Data through {yesterday} (yesterday only)
            </div>
          </div>
        </div>

        {/* Contents */}
        <div className="bg-sidebar min-h-0 flex-1 overflow-y-auto px-6 py-6">
          <div className="grid gap-4">
            <div className="bg-muted/20 flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3">
              <ButtonGroup className="rounded-lg p-1 shadow-xs">
                {scopeOptions.map((option) => (
                  <Button
                    key={option.id}
                    type="button"
                    variant={scope === option.id ? "default" : "outline"}
                    onClick={() => setScope(option.id)}
                    className={cn(
                      "h-9 px-3 text-xs font-semibold",
                      scope === option.id
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border",
                    )}
                  >
                    {option.label}
                  </Button>
                ))}
                <ButtonGroupSeparator />
                <Select value={month} onValueChange={setMonth}>
                  <SelectTrigger className="bg-background h-9 w-35">
                    <SelectValue placeholder="Month" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2025-12">Dec 2025</SelectItem>
                    <SelectItem value="2025-11">Nov 2025</SelectItem>
                    <SelectItem value="2025-10">Oct 2025</SelectItem>
                  </SelectContent>
                </Select>
              </ButtonGroup>

              <div className="flex flex-wrap gap-2">
                {scope !== "personal" && (
                  <Select value={tenantId} onValueChange={setTenantId}>
                    <SelectTrigger className="bg-background h-9 w-45">
                      <SelectValue placeholder="Tenant" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tenant-001">Tenant 001</SelectItem>
                      <SelectItem value="tenant-002">Tenant 002</SelectItem>
                    </SelectContent>
                  </Select>
                )}
                {scope === "tool" && (
                  <Select value={toolId} onValueChange={setToolId}>
                    <SelectTrigger className="bg-background h-9 w-45">
                      <SelectValue placeholder="Tool" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="assistant">Assistant</SelectItem>
                      <SelectItem value="files">File Tools</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Card className="shadow-sm">
                <CardHeader>
                  <CardTitle>Monthly cost breakdown</CardTitle>
                  <CardDescription>
                    Aggregated usage by service for {month}
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-60">
                  <ChartContainer
                    className="h-full w-full"
                    config={chartConfig}
                  >
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <YAxis
                        tickLine={false}
                        axisLine={false}
                        width={40}
                        tickFormatter={(value) => `$${value}`}
                      />
                      <ChartTooltip
                        content={<ChartTooltipContent hideLabel nameKey="id" />}
                      />
                      <ChartLegend
                        verticalAlign="bottom"
                        content={<ChartLegendContent />}
                      />
                      {chartData.map((entry, idx) => (
                        <Bar
                          dataKey={entry.id}
                          radius={[8, 8, 0, 0]}
                          fill={`var(--chart-${idx + 1})`}
                        />
                      ))}
                      {/* <Bar dataKey="ai" radius={[8, 8, 0, 0]} />
                      <Bar dataKey="files" radius={[8, 8, 0, 0]} />
                      <Bar dataKey="history" radius={[8, 8, 0, 0]} />
                      <Bar dataKey="search" radius={[8, 8, 0, 0]} /> */}
                    </BarChart>
                  </ChartContainer>
                </CardContent>
              </Card>

              <Card className="shadow-sm">
                <CardHeader>
                  <CardTitle>Total cost</CardTitle>
                  <CardDescription>Yesterday's usage only</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-primary text-3xl font-semibold">
                    $61.99
                  </div>
                  <p className="text-muted-foreground mt-2 text-sm">
                    Includes AI, storage, history, and vector search. Values
                    shown are based on monthly aggregation through {yesterday}.
                  </p>
                  <div className="text-muted-foreground mt-4 grid gap-4 text-xs">
                    <div className="flex items-center justify-between">
                      <span>AI</span>
                      <span className="text-foreground">$42.30</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>File Storage</span>
                      <span className="text-foreground">$8.70</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Conversation History</span>
                      <span className="text-foreground">$4.15</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Vector Search</span>
                      <span className="text-foreground">$6.84</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {billingItems.map((item, idx) => (
                <Card
                  key={item.id}
                  className={`bg-background shadow-sm transition hover:shadow-md`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <Circle
                            className="size-4 text-transparent"
                            style={{
                              fill: `var(--chart-${idx + 1})`,
                            }}
                          />
                          {item.name}
                        </CardTitle>
                        <CardDescription>{item.description}</CardDescription>
                      </div>
                      <div className="text-right">
                        <p className="text-muted-foreground text-xs">Cost</p>
                        <p className="text-primary text-lg font-semibold">
                          {item.cost}
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground text-xs font-semibold">
                      Billable usage
                    </p>
                    <div className="mt-2 grid gap-2 text-sm">
                      {item.usage.map((metric) => (
                        <div
                          key={metric.label}
                          className="flex items-center justify-between border-b border-dashed pb-2 last:border-none last:pb-0"
                        >
                          <span className="text-muted-foreground">
                            {metric.label}
                          </span>
                          <span className="font-medium">{metric.value}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

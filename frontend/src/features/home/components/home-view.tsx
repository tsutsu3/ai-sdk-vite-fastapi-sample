import { Link } from "react-router";
import { MessageCircleMore } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type {
  HomeViewModel,
  ToolCard,
  ToolSection,
} from "@/features/home/hooks/use-home-view-model";

export type HomeViewProps = {
  viewModel: HomeViewModel;
};

const ToolCardItem = ({ card, index }: { card: ToolCard; index: number }) => {
  const Icon = card.icon;
  const { t } = useTranslation();

  return (
    <Link to={card.path} className="group">
      <Card className="h-full border-muted/60 bg-card/80 transition-all group-hover:-translate-y-0.5 group-hover:border-foreground/10 group-hover:bg-muted/30 group-hover:shadow-lg">
        <div className="flex h-full flex-col gap-5 px-6 py-5">
          <div className="flex items-center justify-between">
            <span className="bg-muted text-foreground inline-flex h-10 w-10 items-center justify-center rounded-xl">
              <Icon className="h-5 w-5" />
            </span>
            <span className="text-muted-foreground text-xs">
              {t("homeToolLabel", { defaultValue: "Tool" })} {index + 1}
            </span>
          </div>
          <div className="space-y-2">
            <CardTitle className="text-lg">
              {t(card.labelKey, { defaultValue: card.id })}
            </CardTitle>
            <CardDescription>
              {t(card.descriptionKey, { defaultValue: t("homeToolDescription") })}
            </CardDescription>
          </div>
        </div>
      </Card>
    </Link>
  );
};

const ToolSectionBlock = ({ section }: { section: ToolSection }) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-3">
      <div className="text-muted-foreground text-xs font-semibold uppercase tracking-wide">
        {t(section.labelKey, { defaultValue: section.id })}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {section.items.map((card, index) => (
          <ToolCardItem key={card.id} card={card} index={index} />
        ))}
      </div>
    </div>
  );
};

export const HomeView = ({ viewModel }: HomeViewProps) => {
  const { t } = useTranslation();

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-6">
      <section className="space-y-4">
        <div className="space-y-1">
          <div className="text-muted-foreground text-xs font-semibold uppercase tracking-wide">
            {t("homeSectionChatLabel")}
          </div>
          <h2 className="text-xl font-semibold">
            {t("homeSectionChatTitle")}
          </h2>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <Link to={viewModel.chatPath} className="group lg:col-span-1">
            <Card className="h-full border-muted/60 bg-card/80 transition-all group-hover:-translate-y-0.5 group-hover:border-foreground/10 group-hover:bg-muted/30 group-hover:shadow-lg">
              <div className="flex h-full flex-col gap-5 px-6 py-5">
                <div className="flex items-center justify-between">
                  <span className="bg-muted text-foreground inline-flex h-10 w-10 items-center justify-center rounded-xl">
                    <MessageCircleMore className="h-5 w-5" />
                  </span>
                  <span className="text-muted-foreground text-xs">
                    {t("homeChatBadge")}
                  </span>
                </div>
                <div className="space-y-2">
                  <CardTitle className="text-lg">{t("chat")}</CardTitle>
                  <CardDescription>
                    {t("homeChatDescription")}
                  </CardDescription>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </section>

      <section className="space-y-4">
        <div className="space-y-1">
          <div className="text-muted-foreground text-xs font-semibold uppercase tracking-wide">
            {t("homeSectionToolsLabel")}
          </div>
          <h2 className="text-xl font-semibold">
            {t("homeSectionToolsTitle")}
          </h2>
        </div>
        <div className="space-y-6">
          {viewModel.toolSections.map((section) => (
            <ToolSectionBlock key={section.id} section={section} />
          ))}
        </div>
      </section>
    </div>
  );
};

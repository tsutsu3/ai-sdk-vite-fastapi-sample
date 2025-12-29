import { Link as LinkIcon, MessageCircleMore } from "lucide-react";

import { type NavMainItem, type NavToolGroup } from "@/shared/types/ui";

/**
 * Primary navigation for the app shell.
 *
 * These items power the sidebar's main section (chat route) and should align
 * with router paths in `frontend/src/app/router.tsx`.
 */
export const navMainItems: NavMainItem[] = [
  {
    id: "chat",
    url: "/chat",
    icon: MessageCircleMore,
  },
];

/**
 * Static link groups shown under tools in the sidebar.
 *
 * These are informational links and do not depend on authz.
 */
export const navLinkGroups: NavToolGroup[] = [
  {
    id: "aiDocs",
    url: "#",
    icon: LinkIcon,
    items: [
      {
        id: "promptSamples",
        url: "https://platform.openai.com/docs/examples",
      },
      {
        id: "generativeAIDocs",
        url: "https://platform.openai.com/docs/examples",
      },
      {
        id: "caseStudies",
        url: "https://platform.openai.com/docs/examples",
      },
    ],
  },
];

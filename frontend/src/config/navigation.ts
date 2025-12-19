import {
  Bot,
  Link as LinkIcon,
  MessageCircleMore,
  SquareTerminal,
} from "lucide-react";

import { type NavMainItem, type NavToolGroup } from "@/types/ui";

export const navMainItems: NavMainItem[] = [
  {
    id: "chat",
    url: "/chat",
    icon: MessageCircleMore,
  },
];

export const navToolGroups: NavToolGroup[] = [
  {
    id: "rag01",
    url: "#",
    icon: SquareTerminal,
    items: [
      {
        id: "rag0101",
        url: "/tools/rag0101",
      },
      {
        id: "rag0102",
        url: "/tools/rag0102",
      },
    ],
  },
  {
    id: "rag02",
    url: "#",
    icon: Bot,
    items: [
      {
        id: "rag0201",
        url: "/tools/rag0201",
      },
      {
        id: "rag0202",
        url: "/tools/rag0202",
      },
      {
        id: "rag0203",
        url: "/tools/rag0203",
      },
    ],
  },
];

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

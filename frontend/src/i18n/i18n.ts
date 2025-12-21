import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ja from "./locales/ja/translation.json";
import en from "./locales/en/translation.json";

const supportedLanguages = ["en", "ja"];

const resolveLanguage = (value: string | null | undefined) => {
  if (!value) {
    return "";
  }
  const normalized = value.toLowerCase();
  if (supportedLanguages.includes(normalized)) {
    return normalized;
  }
  const base = normalized.split("-")[0];
  return supportedLanguages.includes(base) ? base : "";
};

const detectBrowserLanguage = () => {
  if (typeof navigator === "undefined") {
    return "";
  }
  const candidates = Array.isArray(navigator.languages)
    ? navigator.languages
    : [navigator.language];
  for (const candidate of candidates) {
    const resolved = resolveLanguage(candidate);
    if (resolved) {
      return resolved;
    }
  }
  return "";
};

const storedLanguage =
  typeof window !== "undefined" ? resolveLanguage(localStorage.getItem("language")) : "";
const defaultLanguage = storedLanguage || detectBrowserLanguage() || "en";

i18n.use(initReactI18next).init({
  resources: {
    ja: { translation: ja },
    en: { translation: en },
  },
  lng: defaultLanguage,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;

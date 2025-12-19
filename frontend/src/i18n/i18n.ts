import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ja from "./locales/ja/translation.json";
import en from "./locales/en/translation.json";

const storedLanguage =
  typeof window !== "undefined"
    ? localStorage.getItem("language") ?? "en"
    : "en";

i18n.use(initReactI18next).init({
  resources: {
    ja: { translation: ja },
    en: { translation: en },
  },
  lng: storedLanguage,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;

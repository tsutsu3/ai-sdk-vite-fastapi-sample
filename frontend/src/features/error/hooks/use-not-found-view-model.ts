import { useTranslation } from "react-i18next";

export const useNotFoundViewModel = () => {
  const { t } = useTranslation();

  return {
    t,
  };
};

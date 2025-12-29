import * as React from "react";

/** Breakpoint used by layout to switch to mobile navigation. */
const MOBILE_BREAKPOINT = 768;

/**
 * Tracks viewport size against the mobile breakpoint.
 *
 * This hook supports responsive UI decisions without duplicating window
 * listeners across components.
 */
export const useIsMobile = () => {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(
    undefined,
  );

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };
    mql.addEventListener("change", onChange);
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return !!isMobile;
};

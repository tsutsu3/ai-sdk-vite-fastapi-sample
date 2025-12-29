import { useRef, useState } from "react";

export const useStateWithRef = <T,>(initial: T) => {
  const [state, setState] = useState(initial);
  const ref = useRef(state);

  const setStateWithRef = (
    value: T | ((previous: T) => T),
  ) => {
    const nextValue =
      typeof value === "function"
        ? (value as (previous: T) => T)(ref.current)
        : value;
    ref.current = nextValue;
    setState(nextValue);
  };

  return { state, setState: setStateWithRef, ref };
};

import { useCallback, useEffect, useRef } from "react";
import type { StickToBottomContext } from "use-stick-to-bottom";

type UseChatScrollControllerArgs = {
  hasMoreMessages: boolean;
  loadingOlderMessages: boolean;
  handleLoadOlderMessages: () => Promise<number>;
};

export const useChatScrollController = ({
  hasMoreMessages,
  loadingOlderMessages,
  handleLoadOlderMessages,
}: UseChatScrollControllerArgs) => {
  const scrollContextRef = useRef<StickToBottomContext | null>(null);
  const topSentinelRef = useRef<HTMLDivElement | null>(null);

  const setScrollContextRef = useCallback(
    (value: StickToBottomContext | null) => {
      scrollContextRef.current = value;
    },
    [],
  );
  const setTopSentinelRef = useCallback((value: HTMLDivElement | null) => {
    topSentinelRef.current = value;
  }, []);

  const handleLoadMore = useCallback(async () => {
    if (!hasMoreMessages || loadingOlderMessages) {
      return;
    }
    const scrollElement = scrollContextRef.current?.scrollRef.current;
    const previousScrollHeight = scrollElement?.scrollHeight ?? 0;
    const previousScrollTop = scrollElement?.scrollTop ?? 0;
    const added = await handleLoadOlderMessages();
    if (!added || !scrollElement) {
      return;
    }
    // Preserve the visible message after prepending older ones.
    requestAnimationFrame(() => {
      const nextScrollHeight = scrollElement.scrollHeight;
      scrollElement.scrollTop =
        previousScrollTop + (nextScrollHeight - previousScrollHeight);
    });
  }, [handleLoadOlderMessages, hasMoreMessages, loadingOlderMessages]);

  useEffect(() => {
    const scrollElement = scrollContextRef.current?.scrollRef.current;
    const sentinel = topSentinelRef.current;
    if (!scrollElement || !sentinel || !hasMoreMessages) {
      // Avoid observers when we cannot or should not load more.
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          handleLoadMore();
        }
      },
      {
        root: scrollElement,
        rootMargin: "200px 0px 0px 0px",
        threshold: 0,
      },
    );
    observer.observe(sentinel);
    return () => {
      observer.disconnect();
    };
  }, [handleLoadMore, hasMoreMessages]);

  return {
    setScrollContextRef,
    setTopSentinelRef,
  };
};

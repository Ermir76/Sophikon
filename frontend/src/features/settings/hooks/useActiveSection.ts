import { useEffect, useState } from "react";
import type { RefObject } from "react";

export function useActiveSection(
  refs: Record<string, RefObject<HTMLDivElement>>,
  sectionOrder: string[],
): string {
  const fallbackSection = sectionOrder[0] ?? "";
  const [activeSection, setActiveSection] = useState(fallbackSection);

  useEffect(() => {
    if (sectionOrder.length === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);

        if (visible.length === 0) {
          return;
        }

        const sectionId = visible[0].target.getAttribute("data-section-id");
        if (sectionId) {
          setActiveSection(sectionId);
        }
      },
      {
        threshold: [0.3, 0.6, 0.9],
        rootMargin: "-10% 0px -55% 0px",
      },
    );

    sectionOrder.forEach((sectionId) => {
      const element = refs[sectionId]?.current;
      if (element) {
        observer.observe(element);
      }
    });

    return () => {
      observer.disconnect();
    };
  }, [refs, sectionOrder]);

  if (!sectionOrder.includes(activeSection)) {
    return fallbackSection;
  }

  return activeSection;
}

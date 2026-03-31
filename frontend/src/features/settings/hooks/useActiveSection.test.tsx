import { act, renderHook } from "@testing-library/react";
import type { RefObject } from "react";

import { useActiveSection } from "./useActiveSection";

class MockIntersectionObserver {
  static instances: MockIntersectionObserver[] = [];

  readonly observe = vi.fn();
  readonly disconnect = vi.fn();

  constructor(
    public readonly callback: IntersectionObserverCallback,
    public readonly options?: IntersectionObserverInit,
  ) {
    MockIntersectionObserver.instances.push(this);
  }

  trigger(entries: IntersectionObserverEntry[]) {
    this.callback(entries, this as unknown as IntersectionObserver);
  }
}

function createSectionRef(sectionId: string): RefObject<HTMLDivElement> {
  const element = document.createElement("div");
  element.setAttribute("data-section-id", sectionId);

  return { current: element } as RefObject<HTMLDivElement>;
}

function createEntry(
  target: HTMLDivElement,
  isIntersecting: boolean,
  intersectionRatio: number,
): IntersectionObserverEntry {
  return {
    target,
    isIntersecting,
    intersectionRatio,
    boundingClientRect: target.getBoundingClientRect(),
    intersectionRect: target.getBoundingClientRect(),
    rootBounds: null,
    time: 0,
  } as IntersectionObserverEntry;
}

describe("useActiveSection", () => {
  beforeEach(() => {
    MockIntersectionObserver.instances = [];
    vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("defaults to the first section and observes each known ref", () => {
    const refs = {
      profile: createSectionRef("profile"),
      security: createSectionRef("security"),
    };

    const { result, unmount } = renderHook(() =>
      useActiveSection(refs, ["profile", "security"]),
    );

    expect(result.current).toBe("profile");
    expect(MockIntersectionObserver.instances).toHaveLength(1);
    expect(MockIntersectionObserver.instances[0]?.observe).toHaveBeenCalledTimes(2);
    expect(MockIntersectionObserver.instances[0]?.options).toMatchObject({
      threshold: [0.3, 0.6, 0.9],
      rootMargin: "-10% 0px -55% 0px",
    });

    unmount();

    expect(MockIntersectionObserver.instances[0]?.disconnect).toHaveBeenCalledTimes(1);
  });

  it("updates to the most visible intersecting section", () => {
    const refs = {
      profile: createSectionRef("profile"),
      security: createSectionRef("security"),
    };

    const { result } = renderHook(() =>
      useActiveSection(refs, ["profile", "security"]),
    );

    const observer = MockIntersectionObserver.instances[0];
    if (!observer) {
      throw new Error("Expected observer instance");
    }

    act(() => {
      observer.trigger([
        createEntry(refs.profile.current!, true, 0.35),
        createEntry(refs.security.current!, true, 0.8),
      ]);
    });

    expect(result.current).toBe("security");
  });

  it("falls back to the first section when the current active section is no longer in the order", () => {
    const refs = {
      profile: createSectionRef("profile"),
      security: createSectionRef("security"),
    };

    const { result, rerender } = renderHook(
      ({ sectionOrder }: { sectionOrder: string[] }) => useActiveSection(refs, sectionOrder),
      {
        initialProps: { sectionOrder: ["profile", "security"] },
      },
    );

    const observer = MockIntersectionObserver.instances[0];
    if (!observer) {
      throw new Error("Expected observer instance");
    }

    act(() => {
      observer.trigger([createEntry(refs.security.current!, true, 0.9)]);
    });

    expect(result.current).toBe("security");

    rerender({ sectionOrder: ["profile"] });

    expect(result.current).toBe("profile");
  });
});

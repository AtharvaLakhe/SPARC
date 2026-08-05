import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from 'react';

export interface ChapterRailChapter {
  /** The id of the section this chapter navigates to. */
  id: string;
  label: string;
}

export interface ChapterRailProps {
  chapters: readonly ChapterRailChapter[];
  ariaLabel?: string;
  className?: string;
  onActiveChapterChange?: (id: string) => void;
  /**
   * Override the element that scrolls. When omitted, the rail uses its nearest
   * `.sparc-panel`; outside the drawer it observes the browser viewport.
   */
  scrollContainer?: HTMLElement | null;
}

const ACTIVE_LINE = 0.34;

function reducedMotionIsPreferred(view: Window | null): boolean {
  return view?.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

function sectionElements(
  nav: HTMLElement,
  chapters: readonly ChapterRailChapter[],
  root: HTMLElement | null,
): HTMLElement[] {
  const document = nav.ownerDocument;
  return chapters.flatMap(({ id }) => {
    const section = document.getElementById(id);
    if (!section || (root && !root.contains(section))) return [];
    return [section];
  });
}

function viewportIsAtEnd(view: Window): boolean {
  const document = view.document.documentElement;
  return view.scrollY + view.innerHeight >= document.scrollHeight - 2;
}

/**
 * A semantic, keyboard-operable chapter navigator for the long analysis panel.
 * It owns navigation state only; layout and presentation stay with the caller.
 */
export function ChapterRail({
  chapters,
  ariaLabel = 'Analysis chapters',
  className,
  onActiveChapterChange,
  scrollContainer,
}: ChapterRailProps) {
  const navRef = useRef<HTMLElement>(null);
  const linkRefs = useRef(new Map<string, HTMLAnchorElement>());
  const [activeId, setActiveId] = useState(chapters[0]?.id ?? '');

  useEffect(() => {
    if (chapters.some(({ id }) => id === activeId)) return;
    setActiveId(chapters[0]?.id ?? '');
  }, [activeId, chapters]);

  useEffect(() => {
    if (activeId) onActiveChapterChange?.(activeId);
  }, [activeId, onActiveChapterChange]);

  useEffect(() => {
    const nav = navRef.current;
    if (!nav || chapters.length === 0) return;

    const view = nav.ownerDocument.defaultView;
    if (!view) return;

    const root = scrollContainer ?? nav.closest<HTMLElement>('.sparc-panel');
    const sections = sectionElements(nav, chapters, root);
    if (sections.length === 0) return;

    sections.forEach((section) => section.classList.add('chapter-section'));

    const updateActiveSection = () => {
      const rootRect = root?.getBoundingClientRect();
      const rootTop = rootRect?.top ?? 0;
      const rootHeight = rootRect?.height ?? view.innerHeight;
      const activeLine = rootTop + rootHeight * ACTIVE_LINE;
      const atEnd = root
        ? root.scrollTop + root.clientHeight >= root.scrollHeight - 2
        : viewportIsAtEnd(view);

      let candidate = sections[0];
      for (const section of sections) {
        if (section.getBoundingClientRect().top > activeLine) break;
        candidate = section;
      }
      if (atEnd) candidate = sections.at(-1);

      if (candidate) {
        setActiveId((current) => current === candidate.id ? current : candidate.id);
      }
    };

    updateActiveSection();

    let observer: IntersectionObserver | null = null;
    let animationFrame = 0;
    const scheduleUpdate = () => {
      if (animationFrame) return;
      animationFrame = view.requestAnimationFrame(() => {
        animationFrame = 0;
        updateActiveSection();
      });
    };

    if (typeof view.IntersectionObserver === 'function') {
      observer = new view.IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('chapter-section--visible');
        });
        updateActiveSection();
      }, {
        root,
        /* A narrow reading band below the sticky mission header. */
        rootMargin: '-30% 0px -64% 0px',
        threshold: [0, 0.01, 1],
      });
      sections.forEach((section) => observer?.observe(section));
    } else {
      /* Old/test browsers still get accurate tracking without blocking links. */
      sections.forEach((section) => section.classList.add('chapter-section--visible'));
    }
    /* Observe visibility and also follow the scroll position directly. The
       latter matters for long sections that can remain intersecting while the
       reading line crosses from one chapter into the next. */
    (root ?? view).addEventListener('scroll', scheduleUpdate, { passive: true });
    view.addEventListener('resize', scheduleUpdate, { passive: true });

    return () => {
      observer?.disconnect();
      (root ?? view).removeEventListener('scroll', scheduleUpdate);
      view.removeEventListener('resize', scheduleUpdate);
      if (animationFrame) view.cancelAnimationFrame(animationFrame);
      sections.forEach((section) => {
        section.classList.remove('chapter-section', 'chapter-section--visible');
      });
    };
  }, [chapters, scrollContainer]);

  const scrollToChapter = (id: string) => {
    const nav = navRef.current;
    const section = nav?.ownerDocument.getElementById(id);
    if (!nav || !section) return;

    const root = scrollContainer ?? nav.closest<HTMLElement>('.sparc-panel');
    if (root && !root.contains(section)) return;

    section.scrollIntoView({
      behavior: reducedMotionIsPreferred(nav.ownerDocument.defaultView) ? 'auto' : 'smooth',
      block: 'start',
    });
    setActiveId(id);
  };

  const navigateByKey = (event: KeyboardEvent<HTMLElement>) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;

    const key = event.key.toLowerCase();
    const direction = key === 'arrowdown' || key === 'j'
      ? 1
      : key === 'arrowup' || key === 'k'
        ? -1
        : 0;
    if (!direction) return;

    const focusedId = (event.target as HTMLElement)
      .closest<HTMLAnchorElement>('[data-chapter-id]')
      ?.dataset.chapterId;
    const currentIndex = Math.max(0, chapters.findIndex(({ id }) => id === (focusedId ?? activeId)));
    const nextIndex = Math.min(chapters.length - 1, Math.max(0, currentIndex + direction));
    const next = chapters[nextIndex];
    if (!next || nextIndex === currentIndex) return;

    event.preventDefault();
    linkRefs.current.get(next.id)?.focus({ preventScroll: true });
    scrollToChapter(next.id);
  };

  if (chapters.length === 0) return null;

  const classes = ['chapter-rail', className].filter(Boolean).join(' ');

  return (
    <nav
      ref={navRef}
      className={classes}
      aria-label={ariaLabel}
      onKeyDown={navigateByKey}
      style={{ '--chapter-count': chapters.length } as CSSProperties}
    >
      <ol className="chapter-rail__list">
        {chapters.map((chapter, index) => {
          const isActive = chapter.id === activeId;
          return (
            <li key={chapter.id} className="chapter-rail__item">
              <a
                ref={(link) => {
                  if (link) linkRefs.current.set(chapter.id, link);
                  else linkRefs.current.delete(chapter.id);
                }}
                className={`chapter-rail__link${isActive ? ' chapter-rail__link--active' : ''}`}
                href={`#${chapter.id}`}
                data-chapter-id={chapter.id}
                aria-current={isActive ? 'location' : undefined}
                onClick={(event) => {
                  event.preventDefault();
                  scrollToChapter(chapter.id);
                }}
              >
                <span className="chapter-rail__index" aria-hidden="true">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <span className="chapter-rail__label">{chapter.label}</span>
              </a>
            </li>
          );
        })}
      </ol>
      <p className="chapter-rail__hint" aria-hidden="true">
        <kbd>J</kbd><kbd>K</kbd><span>navigate</span>
      </p>
    </nav>
  );
}

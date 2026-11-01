/* eslint-disable */
// Delivered by Originkit · stack: nextjs · styling: tailwind
"use client";

import {
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

/** Sizing has to happen before the first paint, otherwise the frame shows at
 *  1× for a frame or two and then snaps to its real scale. React can't do that
 *  during SSR, so this runs inline right after the markup — the browser applies
 *  it while still parsing, and the effect below only keeps it in sync. */
const inlineScale = (id: string, frameWidth: number) =>
  `(function(){var o=document.getElementById(${JSON.stringify(id)});if(!o)return;` +
  `var i=o.firstElementChild;if(!i)return;var w=o.clientWidth;if(!w)return;` +
  `var s=w/${frameWidth};i.style.transform='scale('+s+')';` +
  `i.style.setProperty('--frame-scale',String(s));` +
  `o.style.height=(i.offsetHeight*s)+'px';})()`;

const useIsomorphicLayoutEffect =
  typeof window === "undefined" ? useEffect : useLayoutEffect;

/** Renders a fixed-width design frame and scales it to the available width.
 *
 *  CSS can't express this on its own — `zoom` and `transform: scale()` both
 *  need a unitless number, and calc() can't divide a vw by a px — so the
 *  factor is measured. Everything inside stays at its exact Figma pixel
 *  value; only the frame is scaled, so line breaks and proportions can't
 *  drift the way per-property clamps let them.
 */
export const ScaleFrame = ({
  frameWidth,
  className,
  children,
}: {
  frameWidth: number;
  className?: string;
  children: ReactNode;
}) => {
  const outerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  /** devicePixelRatio as it was before the user zoomed anything */
  const baseDprRef = useRef<number | null>(null);
  const id = useId();
  const [measured, setMeasured] = useState(false);

  useIsomorphicLayoutEffect(() => {
    const outer = outerRef.current;
    const inner = innerRef.current;
    if (!outer || !inner) return;

    const measure = () => {
      const width = outer.clientWidth;
      if (!width) return;

      // Ctrl +/− works by shrinking the CSS viewport, which is the same signal
      // this component scales from — so without compensation the frame scales
      // down by exactly the amount you zoomed in and nothing appears to change.
      // devicePixelRatio moves with zoom by the same factor, so measuring it
      // against its value on mount recovers the zoom level and cancels the
      // cancellation. Baseline is captured once: a page loaded at 150% starts
      // fit-to-width as before, and zooming from there behaves normally.
      if (baseDprRef.current === null) {
        baseDprRef.current = window.devicePixelRatio || 1;
      }
      const zoom = (window.devicePixelRatio || 1) / baseDprRef.current;

      const scale = (width / frameWidth) * zoom;
      inner.style.transform = `scale(${scale})`;
      // published so a child can opt out of the scaling (see the tablet header
      // in sec3, which counter-scales to keep its native height)
      inner.style.setProperty("--frame-scale", String(scale));
      outer.style.height = `${inner.offsetHeight * scale}px`;

      // Zoomed in, the frame is now wider than its container — the sections clip
      // overflow, so without this the extra would simply be cropped off with no
      // way to reach it. Zoomed out it is narrower, so centre it rather than
      // leaving the gap on one side. Both are no-ops at 100%.
      const scaledWidth = frameWidth * scale;
      outer.style.overflowX = scaledWidth > width + 1 ? "auto" : "";
      inner.style.marginLeft =
        scaledWidth < width - 1 ? `${(width - scaledWidth) / 2}px` : "";

      setMeasured(true);
    };

    const observer = new ResizeObserver(measure);
    observer.observe(outer);
    observer.observe(inner);
    measure();

    // Zoom usually changes the viewport width too, so the observer covers it —
    // but not when the frame's box is pinned by something else, so watch the
    // pixel ratio directly as well.
    const dprWatch = window.matchMedia(
      `(resolution: ${window.devicePixelRatio || 1}dppx)`,
    );
    dprWatch.addEventListener("change", measure);

    return () => {
      observer.disconnect();
      dprWatch.removeEventListener("change", measure);
    };
  }, [frameWidth]);

  return (
    <>
      {/* the inline script below writes height/transform before hydration, so
          the server markup deliberately differs from the client's */}
      <div ref={outerRef} id={id} className={className} suppressHydrationWarning>
        <div
          ref={innerRef}
          suppressHydrationWarning
          style={
            {
              width: frameWidth,
              transformOrigin: "top left",
              "--frame-scale": 1,
            } as React.CSSProperties
          }
        >
          {children}
        </div>
      </div>
      {!measured && (
        <script dangerouslySetInnerHTML={{ __html: inlineScale(id, frameWidth) }} />
      )}
    </>
  );
};

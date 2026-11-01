/* eslint-disable */
// Delivered by Originkit · stack: nextjs · styling: tailwind
"use client";

import { useEffect, useState } from "react";
import Globe from "@/components/originkit/ui/hero-24/globe";

const ACCENT = "#00A1DB";

/** Section 2's globe: Figma panel values (dots #00A1DB · 5 · 8, outline and
 *  grid #00A1DB, ocean #101216, stop on hover, lat 23 / lng -23). Scale is
 *  9.7 rather than the panel's 8 so the sphere fills its 323px frame the way
 *  the design shows it. */
export const MediaGlobe = ({ query }: { query: string }) => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia(query);
    const update = () => setMatches(mql.matches);
    update();
    mql.addEventListener("change", update);
    return () => mql.removeEventListener("change", update);
  }, [query]);

  if (!matches) return null;

  return (
    <Globe
      scale={9.7}
      stopOnHover
      initialLatitude={23}
      initialLongitude={-23}
      fill="dots"
      dots={{ color: ACCENT, size: 5, density: 8, allDots: false }}
      showOutline
      outlineColor={ACCENT}
      showGrid
      graticuleColor={ACCENT}
      oceanColor="#101216"
      style={{ width: "100%", height: "100%" }}
    />
  );
};

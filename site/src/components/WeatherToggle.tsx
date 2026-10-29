import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import type { Img } from "../lib/img";

// Glow per mode, in the order the content lists them: cold, hot, fog
const GLOW = ["var(--color-glow-blue)", "var(--color-glow-red)", "var(--color-copper)"];

/** Monarch "weather eye": switch between warning modes; the render crossfades and the frame glows in the mode colour. */
export default function WeatherToggle({ images }: { images: Img[] }) {
  const [active, setActive] = useState(0);
  const im = images[active];
  return (
    <div>
      <div
        className="relative mx-auto max-w-md overflow-hidden transition-shadow duration-700"
        style={{ aspectRatio: `${im.width} / ${im.height}`, boxShadow: `0 0 80px -10px ${GLOW[active % GLOW.length]}` }}
      >
        <AnimatePresence initial={false}>
          <motion.img
            key={active}
            src={im.src}
            srcSet={im.srcSet}
            sizes="(min-width: 768px) 28rem, 100vw"
            alt={im.alt}
            width={im.width}
            height={im.height}
            className="absolute inset-0 h-full w-full object-cover"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          />
        </AnimatePresence>
      </div>
      <div role="group" aria-label="Warning mode" className="mt-6 flex justify-center gap-2">
        {images.map((m, i) => (
          <button
            key={i}
            type="button"
            aria-pressed={i === active}
            onClick={() => setActive(i)}
            className="display border border-paper/30 px-4 py-2 text-[0.6rem] aria-pressed:border-paper aria-pressed:bg-paper aria-pressed:text-ink"
          >
            {m.label ?? i + 1}
          </button>
        ))}
      </div>
    </div>
  );
}

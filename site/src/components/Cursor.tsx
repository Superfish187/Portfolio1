import { useEffect, useState } from "react";
import { motion, useMotionValue, useSpring } from "motion/react";

/**
 * Smooth-follow cursor (Cursify pattern). Shows the `data-cursor` label of the hovered element,
 * e.g. "Prev" / "Next" over carousel halves. Fine pointers only; touch devices never render it.
 */
export default function Cursor() {
  const [enabled] = useState(() => matchMedia("(pointer: fine)").matches);
  const [label, setLabel] = useState("");
  const x = useMotionValue(-100);
  const y = useMotionValue(-100);
  const spring = { stiffness: 500, damping: 40, mass: 0.4 };
  const sx = useSpring(x, spring);
  const sy = useSpring(y, spring);

  useEffect(() => {
    if (!enabled) return;
    const move = (e: PointerEvent) => {
      x.set(e.clientX);
      y.set(e.clientY);
      const t = (e.target as Element | null)?.closest?.("[data-cursor]");
      setLabel(t?.getAttribute("data-cursor") ?? "");
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, [enabled]);

  if (!enabled) return null;
  return (
    <motion.div
      aria-hidden
      className="pointer-events-none fixed top-0 left-0 z-50 mix-blend-difference"
      style={{ x: sx, y: sy }}
    >
      <motion.div
        className="flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-paper text-[0.6rem] tracking-[0.3em] text-ink uppercase"
        animate={label ? { width: 72, height: 72 } : { width: 8, height: 8 }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
      >
        {label && <span className="pl-[0.3em]">{label}</span>}
      </motion.div>
    </motion.div>
  );
}

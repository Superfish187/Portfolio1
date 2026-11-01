import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";
import { ScrambleTextPlugin } from "gsap/ScrambleTextPlugin";
import { CustomEase } from "gsap/CustomEase";
import Lenis from "lenis";

gsap.registerPlugin(ScrollTrigger, SplitText, ScrambleTextPlugin, CustomEase);

// Same curves as --ease-out / --ease-in-out in global.css
CustomEase.create("out", ".22,1,.36,1");
CustomEase.create("inOut", ".65,0,.35,1");
gsap.defaults({ ease: "out", duration: 0.6 });

const OK = "(prefers-reduced-motion: no-preference)";
const DESKTOP = "(min-width: 768px)";

let lenis: Lenis | undefined;
let mm: gsap.MatchMedia | undefined;

function startLenis() {
  if (lenis || !matchMedia(OK).matches) return;
  // Touch keeps native scrolling (Lenis default syncTouch: false)
  lenis = new Lenis({ autoRaf: false });
  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add((t) => lenis!.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);
}

// 97%: anything already visible at load (e.g. a project summary near the fold) still reveals without scrolling
const onceIn = (el: Element) => ({ trigger: el, start: "top 97%", once: true });

/** Wires every data-* motion hook on the current page. Re-run after each Astro page swap. */
function initPage() {
  lenis?.resize();
  mm = gsap.matchMedia();

  mm.add(OK, () => {
    gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el) =>
      gsap.fromTo(el, { opacity: 0, y: 40 }, { opacity: 1, y: 0, scrollTrigger: onceIn(el) }),
    );

    gsap.utils.toArray<HTMLElement>("[data-split]").forEach((el) => {
      gsap.set(el, { opacity: 1 });
      if (el.dataset.split === "scramble") {
        const text = el.textContent ?? "";
        gsap.to(el, { duration: 1.2, scrambleText: { text, chars: "upperCase", speed: 0.6 }, scrollTrigger: onceIn(el) });
        return;
      }
      SplitText.create(el, {
        type: "chars",
        mask: "chars",
        autoSplit: true,
        onSplit: (s) =>
          gsap.from(s.chars, { yPercent: 110, duration: 1, stagger: 0.035, scrollTrigger: onceIn(el) }),
      });
    });

    // Diagonal wipe in the direction of the portfolio's 60° slices
    gsap.utils.toArray<HTMLElement>("[data-wipe]").forEach((el) =>
      gsap.fromTo(
        el,
        { opacity: 1, clipPath: "polygon(0% 0%, 0% 0%, -25% 100%, -25% 100%)" },
        { clipPath: "polygon(0% 0%, 125% 0%, 100% 100%, -25% 100%)", duration: 1.1, ease: "inOut", scrollTrigger: onceIn(el) },
      ),
    );

    gsap.utils.toArray<HTMLElement>("[data-parallax]").forEach((el) =>
      gsap.fromTo(
        el,
        { yPercent: -Number(el.dataset.parallax || 8) },
        { yPercent: Number(el.dataset.parallax || 8), ease: "none", scrollTrigger: { trigger: el.parentElement, scrub: true } },
      ),
    );
  });

  // Pinned horizontal strip; phones and reduced motion keep the native horizontal scroller
  mm.add(`${OK} and ${DESKTOP}`, () => {
    const strips = gsap.utils.toArray<HTMLElement>("[data-pin-strip]");
    strips.forEach((section) => {
      const track = section.querySelector<HTMLElement>("[data-track]")!;
      // Markup default is a native horizontal scroller; switch it to a translated track while pinned
      Object.assign(track.style, { overflow: "visible", width: "max-content" });
      section.style.overflow = "hidden";
      const distance = () => track.scrollWidth - section.clientWidth;
      gsap.to(track, {
        x: () => -distance(),
        ease: "none",
        scrollTrigger: { trigger: section, pin: true, scrub: 0.6, end: () => `+=${distance()}`, invalidateOnRefresh: true },
      });
    });
    return () =>
      strips.forEach((section) => {
        const track = section.querySelector<HTMLElement>("[data-track]")!;
        section.style.overflow = track.style.overflow = track.style.width = "";
      });
  });
}

startLenis();
document.addEventListener("astro:page-load", initPage);
document.addEventListener("astro:before-swap", () => mm?.revert());

import { getImage } from "astro:assets";

export type Img = { src: string; srcSet: string; alt: string; width: number; height: number; label?: string };

/** Optimised webp + srcset, in a plain shape React islands can take as props. */
export async function toImg(pic: { src: ImageMetadata; alt: string; label?: string }): Promise<Img> {
  const widths = [640, 1024, 1600, 2400].filter((w) => w <= pic.src.width);
  const r = await getImage({ src: pic.src, widths, format: "webp" });
  return { src: r.src, srcSet: r.srcSet.attribute, alt: pic.alt, width: pic.src.width, height: pic.src.height, label: pic.label };
}

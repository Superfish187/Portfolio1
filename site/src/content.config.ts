import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const projects = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/projects" }),
  schema: ({ image }) => {
    // focus: CSS object-position for tiles that crop the image (default centre)
    const pic = z.object({ src: image(), alt: z.string(), label: z.string().optional(), focus: z.string().optional() });
    return z.object({
      number: z.string(),
      title: z.string(),
      brand: z.string(),
      semester: z.string(),
      partner: z.string().optional(),
      // Work page caption, e.g. "Interior Package, Exterior, Rendering"
      scope: z.string(),
      summary: z.string(),
      cover: pic,
      // The three images shown in this project's row on the Work page
      tiles: z.array(pic).length(3),
      sections: z.array(
        z.object({
          heading: z.string(),
          body: z.string().optional(),
          // full: stacked wide images · grid: 3-up tiles · strip: pinned horizontal process
          // carousel: one at a time, click/swipe · weather: Monarch mode toggle
          // moodboard: two 3-up blocks side by side, first half of the images left, second half right
          layout: z.enum(["full", "grid", "strip", "carousel", "weather", "moodboard"]).default("full"),
          images: z.array(pic),
          // Optional video under the images (src is a public/ path)
          video: z.object({ src: z.string(), poster: image() }).optional(),
        }),
      ),
    });
  },
});

export const collections = { projects };

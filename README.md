# Julius Nossoll Testorf: Portfolio

Transportation interior design portfolio website, plus the source material behind it.

| Folder / file | What it is |
|---|---|
| `site/` | The website (Astro + React islands, Tailwind, GSAP, Lenis). |
| `blender/` | Liquid-chrome hero loop scenes (matte + mirror) and render/encode instructions; see `blender/README.md`. |
| `Bilder/` | Original project images, named by where they appear on the site. |
| `Julius_Portfolio_Shotbook.xlsx` | Image placement plan. |
| `Portfolio Julius Nossoll Testorf.pdf` | The original paper portfolio. |

## Run locally

Needs Node 22.12 or newer.

```bash
cd site
npm install
npm run dev
```

The site runs at http://localhost:4321. To run the tests (Playwright):

```bash
cd site
npx playwright install
npm test
```

## Deploy

Netlify builds automatically from this repository: `netlify.toml` points it at `site/` (build `npm run build`, publish `dist`). No extra settings are needed when connecting the repo.

## Not in the repository

`Bilder/MAN Vyra/Video1.mp4` (269 MB) and `Bilder/Geely Skywalker/Skywalker 2.0.mp4` (293 MB) are over GitHub's 100 MB file limit. The site uses the compressed copies in `site/public/video/`.

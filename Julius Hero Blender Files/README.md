# Hero loop: liquid chrome (Blender)

The fullscreen video on the portfolio home page. There are two finishes:

| File | Look |
|---|---|
| `hero-matte.blend` | Satin chrome with soft-edged highlights. This is the site default. |
| `hero-mirror.blend` | Polished chrome with a clear coat for crisp white "wet" reflections. Shown with `?hero=mirror`. |

Previews of frame 0 for both finishes are in `previews/`.

Both scenes are the same apart from the finish:

- **Engine:** Cycles.
- **Loop:** 12 seconds, frames 0–359 at 30 fps. It loops seamlessly, so don't render frame 360.
- **Camera and lights:** locked. Only the liquid moves.
- **Surface:** a Geometry Nodes grid with about 9.6M vertices and three looping noise layers: swells, ripples and micro-ripples.
- **Studio:** camera-invisible softboxes, a ring light and a horizon ring. Blender's studio HDRI is packed into the file, so nothing is missing on another machine.

Blender 5.2 was used to build the files.

## Render

### Production master (as saved: 3840×2160, 512 samples, motion blur, 16-bit PNG)

Open the `.blend` file and use **Render → Render Animation**. Frames are written to `render/<finish>/f0000.png … f0359.png` next to the file.

From a terminal:

```bash
blender -b hero-matte.blend -a
```

```bash
blender -b hero-mirror.blend -a
```

### Faster web loop (1920×1080, 32 samples, 2.4M-vertex mesh, no motion blur)

This rebuilds the scene from `hero.py` and renders it without saving a `.blend`:

```bash
blender -b -P hero.py -- --finish matte --web --frames render/matte-web/
```

### Render time

These timings were measured on an Apple M5 in Cycles with the Metal GPU:

| Settings | Time per frame | Time for 360 frames |
|---|---|---|
| 1080p, 48 samples, with motion blur | about 26 s | about 2.6 h |
| Production 4K | not measured, many times slower | budget accordingly |

Before committing to a full run, render a single frame first:

```bash
blender -b hero-matte.blend -f 0
```

### GPU

The script selects Metal. On NVIDIA, change the device in Preferences → System → Cycles Render Devices (OptiX or CUDA) and keep Render Properties → Device set to GPU.

## Encode for the website

Run these commands from inside a frames folder. They scale 4K masters down to 1080p; for 1080p frames, drop the `-vf` option. Replace `matte` with `mirror` for the other finish.

```bash
ffmpeg -framerate 30 -i f%04d.png -vf scale=1920:-2:flags=lanczos -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -movflags +faststart -an hero-matte.mp4
```

```bash
ffmpeg -framerate 30 -i f%04d.png -vf scale=1920:-2:flags=lanczos -c:v libvpx-vp9 -crf 34 -b:v 0 -row-mt 1 -pix_fmt yuv420p -an hero-matte.webm
```

```bash
ffmpeg -i f0000.png -vf scale=1920:-2 -q:v 2 poster-matte.jpg
```

Aim for about 4 MB or less per MP4. Raise `-crf` if a file comes out bigger.

## Put the files in the site

| File | Goes to |
|---|---|
| `hero-matte.mp4`, `hero-matte.webm`, `hero-mirror.mp4`, `hero-mirror.webm` | `site/public/video/` |
| `poster-matte.jpg`, `poster-mirror.jpg` | `site/src/assets/hero/` (overwrite) |

The page picks the videos up automatically. Until both MP4 files are present, it shows only the posters.

## Check caption contrast

Do this before shipping. The white caption sits on the video behind a dark scrim, and `check_contrast.py` checks every frame against WCAG AA, which requires 4.5:1. It needs Python 3 with numpy and Pillow.

```bash
python3 check_contrast.py 1440 900 551 439 337 23 "render/matte/*.png"
```

```bash
python3 check_contrast.py 375 812 20 424 335 45 "render/matte/*.png"
```

These two commands check desktop and phone sizes. Repeat them for `mirror`.

Frame 0 currently measures 9.9:1 on desktop and 5.4:1 on phones. If a full loop fails, strengthen the scrim in `site/src/pages/index.astro` and update the matching numbers in `check_contrast.py`.

## Change the look

Everything is built in `hero.py`; the `.blend` files are generated from it. Edit the script, then re-save both files:

```bash
blender -b -P hero.py -- --finish matte --save
```

```bash
blender -b -P hero.py -- --finish mirror --save
```

To render a single frame, use `-- --still 0 out.png` for a full render or `-- --still 0 out.png --half --fast` for a quick preview.

| What | Where in `hero.py` |
|---|---|
| Material per finish | `LOOK` |
| Liquid motion | `layer(...)`: `radius` is how far a layer travels per loop, and `cycles` must stay a whole number to keep the loop seamless. |
| Studio lights | the `softbox(...)` calls |

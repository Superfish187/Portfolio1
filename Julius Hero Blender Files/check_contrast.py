"""Worst-case WCAG contrast of the home-page caption over every frame of a hero loop.

Applies the same scrim as site/src/pages/index.astro (keep the numbers in sync), ignores the text-shadow
(conservative), and assumes 1920x1080 frames shown with object-fit: cover.

  python3 check_contrast.py <viewport_w> <viewport_h> <box_x> <box_y> <box_w> <box_h> "<frames glob>"
  # desktop:  python3 check_contrast.py 1440 900 551 439 337 23 "render/matte/*.png"
  # phone:    python3 check_contrast.py 375 812 20 424 335 45 "render/matte/*.png"

Box = the caption's bounding rect in CSS px at that viewport. Needs numpy + Pillow. Pass = 4.5:1 or more.
"""
import glob, sys, numpy as np
from PIL import Image
VW, VH = int(sys.argv[1]), int(sys.argv[2])
bx, by, bw, bh = map(int, sys.argv[3:7])
scrim_stops = [(0, .9), (.70, .45), (1.0, 0)]  # inner ellipse, must match index.astro
s = max(VW / 1920, VH / 1080); ox = (VW - 1920 * s) / 2; oy = (VH - 1080 * s) / 2
xs, ys = np.meshgrid(np.arange(bx, bx + bw), np.arange(by, by + bh))
d = np.sqrt(((xs - VW / 2) / max(.42 * VW, 260)) ** 2 + ((ys - VH / 2) / max(.30 * VH, 170)) ** 2)
alpha = 1 - (1 - .2) * (1 - np.interp(d, [p for p, _ in scrim_stops], [a for _, a in scrim_stops]))  # over the 20% base tint
vx = ((xs - ox) / s).astype(int).clip(0, 1919); vy = ((ys - oy) / s).astype(int).clip(0, 1079)
lin = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
scrim = np.array([20, 21, 24]) / 255
worst = []
for f in sorted(glob.glob(sys.argv[7])):
    img = Image.open(f).convert('RGB').resize((1920, 1080))
    px = np.asarray(img, dtype=float)[vy, vx] / 255
    comp = px * (1 - alpha[..., None]) + scrim * alpha[..., None]
    L = (lin(comp) @ np.array([.2126, .7152, .0722]))
    worst.append(np.percentile(L, 99))
Lbg = max(worst); Ltext = .96 ** 3
print(f"viewport {VW}x{VH}: worst 99th-pct background luminance {Lbg:.3f} -> contrast {(Ltext + .05) / (Lbg + .05):.2f}:1 (need 4.5)")

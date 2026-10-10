"""Generate a deterministic 336x336 PNG test image (red circle, blue square on white) for Phase 0 step 0.4."""
import sys
from PIL import Image, ImageDraw

out = sys.argv[1]
img = Image.new("RGB", (336, 336), "white")
d = ImageDraw.Draw(img)
d.ellipse((30, 30, 150, 150), fill="red")
d.rectangle((190, 190, 306, 306), fill="blue")
img.save(out)
print(out, img.size)

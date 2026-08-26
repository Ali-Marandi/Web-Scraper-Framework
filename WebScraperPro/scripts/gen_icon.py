from PIL import Image, ImageDraw, ImageFont
import os, math, struct

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons")

def create_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    margin = max(1, int(size * 0.05))
    r = size // 2 - margin

    # Background circle
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(47, 129, 247, 255))
    r2 = int(r * 0.82)
    draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], fill=(31, 111, 235, 255))

    # Web radial lines
    web_color = (255, 255, 255, 200)
    for angle_deg in range(0, 360, 60):
        angle = math.radians(angle_deg)
        x_end = cx + int(r2 * 0.75 * math.cos(angle))
        y_end = cy + int(r2 * 0.75 * math.sin(angle))
        lw = max(1, size // 48)
        draw.line([(cx, cy), (x_end, y_end)], fill=web_color, width=lw)

    # Concentric hexagons
    for frac in [0.3, 0.55, 0.75]:
        pts = []
        for ad in range(0, 360, 60):
            a = math.radians(ad)
            pts.append((cx + int(r2*frac*math.cos(a)), cy + int(r2*frac*math.sin(a))))
        pts.append(pts[0])
        lw = max(1, size // 64)
        draw.line(pts, fill=web_color, width=lw)

    # Magnifying glass
    gcx, gcy = cx + int(r2*0.3), cy - int(r2*0.3)
    gr = int(r2 * 0.22)
    lw = max(2, size // 28)
    draw.ellipse([gcx-gr, gcy-gr, gcx+gr, gcy+gr], outline=(255,255,255,255), width=lw)
    ha = math.radians(45)
    draw.line([(gcx+int(gr*0.7*math.cos(ha)), gcy+int(gr*0.7*math.sin(ha))),
               (gcx+int(gr*1.3*math.cos(ha)), gcy+int(gr*1.3*math.sin(ha)))],
              fill=(255,255,255,255), width=lw)

    # W letter
    try:
        fs = int(size * 0.22)
        font = ImageFont.truetype("/usr/share/fonts/truetype/english/Tinos-Bold.ttf", fs)
    except:
        font = ImageFont.load_default()
    text = "W"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text((cx - tw//2, cy + int(r2*0.15) - th//2), text, fill=(255,255,255,255), font=font)

    return img


def save_proper_ico(images, path):
    """Save a proper multi-resolution ICO file manually."""
    png_data_list = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_data_list.append(buf.getvalue())

    # ICO header: reserved(2) + type(2) + count(2)
    count = len(images)
    header_size = 6
    # Each entry: 16 bytes
    entry_size = 16
    dir_size = entry_size * count
    data_offset = header_size + dir_size

    with open(path, "wb") as f:
        # Header
        f.write(struct.pack("<HHH", 0, 1, count))

        # Directory entries
        for i, (img, png_data) in enumerate(zip(images, png_data_list)):
            w = img.width if img.width < 256 else 0
            h = img.height if img.height < 256 else 0
            f.write(struct.pack("<BBBBHHII",
                w, h,  # width, height (0 = 256)
                0,     # color palette
                0,     # reserved
                1,     # color planes
                32,    # bits per pixel
                len(png_data),  # image data size
                data_offset + sum(len(d) for d in png_data_list[:i]),  # offset
            ))

        # Image data
        for png_data in png_data_list:
            f.write(png_data)


import io

def main():
    png = create_icon(256)
    png_path = os.path.join(OUT_DIR, "app.png")
    png.save(png_path, "PNG")
    print(f"Saved PNG: {png_path} ({png.size})")

    sizes = [16, 32, 48, 64, 128, 256]
    icons = [create_icon(s) for s in sizes]
    ico_path = os.path.join(OUT_DIR, "app.ico")
    save_proper_ico(icons, ico_path)
    fsize = os.path.getsize(ico_path)
    print(f"Saved ICO: {ico_path} ({sizes}) - {fsize} bytes")


if __name__ == "__main__":
    main()

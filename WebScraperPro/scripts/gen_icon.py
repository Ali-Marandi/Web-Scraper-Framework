from PIL import Image, ImageDraw
import os

def create_icon():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = max(1, size // 16)
        radius = size // 3
        cx, cy = size // 2, size // 2
        for i in range(radius, 0, -1):
            ratio = i / radius
            r = int(47 * ratio + 20 * (1 - ratio))
            g = int(129 * ratio + 60 * (1 - ratio))
            b = int(247 * ratio + 180 * (1 - ratio))
            draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(r, g, b, 255))
        grid_color = (255, 255, 255, 50)
        step = max(2, size // 8)
        for x in range(margin + step, size - margin, step):
            draw.line([(x, cy - radius // 2), (x, cy + radius // 2)], fill=grid_color, width=1)
        for y in range(margin + step, size - margin, step):
            draw.line([(cx - radius // 2, y), (cx + radius // 2, y)], fill=grid_color, width=1)
        arrow_color = (255, 255, 255, 240)
        aw = max(2, size // 6)
        ah = max(4, size // 3)
        lw = max(1, size // 16)
        draw.line([(cx, cy - ah // 2), (cx, cy + ah // 2 - aw)], fill=arrow_color, width=lw)
        draw.polygon([(cx, cy + ah // 2), (cx - aw, cy + ah // 2 - aw), (cx + aw, cy + ah // 2 - aw)], fill=arrow_color)
        dot_r = max(1, size // 16)
        draw.ellipse([cx - dot_r, cy - ah // 2 - dot_r * 2, cx + dot_r, cy - ah // 2], fill=arrow_color)
        images.append(img)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'icons')
    os.makedirs(out, exist_ok=True)
    ico = os.path.join(out, 'app.ico')
    images[0].save(ico, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f'Saved: {ico}')
    png = os.path.join(out, 'app.png')
    images[-1].save(png, format='PNG')
    print(f'Saved: {png}')

if __name__ == '__main__':
    create_icon()

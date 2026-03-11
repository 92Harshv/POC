"""
Generates a simple .ico file for the game using Pygame.
Run once before building the Windows installer.
"""
import pygame
import sys

def create_icon():
    pygame.init()
    sizes = [16, 32, 48, 64, 128, 256]
    surfaces = []

    for size in sizes:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        s = size

        # Black circle background
        pygame.draw.circle(surf, (20, 20, 20, 255), (s//2, s//2), s//2)

        # Road
        road_h = s // 4
        pygame.draw.rect(surf, (90, 90, 90), (0, s//2, s, road_h))

        # Bike body
        bw, bh = s // 2, s // 5
        bx, by = s // 4, s // 2 - bh
        pygame.draw.rect(surf, (220, 60, 0), (bx, by, bw, bh))

        # Wheels
        wr = max(2, s // 8)
        pygame.draw.circle(surf, (30, 30, 30), (s // 4, s // 2 + wr // 2), wr)
        pygame.draw.circle(surf, (30, 30, 30), (3 * s // 4, s // 2 + wr // 2), wr)

        # Rider (small square)
        rw = max(2, s // 6)
        rh = max(2, s // 5)
        rx = s // 2 - rw // 2
        ry = by - rh
        pygame.draw.rect(surf, (40, 40, 40), (rx, ry, rw, rh))

        surfaces.append(surf)

    # Save as ICO (largest first)
    surfaces.reverse()
    pygame.image.save(surfaces[0], "assets/icon.png")

    # Use PIL if available to make proper .ico
    try:
        from PIL import Image as PILImage
        imgs = []
        for surf in surfaces:
            raw = pygame.image.tostring(surf, "RGBA")
            img = PILImage.frombytes("RGBA", surf.get_size(), raw)
            imgs.append(img)
        imgs[0].save("assets/icon.ico", format="ICO",
                     sizes=[(s.get_width(), s.get_height()) for s in surfaces],
                     append_images=imgs[1:])
        print("Icon saved to assets/icon.ico (using Pillow)")
    except ImportError:
        print("Pillow not found; icon.png saved. For .ico, run: pip install Pillow")

    pygame.quit()

if __name__ == "__main__":
    create_icon()

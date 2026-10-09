"""Draws the app icons (a small ferry) with no dependencies. Run: python3 tools/make_icons.py"""
import struct, zlib, math, sys, os

BG, FG = (10, 111, 125), (255, 255, 255)
POLYS = [  # hull, cabin, funnel (coordinates on a 100x100 grid)
    [(16, 56), (84, 56), (72, 74), (28, 74)],
    [(32, 40), (68, 40), (68, 56), (32, 56)],
    [(44, 28), (56, 28), (56, 40), (44, 40)],
]

def inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c

def wave(x, y):
    return abs(y - (84 + 2.2 * math.sin(x / 6.5))) < 1.6 and 12 < x < 88

def render(n):
    rows = []
    for py in range(n):
        row = bytearray([0])
        for px in range(n):
            hits = 0
            for sx in (0.25, 0.75):
                for sy in (0.25, 0.75):
                    x, y = (px + sx) * 100 / n, (py + sy) * 100 / n
                    if wave(x, y) or any(inside(p, x, y) for p in POLYS): hits += 1
            t = hits / 4
            row += bytes(int(BG[i] + (FG[i] - BG[i]) * t) for i in range(3))
        rows.append(bytes(row))
    return b''.join(rows)

def png(n, path):
    raw = render(n)
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(data)

out = os.path.join(os.path.dirname(__file__), '..', 'public')
for n, name in ((180, 'apple-touch-icon.png'), (192, 'icon-192.png'), (512, 'icon-512.png')):
    png(n, os.path.join(out, name))
    print('wrote', name)

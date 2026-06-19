import pygame as pg
import noise
from colorsys import rgb_to_hsv, hsv_to_rgb
import random
import numpy as np
from player import Player
from cam import Camera
import math
from cam import ZOOM_LEVELS

pg.init()

def make_tiles(color, n=10, size=8, scale=2.0, hue_range=0.08):
    r,g,b = [x/255 for x in color]
    h,s,v = rgb_to_hsv(r,g,b)
    tiles = []
    for _ in range(n):
        ox, oy = random.randint(0,1000), random.randint(0,1000)
        surf = pg.Surface((size, size))
        for x in range(size):
            for y in range(size):
                n_val = noise.pnoise2((x+ox)/scale, (y+oy)/scale)
                nh = (h + n_val * hue_range) % 1.0
                nr,ng,nb = hsv_to_rgb(nh, s, min(max(v + n_val*.5,0),1))
                surf.set_at((x,y), (int(nr*255), int(ng*255), int(nb*255)))
        tiles.append(surf)
    return tiles

WIDTH, HEIGHT = 1440, 900
TILE = 32

display = pg.display.set_mode((WIDTH, HEIGHT), pg.HWSURFACE | pg.DOUBLEBUF)
screen = pg.Surface((WIDTH, HEIGHT))

palette = pg.image.load("palette.png")
colors = [palette.get_at((i,0)) for i in range(14)]

rock_tiles = make_tiles(colors[4][:3], 10, 8)
rock_tiles = [pg.transform.scale(t, (32,32)) for t in rock_tiles]
rock_tiles = [t.convert() for t in rock_tiles]

scaled_rock_tiles = {
    zoom: [pg.transform.scale(t, (math.ceil(TILE*zoom)+1, math.ceil(TILE*zoom))) for t in rock_tiles]
    for zoom in ZOOM_LEVELS
}

COLS = WIDTH // TILE
ROWS = HEIGHT // TILE

world_w = 4000
world_h = 2000
ORIGIN_COL = world_w // 2
ORIGIN_ROW = world_h // 2

world = np.zeros((world_h, world_w), dtype=np.float32)

tile_rng = np.random.default_rng(42)
tile_idx = tile_rng.integers(0, len(rock_tiles), (world_h, world_w))

DENSITY = 0.50
FADE_BOT = 900
DENSITY_MAX_BONUS = 0.25
SCALE = 0.07
CHUNK = 64
generated = set()

def density_at(world_row):
    if world_row <= 0:        return 0.0
    if world_row >= FADE_BOT: return DENSITY + DENSITY_MAX_BONUS
    return DENSITY + (world_row / FADE_BOT) * DENSITY_MAX_BONUS

def gen_chunk(cc, cr):
    for row in range(cr*CHUNK, (cr+1)*CHUNK):
        if not (0 <= row < world_h): continue
        d = density_at(row - ORIGIN_ROW)
        for col in range(cc*CHUNK, (cc+1)*CHUNK):
            if not (0 <= col < world_w): continue
            v = noise.pnoise2(col * SCALE, row * SCALE, octaves=4, persistence=0.5)
            world[row, col] = 1.0 if (v+1)/2 < d else 0.0

def maybe_gen_more():
    cx = int(cam.x // TILE) + ORIGIN_COL
    cy = int(cam.y // TILE) + ORIGIN_ROW
    for cr in range((cy - ROWS - 32) // CHUNK, (cy + ROWS + 32) // CHUNK + 1):
        for cc in range((cx - COLS - 32) // CHUNK, (cx + COLS + 32) // CHUNK + 1):
            if (cc, cr) not in generated:
                gen_chunk(cc, cr)
                generated.add((cc, cr))

cam = Camera(WIDTH, HEIGHT)
cam.x, cam.y = 0, 0

p1 = Player(0, 0, (80,180,255), (pg.K_a, pg.K_d, pg.K_w), ORIGIN_COL, ORIGIN_ROW)
p2 = Player(100, 0, (255,120,80), (pg.K_LEFT, pg.K_RIGHT, pg.K_UP), ORIGIN_COL, ORIGIN_ROW)

clock = pg.time.Clock()
run = True

while run:
    screen.fill(colors[2])

    for e in pg.event.get():
        if e.type == pg.QUIT:
            run = False

    maybe_gen_more()

    keys = pg.key.get_pressed()
    p1.update(keys, world, TILE)
    p2.update(keys, world, TILE)
    cam.update(p1.pos, p2.pos)

    nearest_zoom = min(ZOOM_LEVELS, key=lambda z: abs(z - cam.zoom))
    tiles = scaled_rock_tiles[nearest_zoom]
    hw, hh = WIDTH/2, HEIGHT/2
    zoom = cam.zoom
    cx, cy = cam.x, cam.y

    col0, row0, col1, row1 = cam.tile_bounds(TILE)
    for row in range(row0, row1):
        for col in range(col0, col1):
            wr, wc = row + ORIGIN_ROW, col + ORIGIN_COL
            if 0 <= wr < world_h and 0 <= wc < world_w:
                if world[wr, wc] > 0:
                    px = int((col*TILE - cx) * zoom + hw)
                    py = int((row*TILE - cy) * zoom + hh)         
                    if px > WIDTH or py > HEIGHT or px < -TILE or py < -TILE:
                        continue           
                    scaled = tiles[tile_idx[wr, wc]]
                    screen.blit(scaled, (px, py))

    p1.draw(screen, cam)
    p2.draw(screen, cam)

    clock.tick(80)
    display.blit(screen, (0,0))
    pg.display.set_caption(str(round(clock.get_fps(),1)))
    pg.display.flip()
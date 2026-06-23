# cam.py
import pygame as pg

# Config
ZOOM_MIN = 0.5
ZOOM_MAX = 2.0
ZOOM_SPEED = 0.05
PAN_SPEED = 0.08          # lerp factor, 0=no follow, 1=instant
DEAD_ZONE_RATIO = 0.1     # fraction of viewport that's "free" before cam moves

ZOOM_LEVELS = [0.5, 1.0,1.0,1.0,1.0]
ZOOM_DEFAULT = 2  # index into ZOOM_LEVELS
ZOOM_SPEED = 0.08
SEP_THRESHOLDS = [800, 400, 200, 50]  # pixel sep to drop to each zoom level

class Camera:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h
        self.x = 0.0
        self.y = 0.0
        self.zoom_idx = ZOOM_DEFAULT
        self.zoom = float(ZOOM_LEVELS[ZOOM_DEFAULT])
        self.target_zoom = self.zoom

    def update(self, p1, p2):
        cx = (p1[0] + p2[0]) / 2
        cy = (p1[1] + p2[1]) / 2

        dx = cx - self.x
        dy = cy - self.y
        dead_r = min(self.sw, self.sh) * DEAD_ZONE_RATIO / self.zoom
        dist = (dx**2 + dy**2) ** 0.5
        if dist > dead_r:
            # push cam just enough so centroid is back on the circle edge
            over = dist - dead_r
            self.x += (dx / dist) * over * PAN_SPEED
            self.y += (dy / dist) * over * PAN_SPEED 

        sep = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) ** 0.5
        idx = 0
        for i, threshold in enumerate(SEP_THRESHOLDS):
            if sep < threshold:
                idx = i + 1
        self.zoom_idx = idx
        self.target_zoom = ZOOM_LEVELS[self.zoom_idx]
        self.zoom += (self.target_zoom - self.zoom) * ZOOM_SPEED
        if abs(self.target_zoom - self.zoom) < 0.01:
            self.zoom = self.target_zoom

    def world_to_screen(self, wx, wy):
        sx = (wx - self.x) * self.zoom + self.sw / 2
        sy = (wy - self.y) * self.zoom + self.sh / 2
        return int(sx), int(sy)

    def screen_to_world(self, sx, sy):
        wx = (sx - self.sw / 2) / self.zoom + self.x
        wy = (sy - self.sh / 2) / self.zoom + self.y
        return wx, wy

    def tile_bounds(self, tile_size=32):
        tl = self.screen_to_world(0, 0)
        br = self.screen_to_world(self.sw, self.sh)
        return (int(tl[0]//tile_size)-1, int(tl[1]//tile_size)-1,
                int(br[0]//tile_size)+1, int(br[1]//tile_size)+1)
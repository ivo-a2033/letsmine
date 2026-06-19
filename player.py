import pygame as pg

GRAVITY = 0.5
JUMP_VEL = -20
SPEED = 8
MAX_FALL = 18

class Player:
    def __init__(self, x, y, color, controls, origin_col, origin_row):
        self.x = float(x)
        self.y = float(y)
        self.w = 24
        self.h = 32
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.color = color
        self.left, self.right, self.jump = controls
        self.oc = origin_col
        self.or_ = origin_row

    def update(self, keys, world, T):
        self.vx = 0
        if keys[self.left]:  self.vx = -SPEED
        if keys[self.right]: self.vx =  SPEED
        if keys[self.jump] and self.on_ground:
            self.vy = JUMP_VEL
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.x += self.vx
        self._resolve(world, T, 'x')
        self.on_ground = False
        self.y += self.vy
        self._resolve(world, T, 'y')

    def _resolve(self, world, T, axis):
        col0 = int(self.x // T) + self.oc
        col1 = int((self.x + self.w - 1) // T) + self.oc
        row0 = int(self.y // T) + self.or_
        row1 = int((self.y + self.h - 1) // T) + self.or_
        for row in range(row0, row1+1):
            for col in range(col0, col1+1):
                if not (0 <= row < world.shape[0] and 0 <= col < world.shape[1]): continue
                if world[row, col] == 0: continue
                tx = (col - self.oc) * T
                ty = (row - self.or_) * T
                ox = min(self.x+self.w, tx+T) - max(self.x, tx)
                oy = min(self.y+self.h, ty+T) - max(self.y, ty)
                if ox <= 0 or oy <= 0: continue
                if axis == 'x':
                    self.x += ox if self.vx < 0 else -ox
                    self.vx = 0
                else:
                    if self.vy > 0: self.y -= oy; self.on_ground = True
                    else:           self.y += oy
                    self.vy = 0

    def draw(self, screen, cam):
        px, py = cam.world_to_screen(self.x, self.y)
        pg.draw.rect(screen, self.color, (px, py, int(self.w*cam.zoom), int(self.h*cam.zoom)))

    @property
    def pos(self):
        return (self.x + self.w/2, self.y + self.h/2)
import random
import noise
import pygame

class StellarObjectTriangle:
    def __init__(self, p1: tuple, p2: tuple, p3: tuple):
        self.p1 = list(p1)
        self.p2 = list(p2)
        self.p3 = list(p3)
        self.rgb1 = 0
        self.rgb2 = 0
        self.rgb3 = 0
        self.color = (self.rgb1, self.rgb2, self.rgb3)

    def chooseColor(self, color):
        self.rgb1 = color[0]
        self.rgb2 = color[1]
        self.rgb3 = color[2]
        self.color = (self.rgb1, self.rgb2, self.rgb3)

class StellarObject:
    def __init__(self, triangles, center_x, center_y):
        self.triangles = triangles
        self.randomOffset = random.randint(1,1000)
        self.center_x = center_x
        self.center_y = center_y

    def noiseValue(self, x, y, scale = 0.1, octaves = 4):
        val = noise.pnoise2((x + self.randomOffset) * scale, (y + self.randomOffset) * scale, octaves)
        return (val + 1)/2

    def draw(self, surface):
        # Drawing all the triangles
        for i in self.triangles:
            for j in range(len(i)):
                pygame.draw.polygon(surface, i[j].color, (i[j].p1, i[j].p2, i[j].p3))
                pygame.draw.polygon(surface, i[j].color, (i[j].p1, i[j].p2, i[j].p3))
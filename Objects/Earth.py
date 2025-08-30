#       Classes
import random
import pygame
import noise

from Utils.func_utils import *

class EarthTriangle:
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
    

class Earth:
    def __init__(self, triangles):
        self.triangles = triangles
        self.randomOffset = random.randint(1,1000)

    def noiseValue(self, x, y, scale = 0.1, octaves = 4):
        val = noise.pnoise2((x + self.randomOffset) * scale, (y + self.randomOffset) * scale, octaves)
        return (val + 1)/2

    def draw(self, surface):
        # Drawing all the triangles
        for i in self.triangles:
            for j in range(len(i)):
                pygame.draw.polygon(surface, i[j].color, (i[j].p1, i[j].p2, i[j].p3))
                pygame.draw.polygon(surface, i[j].color, (i[j].p1, i[j].p2, i[j].p3))

    def update(self):
        self.randomOffset -= 1
        #   Changes the color just like during initialization, while moving the offset to rotate the planet
        for y in range(len(self.triangles)):
            for x in range(len(self.triangles[y])):
                n = self.noiseValue(x, y, scale=0.05)
                if (n > 0.5):
                    color = randomColor('earth green')
                else:
                    color = randomColor('earth blue')
                
                self.triangles[y][x].chooseColor(color)
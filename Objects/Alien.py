import pygame
import Objects.Shapes
import random

class Alien():
    def __init__(self, x, y, lifetime, velocity, body_width, body_height, body_color, elipse_width, elipse_height, elipse_color):
        self.x = x
        self.y = y
        self.dx = 0
        self.life_time = lifetime * 200
        
        self.body_color = body_color
        self.elipse_color = elipse_color
        
        #Top parameters
        self.radius =  60 
        self.color = (255, 0, 0)
        
        #Bottom parameters
        self.rx = self.radius *2
        self.ry = self.radius /2
        
        self.top = Objects.Shapes.drawSemiElipse(x, y, body_width, body_height, 24, 0)
        self.bottom = Objects.Shapes.drawSemiElipse(x, y, elipse_width, elipse_height, 7)
        
    def add_booster(self, num):
        pass
        
    
    def update(self):
        self.life_time -= 1
        # self.dx += 1
    
    def draw(self, surface):
        for tri in self.top:
            for coords in tri:
                coords[0] -= 3
                coords[1] -= 1
            pygame.draw.polygon(surface, self.body_color, tri)
            # pygame.draw.polygon(surface, (255, 255, 255), tri, 2)

            
        for tri in self.bottom:
            for coords in tri:
                coords[0] -= 3
                coords[1] -= 1
            pygame.draw.polygon(surface, self.elipse_color, tri)
            pygame.draw.polygon(surface, (255,255,255), tri, 2)
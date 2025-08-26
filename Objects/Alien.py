import pygame
import Objects.Shapes

class Alien():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.life_time = 200 #as a parameter
        self.radius =  60 #as a parameter
        self.color = (255, 0, 0) #as a parameter
        
        #Bottom parameters
        self.rx = self.radius *2
        self.ry = self.radius /2
        
        self.top = Objects.Shapes.drawSemiCercle(x, y, self.radius, 9, 0)
        self.bottom = Objects.Shapes.drawSemiElipse(x, y, self.rx, self.ry, 7)
        
    
    def update(self):
        self.life_time -= 1
        # self.dx += 1
    
    def draw(self, surface):
        for tri in self.top:
            for coords in tri:
                coords[0] -= 1
            pygame.draw.polygon(surface, self.color, tri)
            pygame.draw.polygon(surface, (255, 255, 255), tri, 2)

            
        for tri in self.bottom:
            for coords in tri:
                coords[0] -= 1
            pygame.draw.polygon(surface, (0, 0, 255), tri)
            pygame.draw.polygon(surface, (255,255,255), tri, 2)
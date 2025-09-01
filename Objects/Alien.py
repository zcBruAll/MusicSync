import pygame
import Objects.Shapes
import random
import math

class Alien():
    def __init__(self, x, y, lifetime, velocity, body_width, body_height, body_color, elipse_width, elipse_height, elipse_color, light_color):
        self.x = x
        self.y = y
        self.dx = 0
        self.life_time = lifetime * 200
        self.move_angle = 0
        
        #colors for each part
        self.body_color = body_color
        self.elipse_color = elipse_color
        self.light_color = light_color
        
        #lists of points fo each part
        self.top = Objects.Shapes.drawSemiElipse(x, y, body_width, body_height, random.randint(3, 15), 0)
        self.bottom = Objects.Shapes.drawSemiElipse(x, y, elipse_width, elipse_height, 7)
        self.booster = Alien.add_booster(self, x, y, elipse_width, elipse_height, velocity)
        
    def add_booster(self, cx, cy, rx, ry, num):
        angle_step = 180 / num + 1
        triangles = []
    
        for i in range(1, num):
            angle1 = math.radians(i * (angle_step) - 20)
            angle2 = math.radians(i * (angle_step) + 20)
            
            newx = cx + (rx * math.cos(math.radians(angle_step * i)))*0.7
            newy = cy + (ry * math.sin(math.radians(angle_step * i)))*0.7
        
            point1 = [newx + (rx * math.cos(angle1))/2, newy + (ry * math.sin(angle1))/2]
            point2 = [newx + (rx * math.cos(angle2))/2, newy + (ry * math.sin(angle2))/2]   
        
            triangles.append([[newx,newy], point1, point2])
         
        return triangles 
        
    
    def update(self):
        self.life_time -= 1
        self.move_angle += 0.01
    
    def draw(self, surface):
        for tri in self.top:
            for coords in tri:
                coords[0] -= math.cos(self.move_angle) * 10
                coords[1] -= math.sin(self.move_angle) * 10
            pygame.draw.polygon(surface, self.body_color, tri)

        for tri in self.booster:
            for coords in tri:
                coords[0] -= math.cos(self.move_angle) * 10
                coords[1] -= math.sin(self.move_angle) * 10
            pygame.draw.polygon(surface, self.light_color, tri)
            
        for tri in self.bottom:
            for coords in tri:
                coords[0] -= math.cos(self.move_angle) * 10
                coords[1] -= math.sin(self.move_angle) * 10
            pygame.draw.polygon(surface, self.elipse_color, tri)
            pygame.draw.polygon(surface, (255,255,255), tri, 2)
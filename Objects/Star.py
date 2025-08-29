import numpy as np
import pygame, math

class Star():
    def __init__(self, x, y, num_triangle, size, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.num_triangle = num_triangle  # nombre de triangles autour du centre
        self.size = size                  # taille (longueur du rayon)
        self.color = color
        self.rotation = 0               # rotation actuelle en radians
        self.isMoving = False
        self.rotation_speed = 0.05       # vitesse de rotation
        self.move_angle = 0                # angle de déplacement
        self.trail = []  # stocke les anciennes positions

    def draw(self, surface):
        # petit angle d’ouverture du triangle
        delta = math.radians(15)  

        for i in range(self.num_triangle):
            # angle de base pour ce triangle
            angle = self.rotation + (2 * math.pi / self.num_triangle) * i

            # points du triangle
            p1 = (self.x, self.y)  # centre
            p2 = (self.x + math.cos(angle) * self.size,
                  self.y + math.sin(angle) * self.size)
            p3 = (self.x + math.cos(angle + delta) * self.size,
                  self.y + math.sin(angle + delta) * self.size)

            # dessiner le triangle
            pygame.draw.polygon(surface, self.color, [p1, p2, p3])
            
    def update(self, surface):
        if self.isMoving:
            self.draw_trail(surface)
            self.rotation_speed = 0.1
            self.move_angle += 0.01  # courbure
            self.x += math.cos(self.move_angle) * 10
            self.y += math.sin(self.move_angle) * 10

    def draw_trail(self, surface):
        back_angle = self.move_angle + math.pi  

        num_trail_triangles = 5  # nombre de triangles dans la trainée
        for i in range(num_trail_triangles):
            # plus i est grand → plus le triangle est petit et éloigné
            size = self.size * (1.2 - i * 0.15)  
            distance = self.size * (1.5 + i * 1.0)

            # points du triangle derrière
            p1 = (self.x + math.cos(back_angle) * distance,
                  self.y + math.sin(back_angle) * distance)
            p2 = (self.x + math.cos(back_angle + 0.3) * (size * 0.7),
                  self.y + math.sin(back_angle + 0.3) * (size * 0.7))
            p3 = (self.x + math.cos(back_angle - 0.3) * (size * 0.7),
                  self.y + math.sin(back_angle - 0.3) * (size * 0.7))

            # couleur qui s’assombrit avec la distance
            fade = max(0, 255 - i * 40)
            color = (255, fade, 0)  # du orange vers rouge sombre

            pygame.draw.polygon(surface, color, [p1, p2, p3])
            
    def is_off_screen(self, width, height):
        return (self.x < -self.size or self.x > width + self.size or
                self.y < -self.size or self.y > height + self.size)
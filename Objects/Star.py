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
        self.move_angle = 0                # angle de déplacement


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
            
    def update(self):
        if self.isMoving:
            self.x += math.cos(self.move_angle) * 5
            self.y += math.sin(self.move_angle) * 5
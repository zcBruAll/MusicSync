import pygame, math
from enum import Enum
import math, random, pygame


class StarState(Enum):
    STATIC = 1
    MOVING = 2
    EXPLODING = 3
    
class ExplosionFragment:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(3, 8)
        self.size = random.randint(5, 15)
        self.color = (255, random.randint(100, 200), random.randint(0, 100))  # jaune/orange/rouge
        self.life = 60  # durée de vie (en frames, ~1s à 60fps)

    def update(self):
        if self.life <= 0:
            return
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.speed *= 0.95  # ralentissement
        self.life -= 1      # décrément durée de vie

        # effet feu d’artifice → couleur qui s’assombrit
        fade = max(0, int(255 * (self.life / 60)))
        self.color = (fade, random.randint(50, 150), 0)

    def draw(self, surface):
        if self.life <= 0:
            return
        points = []
        for i in range(3):
            angle = self.angle + i * (2 * math.pi / 3)
            px = self.x + math.cos(angle) * self.size
            py = self.y + math.sin(angle) * self.size
            points.append((px, py))
        pygame.draw.polygon(surface, self.color, points)

class Star():
    def __init__(self, x, y, num_triangle, size, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.num_triangle = num_triangle  # nombre de triangles autour du centre
        self.size = size                  # taille (longueur du rayon)
        self.color = color
        self.rotation = 0               # rotation actuelle en radians
        self.rotation_speed = 0.02       # vitesse de rotation
        self.move_angle = 0                # angle de déplacement
        self.trail = []  # stocke les anciennes positions
        self.state = StarState.STATIC
        self.fragments = []  # stocker les fragments d'explosion


    def draw(self, surface):
        """
        Dessine une étoile avec un corps central (n_branches côtés)
        et un triangle sur chaque arête.
        """
        step = 2 * math.pi / self.num_triangle

        polygon_points = []
        for i in range(self.num_triangle):
            angle = i * step + self.rotation
            px = self.x + math.cos(angle) * self.size / 2
            py = self.y + math.sin(angle) * self.size / 2
            polygon_points.append((px, py))

        # dessiner le corps
        pygame.draw.polygon(surface, self.color, polygon_points)

        # triangles extérieurs
        for i in range(self.num_triangle):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % self.num_triangle]

            # milieu de l’arête
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2

            # vecteur de l'arête
            vx = p2[0] - p1[0]
            vy = p2[1] - p1[1]

            # vecteur perpendiculaire
            nx, ny = -vy, vx
            length = math.hypot(nx, ny)
            if length == 0:
                continue
            nx /= length
            ny /= length

            # vecteur centre → milieu
            cx = mx - self.x
            cy = my - self.y

            # vérifier si la normale pointe vers l’extérieur
            dot = nx * cx + ny * cy
            if dot < 0:
                nx, ny = -nx, -ny

            # sommet extérieur du triangle
            tip = (mx + nx * self.size, my + ny * self.size)

            # dessiner le triangle
            pygame.draw.polygon(surface, self.color, [p1, p2, tip])
        
        if self.state == StarState.EXPLODING:
            for frag in self.fragments:
                frag.draw(surface) 


    def update(self, surface):
        match self.state:
            case StarState.STATIC:
                pass
            case StarState.MOVING:
                self.travel(surface)
            case StarState.EXPLODING:
                self.explode()

    def travel(self, surface):
        self.draw_trail(surface)
        self.rotation_speed = 0.1
        self.move_angle += 0.01  # courbure
        self.x += math.cos(self.move_angle) * 10
        self.y += math.sin(self.move_angle) * 10
        
    def explode(self):
        if not self.fragments:
            self.fragments = [ExplosionFragment(self.x, self.y) for _ in range(40)]

        # Update fragments existants
        for frag in self.fragments:
            frag.update()

        # Si tous les fragments sont morts → l’étoile n’existe plus
        self.fragments = [f for f in self.fragments if f.life > 0]


    def draw_trail(self, surface):
        back_angle = self.move_angle + math.pi  

        num_trail_triangles = 10  # nombre de triangles dans la trainée
            
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
            color = (255, fade, 120)  # du orange vers rouge sombre
            
            pygame.draw.polygon(surface, color, [p1, p2, p3])
            
    def is_off_screen(self, width, height):
        return (self.x < -self.size or self.x > width + self.size or
                self.y < -self.size or self.y > height + self.size)

    def is_moving(self):
        return self.state == StarState.MOVING

    def is_static(self):
        return self.state == StarState.STATIC
    
    def set_moving(self):
        self.state = StarState.MOVING

    def set_exploding(self):
        self.state = StarState.EXPLODING
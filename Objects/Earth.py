#       Classes
import math
from Objects.StellarObject import *
from Utils.func_utils import *

class Earth(StellarObject):
    def __init__(self, triangles, center_x, center_y, death_time_ms=60000):
        super().__init__(triangles, center_x, center_y)
        self.death_time_ms = death_time_ms
        self.is_exploding = False
        self.explosion_started = False
        self.explosion_triangles = []  # stocke triangles avec vitesses

    def interpolate_color(self, c1, c2, t):
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def trigger_explosion(self):
        """Prépare les triangles à s'éparpiller"""
        if self.explosion_started:
            return
        self.is_exploding = True
        self.explosion_started = True
        self.explosion_triangles = []

        for row in self.triangles:
            for tri in row:
                # centre du triangle
                cx = (tri.p1[0] + tri.p2[0] + tri.p3[0]) / 3
                cy = (tri.p1[1] + tri.p2[1] + tri.p3[1]) / 3
                dx = cx - self.center_x
                dy = cy - self.center_y
                dist = math.sqrt(dx * dx + dy * dy) or 1

                speed = random.uniform(30, 40)  # vitesse initiale
                vx = dx / dist * speed + random.uniform(-1, 1)
                vy = dy / dist * speed + random.uniform(-1, 1)

                self.explosion_triangles.append({
                    "triangle": tri,
                    "vx": vx,
                    "vy": vy,
                    "life": 255  # opacité
                })

    def update(self, elapsed_time_ms):
        """Si pas encore d’explosion → update normal"""
        if not self.is_exploding:
            self.randomOffset -= 1
            death_factor = min(1.0, elapsed_time_ms / self.death_time_ms)

            for y in range(len(self.triangles)):
                for x in range(len(self.triangles[y])):
                    n = self.noiseValue(x, y, scale=0.04)

                    if n < 0.4:  
                        # Ocean deep -> brown desert
                        alive = (0, 0, int(150 + 100 * n))     # blue
                        dead  = (139, 69, 19)                  # brown (sienna)

                    elif n < 0.5:  
                        # Coast -> dried coast
                        alive = (20, int(100 + 100 * (n - 0.4) * 10), 200)  # bluish coast
                        dead  = (160, 82, 45)                              # darker brown

                    elif n < 0.65:  
                        # Plains green -> burned red
                        alive = (int(30 + 50 * n), int(120 + 100 * n), int(30 + 20 * n))  # green
                        dead  = (178, 34, 34)                                            # firebrick red

                    elif n < 0.7:  
                        # Mountains -> dry grey-brown
                        alive = (int(60 + 150 * n), int(60 + 150 * n), int(60 + 150 * n))  # gray
                        dead  = (100, 70, 50)                                             # stone brown

                    elif elapsed_time_ms < self.death_time_ms / 2:
                        # Crests -> dusty light brown
                        alive = (int(90 + 150 * n), int(90 + 150 * n), int(90 + 150 * n))  # snowy
                        dead  = (210, 180, 140)
                    else:
                        # Mountains -> dry grey-brown
                        alive = (int(60 + 150 * n), int(60 + 150 * n), int(60 + 150 * n))  # gray
                        dead  = (100, 70, 50)   # tan

                    color = self.interpolate_color(alive, dead, death_factor)
                    self.triangles[y][x].chooseColor(color)

        else:
            # update explosion : triangles qui volent
            for data in self.explosion_triangles:
                tri = data["triangle"]
                vx, vy = data["vx"], data["vy"]

                # mouvement
                tri.p1[0] += vx
                tri.p1[1] += vy
                tri.p2[0] += vx
                tri.p2[1] += vy
                tri.p3[0] += vx
                tri.p3[1] += vy

                # accélération vers l’extérieur
                data["vx"] *= 1.02
                data["vy"] *= 1.02

                # fade out progressif
                r, g, b = tri.color
                tri.chooseColor((max(0, r - 3), max(0, g - 3), max(0, b - 3)))

    def draw(self, surface):
        if not self.is_exploding:
            super().draw(surface)
        else:
            for data in self.explosion_triangles:
                tri = data["triangle"]
                pygame.draw.polygon(surface, tri.color, (tri.p1, tri.p2, tri.p3))

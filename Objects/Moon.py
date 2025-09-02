#       Classes
import math
from Objects.StellarObject import *
from Utils.func_utils import *

class Moon(StellarObject):
    def __init__(self, spacing, earth_x, earth_y, orbit_radius, moon_radius=120, collide_earth_ms=60000):
        super().__init__([], earth_x - orbit_radius, earth_y)
        self.spacing = spacing
        self.earth_x = earth_x
        self.earth_y = earth_y
        self.orbit_radius = orbit_radius
        self.distance = orbit_radius
        self.moon_radius = moon_radius
        self.collide_earth_ms = collide_earth_ms
        self.angle = 0.0
        self.angular_speed = 0.02
        self.cols = int((2 * moon_radius) / spacing) + 1
        self.rows = int((2 * moon_radius) / spacing) + 1

        # Explosion state
        self.is_exploding = False
        self.explosion_started = False
        self.explosion_triangles = []

        self.regenerate_triangles()

    def trigger_explosion(self):
        if self.explosion_started:
            return
        self.is_exploding = True
        self.explosion_started = True
        self.explosion_triangles = []

        for row in self.triangles:
            for tri in row:
                cx = (tri.p1[0] + tri.p2[0] + tri.p3[0]) / 3
                cy = (tri.p1[1] + tri.p2[1] + tri.p3[1]) / 3
                dx = cx - self.center_x
                dy = cy - self.center_y
                dist = math.sqrt(dx * dx + dy * dy) or 1

                speed = random.uniform(20, 30)  # un peu plus lent que la Terre
                vx = dx / dist * speed + random.uniform(-1, 1)
                vy = dy / dist * speed + random.uniform(-1, 1)

                self.explosion_triangles.append({
                    "triangle": tri,
                    "vx": vx,
                    "vy": vy,
                })

    def update(self, elapsed_time_ms):
        if not self.is_exploding:
            # comportement normal (orbite + couleur)
            e_m_distance = 650
            collide_factor = 1 - min(1.0, elapsed_time_ms / self.collide_earth_ms)
            self.distance = (self.orbit_radius - e_m_distance) + (e_m_distance * collide_factor)
            self.angle += self.angular_speed
            self.center_x = self.earth_x + math.cos(self.angle) * self.distance
            self.center_y = self.earth_y + math.sin(self.angle) * self.distance
            self.regenerate_triangles()

            for y in range(len(self.triangles)):
                for x in range(len(self.triangles[y])):
                    n = self.noiseValue(x + int(self.center_x / self.spacing),
                                        y + int(self.center_y / self.spacing),
                                        scale=0.04)
                    if n < 0.4:
                        color = (int(40 + 40 * n),) * 3
                    elif n < 0.55:
                        color = (int(80 + 50 * n),) * 3
                    elif n < 0.7:
                        color = (int(150 + 50 * n),) * 3
                    else:
                        color = (int(200 + 55 * n),) * 3
                    self.triangles[y][x].chooseColor(color)
        else:
            # explosion
            for data in self.explosion_triangles:
                tri = data["triangle"]
                tri.p1[0] += data["vx"]
                tri.p1[1] += data["vy"]
                tri.p2[0] += data["vx"]
                tri.p2[1] += data["vy"]
                tri.p3[0] += data["vx"]
                tri.p3[1] += data["vy"]

                data["vx"] *= 1.02
                data["vy"] *= 1.02

                r, g, b = tri.color
                tri.chooseColor((max(0, r - 4), max(0, g - 4), max(0, b - 4)))

    def draw(self, surface):
        if not self.is_exploding:
            super().draw(surface)
        else:
            for data in self.explosion_triangles:
                tri = data["triangle"]
                pygame.draw.polygon(surface, tri.color, (tri.p1, tri.p2, tri.p3))
    
    def regenerate_triangles(self):
        triangleList = []
        for y in range(self.rows):
            tempList = []
            for x in range(self.cols):
                # Grille locale centrée sur la lune
                x0 = x * self.spacing - self.moon_radius
                x1 = (x + 1) * self.spacing - self.moon_radius
                y0 = y * self.spacing - self.moon_radius
                y1 = (y + 1) * self.spacing - self.moon_radius

                def clamp(px, py):
                    dx, dy = px, py
                    dist2 = dx * dx + dy * dy
                    if dist2 > self.moon_radius * self.moon_radius:
                        dist = math.sqrt(dist2)
                        dx = dx / dist * self.moon_radius
                        dy = dy / dist * self.moon_radius
                    return (dx + self.center_x, dy + self.center_y)

                p0 = clamp(x0, y0)
                p1 = clamp(x1, y0)
                p2 = clamp(x0, y1)
                p3 = clamp(x1, y1)

                tempList.append(StellarObjectTriangle(p0, p1, p2))
                tempList.append(StellarObjectTriangle(p1, p3, p2))
            triangleList.append(tempList)
        self.triangles = triangleList
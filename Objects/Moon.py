#       Classes
import math
from Objects.StellarObject import *
from Utils.func_utils import *

class Moon(StellarObject):
    def __init__(self, rows, cols, spacing, earth_x, earth_y, orbit_radius, moon_radius=120, collide_earth_ms=60000):
        super().__init__([], earth_x - orbit_radius, earth_y)
        self.rows = rows
        self.cols = cols
        self.spacing = spacing
        self.earth_x = earth_x
        self.earth_y = earth_y
        self.orbit_radius = orbit_radius
        self.distance = orbit_radius
        self.moon_radius = moon_radius
        self.collide_earth_ms = collide_earth_ms
        self.angle = 0.0          # position sur l’orbite
        self.angular_speed = 0.02 # vitesse de rotation
        self.regenerate_triangles()

    def regenerate_triangles(self):
        triangleList = []
        for y in range(self.rows):
            tempList = []
            for x in range(self.cols):
                x0 = x * self.spacing - 1920 // 2
                x1 = (x + 1) * self.spacing - 1920 // 2
                y0 = y * self.spacing
                y1 = (y + 1) * self.spacing

                def clamp(px, py):
                    dx, dy = px, py - self.center_y
                    if dx * dx + dy * dy > self.moon_radius * self.moon_radius:
                        dist = (dx * dx + dy * dy) ** 0.5
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

    def update(self, elapsed_time_ms):
        e_m_distance = 650
        # fait tourner la lune autour de la Terre
        collide_factor = 1 - min(1.0, elapsed_time_ms / self.collide_earth_ms)

        self.distance = (self.orbit_radius - e_m_distance) + (e_m_distance * collide_factor)

        self.angle += self.angular_speed
        self.center_x = self.earth_x + math.cos(self.angle) * self.distance
        self.center_y = self.earth_y + math.sin(self.angle) * self.distance

        self.regenerate_triangles()

        # applique la texture grise
        for y in range(len(self.triangles)):
            for x in range(len(self.triangles[y])):
                n = self.noiseValue(
                    x + int(self.center_x / self.spacing),
                    y + int(self.center_y / self.spacing),
                    scale=0.04
                )
                if n < 0.4:
                    color = (int(40 + 40 * n),) * 3
                elif n < 0.55:
                    color = (int(80 + 50 * n),) * 3
                elif n < 0.7:
                    color = (int(150 + 50 * n),) * 3
                else:
                    color = (int(200 + 55 * n),) * 3
                self.triangles[y][x].chooseColor(color)
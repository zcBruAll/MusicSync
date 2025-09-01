#       Classes
from Objects.StellarObject import *
from Utils.func_utils import *

class Earth(StellarObject):
    def __init__(self, triangles, center_x, center_y, death_time_ms=60000):
        super().__init__(triangles, center_x, center_y)
        self.death_time_ms = death_time_ms

    def interpolate_color(self, c1, c2, t):
        """Interpole entre deux couleurs RGB"""
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def update(self, elapsed_time_ms):
        self.randomOffset -= 1

        # facteur de "mort" entre 0 (vivant) et 1 (morte)
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


                # Mélange en fonction du temps
                color = self.interpolate_color(alive, dead, death_factor)
                self.triangles[y][x].chooseColor(color)

import pygame
import random

class Instrument():
    def __init__(self, x, y,noteLifeTime):
        self.x = x
        self.y = y
        self.size = 20
        self.life_time = random.randint(100, noteLifeTime*12) #duration of the note
        self.dx = 0

        # self.color = (255, 255, 255) #default white

    def update(self):
        self.life_time -= 1
        
    # def change_color(self, num):
    #     match num:
    #         case 1:
    #             self.color = (255, 0, 0)
    #         case 2:
    #             self.color = (0, 255, 0)

    def draw(self):
        pass
        
class Piano(Instrument):
    def update(self):
        self.dx += 2
        return super().update()
    
    def draw(self, surface):
        self.color = (255, 0, 0)
        pygame.draw.polygon(surface, self.color, [(self.x + self.dx, self.y), (self.x -self.size + self.dx, self.y - self.size/2), (self.x  -self.size + self.dx , self.y + self.size/2)])
        return super().draw()
    
class Trumpet(Instrument):
    def update(self):
        self.dx -= 2
        return super().update()
    
    def draw(self, surface):
        self.color = (255, 255, 0)
        pygame.draw.polygon(surface, self.color, [(self.x + self.dx, self.y), (self.x +self.size + self.dx, self.y + self.size/2), (self.x + self.size + self.dx , self.y - self.size/2)])
        return super().draw()
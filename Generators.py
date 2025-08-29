import random

import pygame
from Objects.Satellite import Satellite
from Objects.Alien import Alien
from Objects.Star import Star

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

def generate_Satellite(x, y, lifetime, additions):
    
    body_width = random.randint(30, 50)
    body_height = random.randint(30, 50)
    
    if random.randint(1,2) == 1:
        isRectangle = True
    else:
        isRectangle = False
        
    body_color = randomColor('white')
    
    if random.randint(1,2) == 1:
        num_wings = 1
    else:
        num_wings = 2
        
    pannel_width = random.randint(20, 30)
    pannel_height = random.randint(50, 80)
    pannel_color = randomColor('multi')
    
    return Satellite(x, y, lifetime, additions, isRectangle, body_width, body_height, body_color, pannel_width, pannel_height, num_wings, pannel_color)

def generate_Alien(x, y, lifetime, additions):
    
    body_height = random.randint(40, 60)
    body_width = random.randint(body_height, 70)
    body_color = randomColor('blue')
    
    elipse_width = random.randint(body_width + 20, 100)
    elipse_height = random.randint(30, body_height)
    elipse_color = randomColor('multi')
    
    light_color = (0,0,0)
    
    return Alien(x, y, lifetime, additions, body_width, body_height, body_color, elipse_width, elipse_height, elipse_color)

def randomColor(color_name):
    if color_name == 'yellow':
        return (255, random.randint(230, 255), random.randint(1,255))
    
    if color_name == 'purple':
        return (random.randint(160, 190), random.randint(150, 175), random.randint(200, 220))
    
    if color_name == 'white':
        return (random.randint(220, 255),  random.randint(220, 255),  random.randint(220, 255))
    
    if color_name == 'blue':
        hex = random.randint(20, 170)
        return (hex, random.randint(hex, hex+20) , random.randint(120, 225))
    
    if color_name == 'multi':
        return (random.randint(92, 183), random.randint(92, 183), random.randint(92, 183))

def star_generator(number):
    """
    Generate a number of Star with random properties.
    1. Randomly determine the number of triangles (3 to 8).
    2. Randomly determine the size of the star (4 to 8 px).
    3. Randomly determine the position of the star inside the game window
    4. Randomly determine the color of the star (white, gold, or light blue).
    """
    stars = []
    for _ in range(number):
        num_triangle = random.randint(3, 8)
        size = random.randint(4, 8)
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color = random.choice([(255, 255, 255), (255, 215, 0), (173, 216, 230)])
        stars.append(Star(x, y, num_triangle, size, color))
    return stars